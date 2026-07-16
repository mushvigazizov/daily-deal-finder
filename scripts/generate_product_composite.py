#!/usr/bin/env python3

import argparse
import base64
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PRODUCTS_PATH = ROOT / "data/products.json"
REFERENCE_DIR = ROOT / "data/amazon_reference_images"
OUTPUT_DIR = ROOT / "assets/products"

CANVAS_SIZE = (1024, 1536)


def load_env() -> None:
    env_path = ROOT / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(
            key.strip(),
            value.strip().strip('"').strip("'"),
        )


def load_products() -> list[dict]:
    payload = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )
    return payload["products"]


def find_reference(product_id: str) -> Path:
    matches = sorted(REFERENCE_DIR.glob(f"{product_id}.*"))

    if not matches:
        raise RuntimeError(
            f"Amazon reference image missing for {product_id}"
        )

    return matches[0]


def build_background_prompt(product: dict) -> str:
    title = (
        product.get("amazon_product_title")
        or product.get("title")
        or ""
    )

    category = (
        product.get("subcategory")
        or product.get("category")
        or "outdoor product"
    )

    return f"""
Create only a premium realistic lifestyle BACKGROUND for this product.

Product title: {title}
Category: {category}

The product itself will be added later as an unchanged photographic cutout.

Create a bright, attractive outdoor lifestyle environment naturally matching
the product category. Use clear daylight or warm golden-hour lighting.

Composition requirements:
- vertical 2:3 composition
- clean central foreground area for the product
- realistic ground surface under the product
- believable perspective
- premium Pinterest and outdoor-brand aesthetic
- bright and well exposed
- rich but natural colours
- high clarity
- no dark night scene
- no heavy shadows
- no fog
- no people
- no product
- no tent
- no sleeping bag
- no equipment
- no text
- no CTA
- no logo
- no watermark
- no collage

Generate only the empty lifestyle environment.
""".strip()


def generate_background(
    product: dict,
    output_path: Path,
) -> None:
    from openai import OpenAI

    api_key = (
        os.getenv("OPENAI_IMAGE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    if not api_key:
        raise RuntimeError("OpenAI image API key not found")

    client = OpenAI(api_key=api_key)

    response = client.images.generate(
        model="gpt-image-1",
        prompt=build_background_prompt(product),
        size="1024x1536",
        quality="high",
        output_format="webp",
        n=1,
    )

    result = response.data[0]

    if getattr(result, "b64_json", None):
        output_path.write_bytes(
            base64.b64decode(result.b64_json)
        )
        return

    if getattr(result, "url", None):
        urllib.request.urlretrieve(
            result.url,
            output_path,
        )
        return

    raise RuntimeError("Image API returned no image")


def remove_white_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()

    width, height = rgba.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]

            minimum = min(red, green, blue)

            if minimum >= 248:
                pixels[x, y] = (red, green, blue, 0)
            elif minimum >= 225:
                new_alpha = int(
                    alpha * (248 - minimum) / 23
                )
                pixels[x, y] = (
                    red,
                    green,
                    blue,
                    max(0, min(255, new_alpha)),
                )

    alpha_channel = rgba.getchannel("A").filter(
        ImageFilter.GaussianBlur(0.7)
    )
    rgba.putalpha(alpha_channel)

    bbox = rgba.getbbox()

    if not bbox:
        raise RuntimeError(
            "Reference image became empty after background removal"
        )

    return rgba.crop(bbox)


def resize_product(product: Image.Image) -> Image.Image:
    max_width = 900
    max_height = 790

    ratio = min(
        max_width / product.width,
        max_height / product.height,
    )

    new_size = (
        max(1, int(product.width * ratio)),
        max(1, int(product.height * ratio)),
    )

    return product.resize(
        new_size,
        Image.Resampling.LANCZOS,
    )


def create_shadow(product: Image.Image) -> Image.Image:
    alpha = product.getchannel("A")

    shadow = Image.new(
        "RGBA",
        product.size,
        (0, 0, 0, 0),
    )

    shadow.putalpha(
        alpha.filter(
            ImageFilter.GaussianBlur(22)
        ).point(lambda value: int(value * 0.42))
    )

    return shadow


def composite_product(
    background_path: Path,
    reference_path: Path,
    output_path: Path,
) -> None:
    background = Image.open(
        background_path
    ).convert("RGB")

    background = ImageOps.fit(
        background,
        CANVAS_SIZE,
        method=Image.Resampling.LANCZOS,
    ).convert("RGBA")

    reference = Image.open(
        reference_path
    ).convert("RGBA")

    product = resize_product(
        remove_white_background(reference)
    )

    x = (CANVAS_SIZE[0] - product.width) // 2
    y = CANVAS_SIZE[1] - product.height - 115

    shadow = create_shadow(product)

    background.alpha_composite(
        shadow,
        (x + 14, y + 27),
    )

    background.alpha_composite(
        product,
        (x, y),
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    background.convert("RGB").save(
        output_path,
        "WEBP",
        quality=90,
        method=6,
    )


def process_product(product: dict) -> None:
    product_id = product["id"]

    if (
        product.get("verification_status") != "verified"
        or product.get("identity_locked") is not True
    ):
        raise RuntimeError(
            f"{product_id} is not verified and locked"
        )

    reference_path = find_reference(product_id)

    temporary_background = Path(
        f"/tmp/{product_id}-ai-background.webp"
    )

    output_path = OUTPUT_DIR / f"{product_id}.webp"

    print(f"[REFERENCE] {reference_path}")
    print("[AI] Generating lifestyle background...")

    generate_background(
        product,
        temporary_background,
    )

    print("[COMPOSITE] Placing unchanged original product...")

    composite_product(
        temporary_background,
        reference_path,
        output_path,
    )

    with Image.open(output_path) as result:
        print(f"[PASS] {output_path}")
        print(f"       Dimensions: {result.size}")
        print(
            f"       Size: "
            f"{output_path.stat().st_size / 1024:.1f} KB"
        )


def main() -> int:
    load_env()

    parser = argparse.ArgumentParser(
        description=(
            "Generate premium website images while preserving "
            "the original Amazon product."
        )
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument("--product")
    group.add_argument("--all-verified", action="store_true")

    args = parser.parse_args()

    products = load_products()

    if args.product:
        product = next(
            (
                item for item in products
                if item.get("id") == args.product
            ),
            None,
        )

        if product is None:
            raise SystemExit(
                f"ERROR: product not found: {args.product}"
            )

        targets = [product]
    else:
        targets = [
            item for item in products
            if (
                item.get("verification_status") == "verified"
                and item.get("identity_locked") is True
            )
        ]

    completed = 0

    for product in targets:
        try:
            process_product(product)
            completed += 1
        except Exception as error:
            print(
                f"[FAIL] {product.get('id')}: {error}"
            )

    print()
    print(f"Completed: {completed}/{len(targets)}")

    return 0 if completed == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
