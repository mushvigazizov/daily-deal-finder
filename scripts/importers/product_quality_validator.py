from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_PRODUCTS_PATH = Path("data/products.json")

REQUIRED_FIELDS = [
    "id",
    "title",
    "category",
    "amazon_asin",
    "amazon_link_type",
    "image",
    "seo_title",
    "seo_description",
    "pinterest_title",
    "pinterest_description",
]

ALLOWED_CATEGORIES = {
    "camping",
    "outdoor",
    "kitchen",
    "home",
    "tech",
    "beauty",
    "pets",
    "gifts",
}

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


def load_products(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    products = data.get("products", data) if isinstance(data, dict) else data

    if not isinstance(products, list):
        raise ValueError("products data must be a list")

    return products


def validate_product(product: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [
        field
        for field in REQUIRED_FIELDS
        if product.get(field) is None
        or str(product.get(field)).strip() == ""
    ]

    if missing:
        errors.append("missing required fields: " + ", ".join(missing))

    category = product.get("category")
    asin = str(product.get("amazon_asin", "")).strip()
    link_type = str(product.get("amazon_link_type", "")).strip()

    if category not in ALLOWED_CATEGORIES:
        errors.append(f"invalid category: {category}")

    if link_type not in {"search", "product"}:
        errors.append(f"invalid amazon_link_type: {link_type}")
        return errors, warnings

    if link_type == "search":
        warnings.append("search fallback link still used")
        return errors, warnings

    if not ASIN_PATTERN.fullmatch(asin):
        errors.append(f"product link type but invalid ASIN: {asin}")
        return errors, warnings

    expected_url = f"https://www.amazon.de/dp/{asin}"

    amazon_url = str(product.get("amazon_url", "")).strip()
    verified_url = str(product.get("verified_amazon_url", "")).strip()

    if amazon_url != expected_url:
        errors.append("amazon_url does not match amazon_asin")

    if verified_url != expected_url:
        errors.append("verified_amazon_url does not match amazon_asin")

    if product.get("asin_verified") is not True:
        errors.append("asin_verified must be true")

    if product.get("verification_status") != "verified":
        errors.append("verification_status must be verified")

    if not str(product.get("asin_verified_at", "")).strip():
        errors.append("missing asin_verified_at")

    if not str(product.get("verification_source", "")).strip():
        errors.append("missing verification_source")

    return errors, warnings


def validate_products(
    products: list[dict[str, Any]],
) -> tuple[int, int]:
    products_with_errors = 0
    warning_count = 0

    print("=" * 70)
    print("PRODUCT QUALITY VALIDATOR")
    print("=" * 70)

    for product in products:
        product_id = product.get("id", "<missing-id>")
        title = product.get("title", "<missing-title>")

        errors, warnings = validate_product(product)

        if errors:
            products_with_errors += 1
            print(f"[ERROR] {product_id} | {title}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[ OK ]  {product_id}")

        for warning in warnings:
            warning_count += 1
            print(f"[WARN]  {product_id} | {warning}")

    print()
    print(f"Products checked      : {len(products)}")
    print(f"Warnings              : {warning_count}")
    print(f"Products with errors  : {products_with_errors}")

    if products_with_errors == 0:
        print("QUALITY CHECK PASSED")
    else:
        print("QUALITY CHECK FAILED")

    return products_with_errors, warning_count


def main() -> int:
    products = load_products(DEFAULT_PRODUCTS_PATH)
    errors, _warnings = validate_products(products)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
