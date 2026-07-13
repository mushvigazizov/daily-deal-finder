from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.amazon.identity_lock import validate_identity_for_lock


REGISTRY_PATH = Path("scripts/importers/asin_import_template.json")


def load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"ERROR: Registry not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: Invalid JSON in {path}: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise SystemExit("ERROR: Registry must contain a JSON list.")

    return payload


def write_registry(
    path: Path,
    registry: list[dict[str, Any]],
) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)


def lock_product(
    registry: list[dict[str, Any]],
    product_id: str,
) -> tuple[bool, tuple[str, ...]]:
    record = next(
        (
            item
            for item in registry
            if item.get("id") == product_id
        ),
        None,
    )

    if record is None:
        return False, (f"product not found: {product_id}",)

    validation = validate_identity_for_lock(record)

    if not validation.valid:
        return False, validation.issues

    record["identity_hash"] = validation.identity_hash
    record["identity_locked"] = True
    record["status"] = "verified"
    record["verification_status"] = "verified"

    return True, ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and lock one Amazon product identity "
            "inside the identity registry."
        )
    )

    parser.add_argument(
        "--product-id",
        required=True,
        help="Product ID, for example camp-001.",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the validated lock to the registry.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_registry(REGISTRY_PATH)

    success, issues = lock_product(
        registry,
        args.product_id,
    )

    print("=" * 78)
    print("AMAZON PRODUCT IDENTITY LOCK")
    print("=" * 78)
    print(f"Product ID : {args.product_id}")

    if not success:
        print("Result     : REJECTED")

        for issue in issues:
            print(f"  - {issue}")

        return 1

    record = next(
        item
        for item in registry
        if item.get("id") == args.product_id
    )

    print("Result     : VALID")
    print(f"ASIN       : {record.get('verified_asin')}")
    print(f"Brand      : {record.get('amazon_brand')}")
    print(f"Model      : {record.get('amazon_model')}")
    print(f"Hash       : {record.get('identity_hash')}")

    if not args.write:
        print("Write mode : DRY RUN")
        print("Registry was not changed.")
        return 0

    write_registry(REGISTRY_PATH, registry)

    print("Write mode : WRITTEN")
    print(f"Registry   : {REGISTRY_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
