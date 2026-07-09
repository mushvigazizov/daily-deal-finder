import json
from pathlib import Path
from collections import Counter

PRODUCTS_PATH = Path("data/products.json")
CATEGORIES_PATH = Path("data/categories.json")
ASSETS_ROOT = Path(".")

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    print("=" * 70)
    print("DAILY DEAL FINDER PROJECT HEALTH CHECK")
    print("=" * 70)

    errors = []
    warnings = []

    data = load_json(PRODUCTS_PATH)
    products = data.get("products", data)

    categories = load_json(CATEGORIES_PATH)
    official_categories = {c["slug"] for c in categories}

    ids = [p.get("id") for p in products]
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]

    if duplicate_ids:
        errors.append(f"Duplicate product IDs: {duplicate_ids}")

    invalid_categories = sorted({
        p.get("category", "MISSING")
        for p in products
        if p.get("category") not in official_categories
    })

    if invalid_categories:
        errors.append(f"Invalid categories: {invalid_categories}")

    missing_images = []
    missing_required = []
    missing_seo = []
    search_fallback_links = []

    required_fields = ["id", "title", "category", "short_description", "amazon_asin"]

    for product in products:
        pid = product.get("id", "UNKNOWN")

        missing = [field for field in required_fields if not product.get(field)]
        if missing:
            missing_required.append({"id": pid, "missing": missing})

        image = product.get("image")
        if image and not (ASSETS_ROOT / image).exists():
            missing_images.append({"id": pid, "image": image})

        if not product.get("seo_title") or not product.get("seo_description"):
            missing_seo.append(pid)

        asin = product.get("amazon_asin", "")
        if asin.startswith("s?k="):
            search_fallback_links.append(pid)

    if missing_required:
        errors.append(f"Products with missing required fields: {missing_required}")

    if missing_images:
        errors.append(f"Products with missing image files: {missing_images}")

    if missing_seo:
        warnings.append(f"Products missing SEO fields: {missing_seo}")

    if search_fallback_links:
        warnings.append(f"Products using Amazon search fallback links: {search_fallback_links}")

    print()
    print("SUMMARY")
    print("-" * 70)
    print(f"Products checked       : {len(products)}")
    print(f"Official categories    : {len(official_categories)}")
    print(f"Duplicate IDs          : {len(duplicate_ids)}")
    print(f"Invalid categories     : {len(invalid_categories)}")
    print(f"Missing image files    : {len(missing_images)}")
    print(f"Missing SEO fields     : {len(missing_seo)}")
    print(f"Search fallback links  : {len(search_fallback_links)}")
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
