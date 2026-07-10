import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs


PRODUCTS_PATH = Path("data/products.json")
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


def load_products():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    return data.get("products", data)


def classify_product(product):
    product_id = product.get("id", "unknown")
    asin = str(product.get("amazon_asin") or "").strip()
    link_type = str(product.get("amazon_link_type") or "").strip()
    verified_url = str(product.get("verified_amazon_url") or "").strip()

    problems = []

    if asin:
        if asin.startswith("s?") or "s?k=" in asin:
            problems.append("amazon_asin contains a search query instead of an ASIN")
        elif not ASIN_PATTERN.fullmatch(asin):
            problems.append("amazon_asin is not a valid 10-character ASIN")
    else:
        problems.append("amazon_asin is empty")

    if link_type == "product" and not verified_url:
        problems.append("product link type has no verified_amazon_url")

    if verified_url:
        parsed = urlparse(verified_url)

        if "amazon." not in parsed.netloc.lower():
            problems.append("verified_amazon_url is not an Amazon URL")

        # Affiliate tag ayrıca mərhələdə yoxlanacaq.
        # Hazırda canonical Amazon product URL etibarlı sayılır.

    return product_id, problems


def main():
    products = load_products()

    valid = 0
    invalid = 0

    print("=" * 70)
    print("AMAZON FIELD AUDIT")
    print("=" * 70)

    for product in products:
        product_id, problems = classify_product(product)

        if problems:
            invalid += 1
            print(f"\n[WARN] {product_id}")

            for problem in problems:
                print(f"  - {problem}")
        else:
            valid += 1
            print(f"[PASS] {product_id}")

    print("\n" + "-" * 70)
    print(f"Products checked : {len(products)}")
    print(f"Valid            : {valid}")
    print(f"Needs attention  : {invalid}")
    print("-" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
