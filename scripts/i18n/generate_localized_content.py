import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from core.i18n.german_content_builder import build_german_content
from core.i18n.localization_openai import generate_localized_content
from core.i18n.content_hash import build_source_hash


PRODUCTS_PATH = Path("data/products.json")
CONTENT_DIR = Path("data/content")
DEFAULT_PRODUCT_ID = "camp-001"
TARGET_LANGUAGES = ("en", "ru")


def load_products():
    data = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )
    products = data.get("products", data)

    if not isinstance(products, list):
        raise ValueError("Products data must be a list")

    return products


def select_products(product_id=None, all_products=False):
    products = load_products()

    if all_products:
        return products

    selected_id = product_id or DEFAULT_PRODUCT_ID

    product = next(
        (
            item
            for item in products
            if item.get("id") == selected_id
        ),
        None,
    )

    if not product:
        raise ValueError(f"Product not found: {selected_id}")

    return [product]


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


def existing_language_files(product_id):
    return {
        language: CONTENT_DIR / f"{product_id}.{language}.json"
        for language in TARGET_LANGUAGES
    }


def generate_product(product, write=False, force=False):
    product_id = product.get("id")

    if not product_id:
        return {
            "product_id": None,
            "passed": 0,
            "failed": len(TARGET_LANGUAGES),
            "changed": 0,
            "unchanged": 0,
            "written": 0,
            "skipped": 0,
            "errors": ["Product is missing id"],
        }

    targets = existing_language_files(product_id)
    master_content = build_german_content(product)
    source_hash = build_source_hash(master_content)

    if not force:
        existing = [
            language
            for language, path in targets.items()
            if path.exists()
        ]

        if len(existing) == len(TARGET_LANGUAGES):
            stored_hashes = {}

            for language, target in targets.items():
                try:
                    current_content = json.loads(
                        target.read_text(encoding="utf-8")
                    )
                    stored_hashes[language] = current_content.get(
                        "source_hash"
                    )
                except (OSError, json.JSONDecodeError):
                    stored_hashes[language] = None

            hashes_current = all(
                stored_hashes.get(language) == source_hash
                for language in TARGET_LANGUAGES
            )

            if hashes_current:
                print("-" * 76)
                print(f"PRODUCT {product_id}")
                print("-" * 76)

                for language in TARGET_LANGUAGES:
                    print(
                        f"SKIPPED {product_id}.{language} "
                        "(source hash unchanged)"
                    )

                print()

                return {
                    "product_id": product_id,
                    "passed": len(TARGET_LANGUAGES),
                    "failed": 0,
                    "changed": 0,
                    "unchanged": 0,
                    "written": 0,
                    "skipped": len(TARGET_LANGUAGES),
                    "errors": [],
                }

            print("-" * 76)
            print(f"PRODUCT {product_id}")
            print("-" * 76)
            print("STALE LOCALIZATION DETECTED")
            print(f"Current source hash: {source_hash}")

            for language in TARGET_LANGUAGES:
                print(
                    f"{language}: stored hash="
                    f"{stored_hashes.get(language)!r}"
                )

            print("Regenerating both localized files.")
            print()

        if existing and len(existing) != len(TARGET_LANGUAGES):
            missing = [
                language
                for language in TARGET_LANGUAGES
                if language not in existing
            ]

            print("-" * 76)
            print(f"PRODUCT {product_id}")
            print("-" * 76)
            print(
                "PARTIAL LOCALIZATION DETECTED: "
                f"existing={', '.join(existing)}, "
                f"missing={', '.join(missing)}"
            )
            print(
                "Product aborted to preserve atomic "
                "EN/RU localization behavior."
            )
            print(
                "Use --force to regenerate both language files."
            )
            print()

            return {
                "product_id": product_id,
                "passed": 0,
                "failed": len(TARGET_LANGUAGES),
                "changed": 0,
                "unchanged": 0,
                "written": 0,
                "skipped": 0,
                "errors": [
                    "Partial localized file set detected"
                ],
            }

    generated_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    generated = {}
    errors = []

    print("-" * 76)
    print(f"PRODUCT {product_id}")
    print("-" * 76)

    for language in TARGET_LANGUAGES:
        try:
            content = generate_localized_content(
                master_content,
                language,
            )

            content["source"] = "localized_from_de_v2"
            content["source_language"] = "de"
            content["source_hash"] = source_hash
            content["generated_at"] = generated_at
            content["content_engine"] = "openai_localization_v2"

            generated[language] = content
            print(f"PASS {product_id}.{language}")
        except Exception as exc:
            errors.append(f"{language}: {exc}")
            print(f"FAIL {product_id}.{language}")
            print(f"  - {exc}")

    if errors:
        print(
            "PRODUCT ABORTED: no localized files were "
            "written for this product."
        )
        print()

        return {
            "product_id": product_id,
            "passed": len(generated),
            "failed": len(errors),
            "changed": 0,
            "unchanged": 0,
            "written": 0,
            "skipped": 0,
            "errors": errors,
        }

    changed = 0
    unchanged = 0
    written = 0

    for language in TARGET_LANGUAGES:
        content = generated[language]
        target = targets[language]
        generated_text = serialize_content(content)

        current_text = (
            target.read_text(encoding="utf-8")
            if target.exists()
            else None
        )

        if current_text == generated_text:
            unchanged += 1
            print(f"UNCHANGED {product_id}.{language}")
            continue

        changed += 1

        if write:
            write_atomically(target, generated_text)
            written += 1
            print(f"WRITTEN {product_id}.{language}")
        else:
            print(f"WOULD WRITE {product_id}.{language}")

    print()

    return {
        "product_id": product_id,
        "passed": len(generated),
        "failed": 0,
        "changed": changed,
        "unchanged": unchanged,
        "written": written,
        "skipped": 0,
        "errors": [],
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate validated English and Russian "
            "localized product content."
        )
    )

    selection = parser.add_mutually_exclusive_group()

    selection.add_argument(
        "--product-id",
        help=(
            "Generate localization for one product. "
            f"Defaults to {DEFAULT_PRODUCT_ID}."
        ),
    )

    selection.add_argument(
        "--all-products",
        action="store_true",
        help="Generate localization for every product.",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write both localized files for a product only "
            "after both languages pass validation."
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Regenerate existing localized files. "
            "Without this flag, complete existing EN/RU "
            "file pairs are skipped."
        ),
    )

    args = parser.parse_args()

    products = select_products(
        product_id=args.product_id,
        all_products=args.all_products,
    )

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    mode = "WRITE" if args.write else "DRY RUN"
    scope = (
        "ALL PRODUCTS"
        if args.all_products
        else (args.product_id or DEFAULT_PRODUCT_ID)
    )

    print("=" * 76)
    print("LOCALIZED CONTENT GENERATOR")
    print("=" * 76)
    print(f"Scope   : {scope}")
    print(f"Products: {len(products)}")
    print(f"Mode    : {mode}")
    print(f"Force   : {'YES' if args.force else 'NO'}")
    print(f"Targets : {', '.join(TARGET_LANGUAGES)}")
    print()

    results = [
        generate_product(
            product,
            write=args.write,
            force=args.force,
        )
        for product in products
    ]

    products_passed = sum(
        result["failed"] == 0
        for result in results
    )
    products_failed = len(results) - products_passed
    languages_passed = sum(
        result["passed"]
        for result in results
    )
    languages_failed = sum(
        result["failed"]
        for result in results
    )
    changed = sum(
        result["changed"]
        for result in results
    )
    unchanged = sum(
        result["unchanged"]
        for result in results
    )
    written = sum(
        result["written"]
        for result in results
    )
    skipped = sum(
        result["skipped"]
        for result in results
    )

    print("=" * 76)
    print("SUMMARY")
    print("=" * 76)
    print(f"Products checked  : {len(results)}")
    print(f"Products passed   : {products_passed}")
    print(f"Products failed   : {products_failed}")
    print(f"Languages passed  : {languages_passed}")
    print(f"Languages failed  : {languages_failed}")
    print(f"Changed           : {changed}")
    print(f"Unchanged         : {unchanged}")
    print(f"Skipped existing  : {skipped}")
    print(f"Written           : {written}")

    if not args.write:
        print()
        print("Dry run only. No content files were changed.")

    if products_failed:
        print()
        print("LOCALIZATION GENERATION FAILED")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
