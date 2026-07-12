import argparse
import json
from pathlib import Path

from core.i18n.german_content_builder import build_german_content
from core.i18n.localization_openai import generate_localized_content


PRODUCTS_PATH = Path("data/products.json")
CONTENT_DIR = Path("data/content")
DEFAULT_PRODUCT_ID = "camp-001"
TARGET_LANGUAGES = ("en", "ru")


def load_product(product_id):
    data = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )
    products = data.get("products", data)

    product = next(
        (
            item
            for item in products
            if item.get("id") == product_id
        ),
        None,
    )

    if not product:
        raise ValueError(f"Product not found: {product_id}")

    return product


def serialize_content(content):
    return json.dumps(
        content,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def write_atomically(path, text):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate validated English and Russian "
            "localized product content."
        )
    )
    parser.add_argument(
        "--product-id",
        default=DEFAULT_PRODUCT_ID,
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write both localized files only after "
            "both languages pass validation."
        ),
    )
    args = parser.parse_args()

    product = load_product(args.product_id)
    master_content = build_german_content(product)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    generated = {}
    failures = []

    print("=" * 76)
    print("LOCALIZED CONTENT GENERATOR")
    print("=" * 76)
    print(f"Product : {args.product_id}")
    print(f"Mode    : {'WRITE' if args.write else 'DRY RUN'}")
    print(f"Targets : {', '.join(TARGET_LANGUAGES)}")
    print()

    for language in TARGET_LANGUAGES:
        try:
            content = generate_localized_content(
                master_content,
                language,
            )
            generated[language] = content
            print(f"PASS {args.product_id}.{language}")
        except Exception as exc:
            failures.append((language, str(exc)))
            print(f"FAIL {args.product_id}.{language}")
            print(f"  - {exc}")

    print()

    if failures:
        print("BATCH ABORTED")
        print(
            "No localized files were written because "
            "at least one language failed."
        )
        print()
        print("=" * 76)
        print("SUMMARY")
        print("=" * 76)
        print(f"Languages checked : {len(TARGET_LANGUAGES)}")
        print(f"Passed            : {len(generated)}")
        print(f"Failed            : {len(failures)}")
        print("Written           : 0")
        return 1

    changed = 0
    unchanged = 0

    for language in TARGET_LANGUAGES:
        content = generated[language]
        target = CONTENT_DIR / f"{args.product_id}.{language}.json"
        generated_text = serialize_content(content)

        current_text = (
            target.read_text(encoding="utf-8")
            if target.exists()
            else None
        )

        if current_text == generated_text:
            unchanged += 1
            print(f"UNCHANGED {args.product_id}.{language}")
            continue

        changed += 1

        if args.write:
            write_atomically(target, generated_text)
            print(f"WRITTEN {args.product_id}.{language}")
        else:
            print(f"WOULD WRITE {args.product_id}.{language}")

        print(
            json.dumps(
                content,
                ensure_ascii=False,
                indent=2,
            )
        )
        print()

    print("=" * 76)
    print("SUMMARY")
    print("=" * 76)
    print(f"Languages checked : {len(TARGET_LANGUAGES)}")
    print(f"Passed            : {len(generated)}")
    print("Failed            : 0")
    print(f"Changed           : {changed}")
    print(f"Unchanged         : {unchanged}")
    print(f"Written           : {changed if args.write else 0}")

    if not args.write:
        print()
        print("Dry run only. No content files were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
