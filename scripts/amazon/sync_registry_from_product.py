#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = ROOT / "data/products.json"
REGISTRY_PATH = ROOT / "scripts/importers/asin_import_template.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize one verified product into the Amazon identity registry."
    )
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    product_id = args.product_id.strip()

    if not re.fullmatch(r"camp-\d{3}", product_id):
        raise SystemExit("ERROR: product ID must look like camp-012")

    payload = load_json(PRODUCTS_PATH)
    products = payload.get("products", payload)

    product = next(
        (item for item in products if item.get("id") == product_id),
        None,
    )

    if product is None:
        raise SystemExit(f"ERROR: product not found: {product_id}")

    asin = str(
        product.get("verified_asin")
        or product.get("amazon_asin")
        or ""
    ).strip().upper()

    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise SystemExit("ERROR: product has no valid verified ASIN")

    canonical_url = f"https://www.amazon.de/dp/{asin}"

    if product.get("verification_status") != "verified":
        raise SystemExit("ERROR: verification_status is not verified")

    if product.get("identity_locked") is not True:
        raise SystemExit("ERROR: identity_locked is not true")

    key_specs = product.get("amazon_key_specs") or product.get("features") or []

    required_values = {
        "amazon_product_title": product.get("amazon_product_title") or product.get("title"),
        "amazon_brand": product.get("amazon_brand") or product.get("brand"),
        "amazon_model": product.get("amazon_model"),
        "amazon_key_specs": key_specs,
    }

    missing = [
        key for key, value in required_values.items()
        if not value
    ]

    if missing:
        raise SystemExit(
            "ERROR: products.json is missing: " + ", ".join(missing)
        )

    registry = load_json(REGISTRY_PATH)

    if not isinstance(registry, list):
        raise SystemExit("ERROR: registry must be a JSON list")

    record = next(
        (item for item in registry if item.get("id") == product_id),
        None,
    )

    new_record = {
        "id": product_id,
        "title": product.get("title"),
        "current_amazon_asin": asin,
        "verified_asin": asin,
        "verified_amazon_url": canonical_url,
        "status": "verified",
        "notes": (
            "Automatically synchronized from an already verified and locked "
            "product record."
        ),
        "amazon_product_title": required_values["amazon_product_title"],
        "amazon_brand": required_values["amazon_brand"],
        "amazon_model": required_values["amazon_model"],
        "verification_status": "verified",
        "verification_source": (
            product.get("verification_source")
            or canonical_url
        ),
        "amazon_size": product.get("amazon_size") or "",
        "amazon_color": product.get("amazon_color") or "",
        "amazon_key_specs": key_specs,
        "identity_locked": True,
        "identity_hash": product.get("identity_hash") or "",
    }

    action = "UPDATE" if record else "ADD"

    print("=" * 78)
    print("AMAZON REGISTRY SYNCHRONIZATION")
    print("=" * 78)
    print("Product :", product_id)
    print("ASIN    :", asin)
    print("Action  :", action)
    print("Mode    :", "WRITE" if args.write else "DRY RUN")
    print("=" * 78)
    print(json.dumps(new_record, ensure_ascii=False, indent=2))

    if not args.write:
        print("\nDry run completed. Registry was not changed.")
        return 0

    if record:
        index = registry.index(record)
        registry[index] = new_record
    else:
        registry.append(new_record)

    registry.sort(key=lambda item: item.get("id", ""))

    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n[PASS] Registry synchronized: {product_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
