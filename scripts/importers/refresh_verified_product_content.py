import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.product_refresh import refresh_verified_products


def main():
    parser = argparse.ArgumentParser(
        description="Refresh content for verified Amazon products."
    )

    parser.add_argument(
        "--product",
        help="Refresh only one product, for example camp-006.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("PRODUCT REFRESH ENGINE")
    print("=" * 70)

    result = refresh_verified_products(
        product_id=args.product,
        dry_run=args.dry_run,
    )

    for item in result["items"]:
        print(
            f"READY: {item['product_id']} - "
            f"{len(item['changed_fields'])} fields"
        )

        for field, new_value in item["changed_fields"].items():
            if field in {
                "seo_title",
                "seo_description",
                "pinterest_title",
                "buying_angle",
            }:
                old_value = item["product"].get(field)
                print(f"  {field}")
                print(f"    OLD: {old_value}")
                print(f"    NEW: {new_value}")

    print("-" * 70)
    print(f"Products prepared: {result['prepared']}")

    if result["dry_run"]:
        print("DRY RUN: No files changed.")
        return 0

    print(f"Products updated : {result['updated']}")

    if result["backup"]:
        print(f"Backup          : {result['backup']}")

    print("PRODUCT REFRESH COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
