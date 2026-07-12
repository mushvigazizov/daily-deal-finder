import json
from pathlib import Path

from core.i18n.german_content_builder import build_german_content
from core.i18n.language_guard import validate_language_content


PRODUCTS_PATH = Path("data/products.json")


def main():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products = data.get("products", [])

    passed = 0
    failed = 0

    print("=" * 72)
    print("GERMAN MASTER CONTENT VALIDATION")
    print("=" * 72)

    for product in products:
        product_id = product.get("id", "unknown")

        try:
            content = build_german_content(product)
            errors = validate_language_content(content, "de")
        except Exception as exc:
            failed += 1
            print(f"FAIL {product_id}")
            print(f"  - Builder error: {exc}")
            continue

        if errors:
            failed += 1
            print(f"FAIL {product_id}")
            for error in errors:
                print(f"  - {error}")
        else:
            passed += 1
            print(f"PASS {product_id}")

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Products checked : {len(products)}")
    print(f"Passed           : {passed}")
    print(f"Failed           : {failed}")
    print()
    print("No content files were created or changed.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
