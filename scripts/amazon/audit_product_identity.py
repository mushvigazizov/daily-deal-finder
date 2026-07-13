from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import Any

from core.amazon.identity import audit_product_identity


PRODUCTS_PATH = Path("data/products.json")


def load_products(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"ERROR: Product file was not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: Invalid JSON in {path}: {exc}"
        ) from exc

    products = payload.get("products", payload) if isinstance(payload, dict) else payload

    if not isinstance(products, list):
        raise SystemExit(
            "ERROR: products.json must contain a list or a 'products' list."
        )

    return products


def main() -> int:
    products = load_products(PRODUCTS_PATH)

    verified_count = 0
    review_count = 0
    search_count = 0

    print("=" * 78)
    print("AMAZON PRODUCT IDENTITY AUDIT")
    print("=" * 78)

    for product in products:
        result = audit_product_identity(product)

        product_id = product.get("id", "<missing-id>")
        website_title = product.get("title", "")
        asin = product.get("amazon_asin", "")

        if result.status == "verified":
            verified_count += 1
            print(f"[VERIFIED] {product_id}")
            print(f"  Website title : {website_title}")
            print(f"  ASIN          : {asin}")

        elif result.status == "review":
            review_count += 1
            print(f"[REVIEW] {product_id}")
            print(f"  Website title : {website_title}")
            print(f"  ASIN          : {asin}")

            for issue in result.issues:
                print(f"  - {issue}")

        else:
            search_count += 1
            print(f"[SEARCH] {product_id}")
            print(f"  Website title : {website_title}")
            print(f"  Status        : {result.issues[0]}")

        print()

    print("-" * 78)
    print(f"Fully verified products : {verified_count}")
    print(f"Products needing review : {review_count}")
    print(f"Search fallback products: {search_count}")
    print("-" * 78)

    # Search and review states are expected during gradual catalog verification.
    # The audit itself succeeds unless loading or parsing failed.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
