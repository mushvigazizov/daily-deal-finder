import json
from collections import Counter
from pathlib import Path


PRODUCTS_PATH = Path("data/products.json")
CATEGORIES_PATH = Path("data/categories.json")
ASSETS_ROOT = Path(".")


BASE_REQUIRED_FIELDS = {
    "id",
    "sku",
    "title",
    "brand",
    "category",
    "subcategory",
    "short_description",
    "long_description",
    "features",
    "image",
    "amazon_asin",
    "amazon_link_type",
    "seo_title",
    "seo_description",
    "pinterest_title",
    "pinterest_description",
    "active",
}

VERIFIED_IDENTITY_FIELDS = {
    "verified_asin",
    "verified_amazon_url",
    "amazon_url",
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
    "amazon_key_specs",
    "verification_status",
    "verification_source",
    "identity_locked",
    "identity_hash",
    "identity_applied_at",
    "asin_verified",
    "asin_verified_at",
}

OPTIONAL_IDENTITY_FIELDS = {
    "amazon_size",
    "amazon_color",
}

ALLOWED_OPTIONAL_FIELDS = {
    "availability",
    "button_text",
    "buying_angle",
    "content_engine",
    "content_refreshed_at",
    "content_status",
    "created_at",
    "featured",
    "gallery",
    "manufacturer_source",
    "rating",
    "review_count",
    "tags",
    "updated_at",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_verified_product(product: dict) -> bool:
    return (
        product.get("identity_locked") is True
        and product.get("verification_status") == "verified"
        and bool(product.get("verified_asin"))
    )


def is_missing_base_field(product: dict, field: str) -> bool:
    if field not in product:
        return True

    value = product[field]

    if field == "active":
        return not isinstance(value, bool)

    return value in (None, "", [])


def main() -> None:
    print("=" * 70)
    print("DAILY DEAL FINDER PROJECT HEALTH CHECK")
    print("=" * 70)

    errors: list[str] = []
    warnings: list[str] = []

    data = load_json(PRODUCTS_PATH)
    products = data.get("products", data)

    categories = load_json(CATEGORIES_PATH)
    official_categories = {category["slug"] for category in categories}

    base_field_issues = []
    verified_identity_issues = []
    unexpected_extra_fields = []

    known_fields = (
        BASE_REQUIRED_FIELDS
        | VERIFIED_IDENTITY_FIELDS
        | OPTIONAL_IDENTITY_FIELDS
        | ALLOWED_OPTIONAL_FIELDS
    )

    for product in products:
        pid = product.get("id", "UNKNOWN")
        keys = set(product.keys())

        missing_base = sorted(
            field
            for field in BASE_REQUIRED_FIELDS
            if is_missing_base_field(product, field)
        )
        if missing_base:
            base_field_issues.append(
                {
                    "id": pid,
                    "missing": missing_base,
                }
            )

        if is_verified_product(product):
            missing_identity = sorted(
                field
                for field in VERIFIED_IDENTITY_FIELDS
                if product.get(field) in (None, "", [], False)
            )
            if missing_identity:
                verified_identity_issues.append(
                    {
                        "id": pid,
                        "missing": missing_identity,
                    }
                )

        extra_fields = sorted(keys - known_fields)
        if extra_fields:
            unexpected_extra_fields.append(
                {
                    "id": pid,
                    "extra": extra_fields,
                }
            )

    if base_field_issues:
        errors.append(
            f"Products with missing base fields: {base_field_issues}"
        )

    if verified_identity_issues:
        errors.append(
            "Verified products with incomplete identity fields: "
            f"{verified_identity_issues}"
        )

    if unexpected_extra_fields:
        warnings.append(
            f"Products with unexpected fields: {unexpected_extra_fields}"
        )

    ids = [product.get("id") for product in products]
    duplicate_ids = [
        item
        for item, count in Counter(ids).items()
        if count > 1
    ]

    if duplicate_ids:
        errors.append(f"Duplicate product IDs: {duplicate_ids}")

    invalid_categories = sorted(
        {
            product.get("category", "MISSING")
            for product in products
            if product.get("category") not in official_categories
        }
    )

    if invalid_categories:
        errors.append(f"Invalid categories: {invalid_categories}")

    missing_images = []
    missing_seo = []
    search_fallback_links = []
    verified_products = []

    for product in products:
        pid = product.get("id", "UNKNOWN")

        image = product.get("image")
        if image and not (ASSETS_ROOT / image).exists():
            missing_images.append(
                {
                    "id": pid,
                    "image": image,
                }
            )

        if (
            not product.get("seo_title")
            or not product.get("seo_description")
        ):
            missing_seo.append(pid)

        asin = str(product.get("amazon_asin", ""))
        if asin.startswith("s?k="):
            search_fallback_links.append(pid)

        if is_verified_product(product):
            verified_products.append(pid)

    if missing_images:
        errors.append(
            f"Products with missing image files: {missing_images}"
        )

    if missing_seo:
        warnings.append(
            f"Products missing SEO fields: {missing_seo}"
        )

    if search_fallback_links:
        warnings.append(
            "Products using Amazon search fallback links: "
            f"{search_fallback_links}"
        )

    field_consistency_ok = (
        not base_field_issues
        and not verified_identity_issues
        and not unexpected_extra_fields
    )

    print()
    print("SUMMARY")
    print("-" * 70)
    print(f"Products checked       : {len(products)}")
    print(f"Official categories    : {len(official_categories)}")
    print(
        "Field consistency      : "
        f"{'OK' if field_consistency_ok else 'WARN'}"
    )
    print(f"Verified products      : {len(verified_products)}")
    print(f"Search fallback links  : {len(search_fallback_links)}")
    print(f"Duplicate IDs          : {len(duplicate_ids)}")
    print(f"Invalid categories     : {len(invalid_categories)}")
    print(f"Missing image files    : {len(missing_images)}")
    print(f"Missing SEO fields     : {len(missing_seo)}")
    print(f"Errors                 : {len(errors)}")
    print(f"Warnings               : {len(warnings)}")
    print()

    if warnings:
        print("WARNINGS")
        print("-" * 70)
        for warning in warnings:
            print("[WARN]", warning)
        print()

    if errors:
        print("ERRORS")
        print("-" * 70)
        for error in errors:
            print("[ERROR]", error)
        print()
        print("HEALTH CHECK FAILED")
        raise SystemExit(1)

    print("HEALTH CHECK PASSED")


if __name__ == "__main__":
    main()
