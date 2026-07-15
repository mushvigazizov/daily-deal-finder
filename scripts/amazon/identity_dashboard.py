from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PRODUCTS_PATH = Path("data/products.json")


def load_products(path: Path = PRODUCTS_PATH) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    products = payload.get("products", payload)

    if not isinstance(products, list):
        raise ValueError("products payload must be a list")

    return products


def is_verified(product: dict[str, Any]) -> bool:
    return (
        product.get("identity_locked") is True
        and product.get("verification_status") == "verified"
        and bool(product.get("verified_asin"))
        and product.get("amazon_link_type") == "product"
    )


def is_search_fallback(product: dict[str, Any]) -> bool:
    asin = str(product.get("amazon_asin", ""))
    return (
        product.get("amazon_link_type") == "search"
        or asin.startswith("s?k=")
    )


def is_review_required(product: dict[str, Any]) -> bool:
    return (
        product.get("verification_status") == "review_required"
        and not is_verified(product)
    )


def is_publish_ready(product: dict[str, Any]) -> bool:
    return (
        product.get("active") is True
        and is_verified(product)
        and bool(product.get("image"))
        and bool(product.get("seo_title"))
        and bool(product.get("seo_description"))
    )


def build_dashboard(products: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(products)

    verified = [
        product for product in products
        if is_verified(product)
    ]
    review_required = [
        product for product in products
        if is_review_required(product)
    ]
    search_fallback = [
        product for product in products
        if is_search_fallback(product)
    ]
    locked = [
        product for product in products
        if product.get("identity_locked") is True
    ]
    product_urls = [
        product for product in products
        if product.get("amazon_link_type") == "product"
    ]
    publish_ready = [
        product for product in products
        if is_publish_ready(product)
    ]

    coverage = (len(verified) / total * 100) if total else 0.0

    return {
        "total": total,
        "verified": len(verified),
        "review_required": len(review_required),
        "search_fallback": len(search_fallback),
        "locked": len(locked),
        "product_urls": len(product_urls),
        "search_urls": len(search_fallback),
        "publish_ready": len(publish_ready),
        "not_ready": total - len(publish_ready),
        "coverage": coverage,
        "verified_ids": [
            product.get("id", "UNKNOWN")
            for product in verified
        ],
        "pending_ids": [
            product.get("id", "UNKNOWN")
            for product in products
            if not is_verified(product)
        ],
    }


def main() -> None:
    products = load_products()
    dashboard = build_dashboard(products)

    print("=" * 72)
    print("AMAZON IDENTITY DASHBOARD")
    print("=" * 72)
    print()
    print(f"Products                     : {dashboard['total']}")
    print()
    print(f"Verified                     : {dashboard['verified']}")
    print(f"Review required              : {dashboard['review_required']}")
    print(f"Search fallback              : {dashboard['search_fallback']}")
    print()
    print(
        "Identity coverage            : "
        f"{dashboard['coverage']:.1f}%"
    )
    print()
    print(f"Locked identities            : {dashboard['locked']}")
    print(f"Amazon product URLs          : {dashboard['product_urls']}")
    print(f"Amazon search URLs           : {dashboard['search_urls']}")
    print()
    print(f"Ready for publish            : {dashboard['publish_ready']}")
    print(f"Not ready                    : {dashboard['not_ready']}")
    print()
    print("-" * 72)
    print(
        "Verified IDs                : "
        + (
            ", ".join(dashboard["verified_ids"])
            if dashboard["verified_ids"]
            else "none"
        )
    )
    print(
        "Pending IDs                 : "
        + (
            ", ".join(dashboard["pending_ids"])
            if dashboard["pending_ids"]
            else "none"
        )
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
