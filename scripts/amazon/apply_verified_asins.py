import json
from pathlib import Path

from scripts.amazon.asin_utils import (
    build_product_url,
    extract_asin_from_url,
    is_valid_asin,
    normalize_asin,
)


PRODUCTS_PATH = Path("data/products.json")
VERIFICATION_PATH = Path("scripts/importers/asin_import_template.json")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_asin(entry):
    verified_asin = normalize_asin(entry.get("verified_asin"))

    if verified_asin:
        return verified_asin

    verified_url = str(entry.get("verified_amazon_url") or "").strip()

    if verified_url:
        extracted_asin = extract_asin_from_url(verified_url)

        if is_valid_asin(extracted_asin):
            return extracted_asin

    return ""


def main():
    products_data = load_json(PRODUCTS_PATH)
    products = products_data.get("products", products_data)

    verification_entries = load_json(VERIFICATION_PATH)
    verification_by_id = {
        entry.get("id"): entry
        for entry in verification_entries
        if entry.get("id")
    }

    changed = 0
    skipped = 0
    missing = 0

    print("=" * 70)
    print("APPLY VERIFIED ASINS")
    print("=" * 70)

    for product in products:
        product_id = product.get("id")
        entry = verification_by_id.get(product_id)

        if not entry:
            missing += 1
            print(f"[MISSING] {product_id}: no verification entry")
            continue

        asin = resolve_asin(entry)

        if not asin:
            skipped += 1
            print(f"[SKIP] {product_id}: no valid verified ASIN")
            continue

        product_url = build_product_url(asin)

        already_current = (
            product.get("amazon_asin") == asin
            and product.get("amazon_link_type") == "product"
            and product.get("verified_amazon_url") == product_url
        )

        if already_current:
            skipped += 1
            print(f"[OK] {product_id}: already current ({asin})")
            continue

        product["amazon_asin"] = asin
        product["amazon_link_type"] = "product"
        product["verified_amazon_url"] = product_url

        changed += 1
        print(f"[UPDATE] {product_id}: {asin}")

    if changed:
        save_json(PRODUCTS_PATH, products_data)

    print("\n" + "-" * 70)
    print(f"Products checked : {len(products)}")
    print(f"Updated          : {changed}")
    print(f"Skipped          : {skipped}")
    print(f"Missing entries  : {missing}")
    print("-" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
