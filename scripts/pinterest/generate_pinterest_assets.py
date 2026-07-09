import json
#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datetime import datetime, UTC
from core.products import load_products

ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = ROOT / "data" / "products.json"
OUT_DIR = ROOT / "reports" / "pinterest"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def safe(value, fallback=""):
    return str(value or fallback).strip()

def make_pin(product):
    title = safe(product.get("title"), "Smart Product Pick")
    category = safe(product.get("category"), "Shopping")
    subcategory = safe(product.get("subcategory"), category)
    description = safe(product.get("description"), "")

    pin_title = f"{title} | Smart {subcategory} Find"

    pin_description = (
        f"Discover this {subcategory.lower()} pick for everyday use. "
        f"A practical product idea for smart shoppers looking for useful finds. "
        f"See details, features, and buying angle on Daily Deal Finder."
    )

    if description:
        pin_description = pin_description + " " + description[:180]

    image_prompt = (
        f"Create a premium Pinterest pin for a product in the {subcategory} category. "
        f"Clean modern ecommerce style, vertical 2:3 layout, bright natural lighting, "
        f"high trust shopping design, clear product focus, minimal text space, "
        f"premium lifestyle background, suitable for Daily Deal Finder."
    )

    return {
        "product_id": product.get("id"),
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "pin_title": pin_title[:100],
        "pin_description": pin_description[:500],
        "image_prompt": image_prompt,
        "target_url": product.get("url") or product.get("amazon_url") or "",
        "created_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    }

def main():
    products = load_products()
    pins = [make_pin(p) for p in products]

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = OUT_DIR / f"{stamp}.json"
    latest_file = OUT_DIR / "latest.json"

    payload = {
        "generated_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        "count": len(pins),
        "pins": pins
    }

    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 70)
    print("PINTEREST ASSET GENERATOR")
    print("=" * 70)
    print(f"Products processed: {len(pins)}")
    print(f"Report: {out_file}")
    print("Status: PASS")

if __name__ == "__main__":
    main()
