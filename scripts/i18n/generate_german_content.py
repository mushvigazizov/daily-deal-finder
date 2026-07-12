import argparse
import json
import sys
from pathlib import Path

from core.i18n.german_content_builder import build_german_content
from core.i18n.language_guard import validate_language_content


PRODUCTS_PATH = Path("data/products.json")
CONTENT_DIR = Path("data/content")


def load_products():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products = data.get("products", data)

    if not isinstance(products, list):
        raise ValueError("data/products.json must contain a product list")

    return products


def serialize_content(content):
    return json.dumps(
        content,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate validated German content files."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changed files. Without this flag, only perform a dry run.",
    )
    args = parser.parse_args()

    products = load_products()
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    changed = 0
    unchanged = 0
    failed = 0

    print("=" * 72)
    print("GERMAN CONTENT GENERATOR")
    print("=" * 72)
    print(f"Mode: {'WRITE' if args.write else 'DRY RUN'}")
    print()

    for product in products:
        product_id = product.get("id", "").strip()

        if not product_id:
            failed += 1
            print("FAIL unknown")
            print("  - Product has no id")
            continue

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
            continue

        target = CONTENT_DIR / f"{product_id}.de.json"
        generated_text = serialize_content(content)

        current_text = (
            target.read_text(encoding="utf-8")
            if target.exists()
            else None
        )

        if current_text == generated_text:
            unchanged += 1
            print(f"UNCHANGED {product_id}")
            continue

        changed += 1

        if args.write:
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(generated_text, encoding="utf-8")
            temporary.replace(target)
            print(f"UPDATED {product_id}")
        else:
            print(f"WOULD UPDATE {product_id}")

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Products checked : {len(products)}")
    print(f"Changed          : {changed}")
    print(f"Unchanged        : {unchanged}")
    print(f"Failed           : {failed}")

    if not args.write:
        print()
        print("Dry run only. No content files were changed.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
