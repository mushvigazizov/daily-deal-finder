import json
from pathlib import Path

from core.i18n.german_content_builder import build_german_content
from core.i18n.localization_prompt_builder import build_localization_prompt


PRODUCTS_PATH = Path("data/products.json")
PRODUCT_ID = "camp-001"
TARGET_LANGUAGES = ("en", "ru")


def main():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products = data.get("products", [])

    product = next(
        (
            item
            for item in products
            if item.get("id") == PRODUCT_ID
        ),
        None,
    )

    if not product:
        raise SystemExit(f"Product not found: {PRODUCT_ID}")

    master_content = build_german_content(product)

    print("=" * 76)
    print("LOCALIZATION PROMPT DRY RUN")
    print("=" * 76)
    print("Product :", PRODUCT_ID)
    print("Source  : German master content")
    print("Targets :", ", ".join(TARGET_LANGUAGES))
    print()

    for language in TARGET_LANGUAGES:
        prompt = build_localization_prompt(
            master_content,
            language,
        )

        print("=" * 76)
        print(f"TARGET LANGUAGE: {language}")
        print("=" * 76)
        print(prompt)
        print()

    print("=" * 76)
    print("DRY RUN COMPLETE")
    print("=" * 76)
    print("No API calls were made.")
    print("No content files were created or changed.")


if __name__ == "__main__":
    main()
