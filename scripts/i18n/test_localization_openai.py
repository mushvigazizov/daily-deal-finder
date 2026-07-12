import json
from pathlib import Path

from core.i18n.german_content_builder import (
    build_german_content,
)
from core.i18n.localization_openai import (
    generate_localized_content,
)


PRODUCTS_PATH = Path("data/products.json")
PRODUCT_ID = "camp-001"
TARGET_LANGUAGES = ("en", "ru")


def main():
    data = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )
    products = data.get("products", data)

    product = next(
        (
            item
            for item in products
            if item.get("id") == PRODUCT_ID
        ),
        None,
    )

    if not product:
        raise SystemExit(
            f"Product not found: {PRODUCT_ID}"
        )

    master_content = build_german_content(product)

    print("=" * 76)
    print("LOCALIZATION OPENAI TEST")
    print("=" * 76)
    print(f"Product : {PRODUCT_ID}")
    print(f"Targets : {', '.join(TARGET_LANGUAGES)}")
    print("Write   : disabled")
    print()

    failed = 0

    for language in TARGET_LANGUAGES:
        print("=" * 76)
        print(f"TARGET LANGUAGE: {language}")
        print("=" * 76)

        try:
            content = generate_localized_content(
                master_content,
                language,
            )
        except Exception as exc:
            failed += 1
            print(f"FAIL {PRODUCT_ID}.{language}")
            print(exc)
            print()
            continue

        print(f"PASS {PRODUCT_ID}.{language}")
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
    print(f"Languages tested : {len(TARGET_LANGUAGES)}")
    print(
        f"Passed           : "
        f"{len(TARGET_LANGUAGES) - failed}"
    )
    print(f"Failed           : {failed}")
    print()
    print("No content files were created or changed.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
