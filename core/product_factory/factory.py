from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ASIN_PATTERN = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)", re.I)


@dataclass(frozen=True)
class FactoryInput:
    product_id: str
    amazon_url: str
    reference_image: str | None = None


@dataclass(frozen=True)
class FactoryManifest:
    schema_version: str
    product_id: str
    asin: str
    canonical_amazon_url: str
    original_amazon_url: str
    reference_image: str | None
    status: str
    created_at: str
    live_site_modified: bool
    requires_human_approval: bool


class ProductFactoryError(RuntimeError):
    pass


def extract_asin(amazon_url: str) -> str:
    value = amazon_url.strip()
    match = ASIN_PATTERN.search(value)

    if not match:
        raise ProductFactoryError(
            "Amazon URL must contain /dp/ASIN or /gp/product/ASIN."
        )

    return match.group(1).upper()


def validate_product_id(product_id: str) -> str:
    value = product_id.strip()

    if not re.fullmatch(r"camp-\d{3}", value):
        raise ProductFactoryError(
            "Product ID must use the format camp-001."
        )

    return value


def canonical_amazon_url(asin: str) -> str:
    return f"https://www.amazon.de/dp/{asin}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_product_exists(root: Path, product_id: str) -> None:
    products_path = root / "data/products.json"

    if not products_path.exists():
        raise ProductFactoryError("data/products.json was not found.")

    payload = read_json(products_path)
    products = payload.get("products", payload)

    if not isinstance(products, list):
        raise ProductFactoryError(
            "data/products.json must contain a product list."
        )

    if not any(item.get("id") == product_id for item in products):
        raise ProductFactoryError(
            f"Product does not exist in catalog: {product_id}"
        )


def create_preview(
    *,
    root: Path,
    product_id: str,
    amazon_url: str,
    reference_image: str | None = None,
) -> Path:
    product_id = validate_product_id(product_id)
    asin = extract_asin(amazon_url)

    ensure_product_exists(root, product_id)

    if reference_image:
        reference_path = Path(reference_image)

        if not reference_path.exists():
            raise ProductFactoryError(
                f"Reference image was not found: {reference_image}"
            )

    preview_root = (
        root
        / "data"
        / "product_factory"
        / "previews"
        / product_id
    )

    if preview_root.exists():
        raise ProductFactoryError(
            f"Preview already exists: {preview_root}"
        )

    preview_root.mkdir(parents=True, exist_ok=False)

    manifest = FactoryManifest(
        schema_version="1.0",
        product_id=product_id,
        asin=asin,
        canonical_amazon_url=canonical_amazon_url(asin),
        original_amazon_url=amazon_url.strip(),
        reference_image=reference_image,
        status="draft",
        created_at=datetime.now(timezone.utc).isoformat(),
        live_site_modified=False,
        requires_human_approval=True,
    )

    identity = {
        "product_id": product_id,
        "asin": asin,
        "canonical_amazon_url": canonical_amazon_url(asin),
        "amazon_product_title": None,
        "amazon_brand": None,
        "amazon_model": None,
        "amazon_size": None,
        "amazon_color": None,
        "amazon_key_specs": [],
        "verification_status": "draft",
        "identity_locked": False,
        "human_approved": False,
    }

    product = {
        "product_id": product_id,
        "title_de": None,
        "title_en": None,
        "short_description_de": None,
        "short_description_en": None,
        "long_description_de": None,
        "long_description_en": None,
        "features_de": [],
        "features_en": [],
        "tags": [],
        "seo": {},
        "status": "draft",
    }

    media = {
        "reference_image": reference_image,
        "website_image": None,
        "pinterest_image": None,
        "identity_preservation_required": True,
        "status": "pending",
    }

    approval = {
        "approved": False,
        "approved_by": None,
        "approved_at": None,
        "approval_note": None,
    }

    files = {
        "manifest.json": asdict(manifest),
        "identity.json": identity,
        "product.json": product,
        "media.json": media,
        "approval.json": approval,
    }

    for filename, content in files.items():
        (preview_root / filename).write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return preview_root


def hydrate_preview(
    *,
    root: Path,
    product_id: str,
) -> Path:
    product_id = validate_product_id(product_id)

    preview_root = (
        root
        / "data"
        / "product_factory"
        / "previews"
        / product_id
    )

    if not preview_root.exists():
        raise ProductFactoryError(
            f"Preview was not found: {product_id}"
        )

    products_payload = read_json(root / "data/products.json")
    products = products_payload.get("products", products_payload)

    product = next(
        (
            item
            for item in products
            if item.get("id") == product_id
        ),
        None,
    )

    if product is None:
        raise ProductFactoryError(
            f"Product does not exist in catalog: {product_id}"
        )

    if (
        product.get("verification_status") != "verified"
        or product.get("identity_locked") is not True
    ):
        raise ProductFactoryError(
            f"Product is not verified and locked: {product_id}"
        )

    reference_path = (
        root
        / "data"
        / "amazon_reference_images"
        / f"{product_id}.jpg"
    )
    candidate_path = (
        root
        / "inspection"
        / "candidates"
        / "website"
        / f"{product_id}.webp"
    )

    identity = {
        "product_id": product_id,
        "asin": product.get("verified_asin"),
        "canonical_amazon_url": product.get(
            "verified_amazon_url"
        ),
        "amazon_product_title": product.get(
            "amazon_product_title"
        ),
        "amazon_brand": product.get("amazon_brand"),
        "amazon_model": product.get("amazon_model"),
        "amazon_size": product.get("amazon_size"),
        "amazon_color": product.get("amazon_color"),
        "amazon_key_specs": product.get(
            "amazon_key_specs",
            [],
        ),
        "verification_status": product.get(
            "verification_status"
        ),
        "identity_locked": product.get(
            "identity_locked"
        ),
        "identity_hash": product.get("identity_hash"),
        "human_approved": False,
    }

    product_preview = {
        "product_id": product_id,
        "title": product.get("title"),
        "short_description": product.get(
            "short_description"
        ),
        "long_description": product.get(
            "long_description"
        ),
        "features": product.get("features", []),
        "tags": product.get("tags", []),
        "seo_title": product.get("seo_title"),
        "seo_description": product.get(
            "seo_description"
        ),
        "pinterest_title": product.get(
            "pinterest_title"
        ),
        "pinterest_description": product.get(
            "pinterest_description"
        ),
        "status": "verified_preview",
    }

    media = {
        "reference_image": (
            str(reference_path.relative_to(root))
            if reference_path.exists()
            else None
        ),
        "website_image": (
            str(candidate_path.relative_to(root))
            if candidate_path.exists()
            else None
        ),
        "pinterest_image": None,
        "identity_preservation_required": True,
        "status": (
            "candidate_ready"
            if candidate_path.exists()
            else "reference_ready"
            if reference_path.exists()
            else "pending"
        ),
    }

    for filename, payload in {
        "identity.json": identity,
        "product.json": product_preview,
        "media.json": media,
    }.items():
        (preview_root / filename).write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    manifest_path = preview_root / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["status"] = media["status"]
    manifest["reference_image"] = media["reference_image"]
    manifest["live_site_modified"] = False
    manifest["requires_human_approval"] = True

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    return preview_root
