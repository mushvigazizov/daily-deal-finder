from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.amazon.identity_lock import (
    canonical_identity,
    verify_existing_lock,
)


PRODUCTS_PATH = Path("data/products.json")
REGISTRY_PATH = Path("scripts/importers/asin_import_template.json")
BACKUP_DIR = Path("backups/products")


IDENTITY_COPY_FIELDS = (
    "verified_asin",
    "verified_amazon_url",
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
    "amazon_size",
    "amazon_color",
    "amazon_key_specs",
    "verification_status",
    "verification_source",
    "identity_hash",
    "identity_locked",
)


class ApplyLockedIdentityError(ValueError):
    """Raised when a locked Amazon identity cannot be applied safely."""


def load_json(path: Path) -> Any:
    if not path.exists():
        raise ApplyLockedIdentityError(f"file not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApplyLockedIdentityError(
            f"invalid JSON in {path}: {exc}"
        ) from exc


def extract_products(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        products = payload.get("products")
    else:
        products = payload

    if not isinstance(products, list):
        raise ApplyLockedIdentityError(
            "products.json must contain a list or a 'products' list"
        )

    if not all(isinstance(item, dict) for item in products):
        raise ApplyLockedIdentityError(
            "every product entry must be a JSON object"
        )

    return products


def extract_registry(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ApplyLockedIdentityError(
            "identity registry must contain a JSON list"
        )

    if not all(isinstance(item, dict) for item in payload):
        raise ApplyLockedIdentityError(
            "every registry entry must be a JSON object"
        )

    return payload


def build_unique_index(
    records: list[dict[str, Any]],
    *,
    source_name: str,
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for record in records:
        product_id = str(record.get("id", "")).strip()

        if not product_id:
            raise ApplyLockedIdentityError(
                f"{source_name} contains an entry without id"
            )

        if product_id in index:
            raise ApplyLockedIdentityError(
                f"duplicate product id in {source_name}: {product_id}"
            )

        index[product_id] = record

    return index


def locked_registry_records(
    registry: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        record
        for record in registry
        if record.get("identity_locked") is True
    ]


def validate_locked_registry(
    registry: list[dict[str, Any]],
    products_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    locked_records = locked_registry_records(registry)

    seen_asins: dict[str, str] = {}
    prepared: list[dict[str, Any]] = []
    errors: list[str] = []

    for record in locked_records:
        product_id = str(record.get("id", "")).strip()

        if not product_id:
            errors.append("locked registry entry has no product id")
            continue

        if product_id not in products_by_id:
            errors.append(
                f"{product_id}: product does not exist in products.json"
            )
            continue

        lock_result = verify_existing_lock(record)

        if not lock_result.valid:
            for issue in lock_result.issues:
                errors.append(f"{product_id}: {issue}")
            continue

        identity = canonical_identity(record)
        asin = identity["verified_asin"]

        previous_owner = seen_asins.get(asin)

        if previous_owner and previous_owner != product_id:
            errors.append(
                f"duplicate locked ASIN {asin}: "
                f"{previous_owner} and {product_id}"
            )
            continue

        seen_asins[asin] = product_id

        prepared.append(
            {
                "product_id": product_id,
                "record": record,
                "identity": identity,
                "identity_hash": lock_result.identity_hash,
            }
        )

    if errors:
        raise ApplyLockedIdentityError("\n".join(errors))

    return prepared


def apply_identity_to_product(
    product: dict[str, Any],
    record: dict[str, Any],
    *,
    applied_at: str,
) -> bool:
    before = deepcopy(product)
    identity = canonical_identity(record)

    for field_name in IDENTITY_COPY_FIELDS:
        if field_name in record:
            product[field_name] = deepcopy(record[field_name])

    asin = identity["verified_asin"]
    canonical_url = identity["verified_amazon_url"]

    product["amazon_asin"] = asin
    product["verified_asin"] = asin
    product["verified_amazon_url"] = canonical_url
    product["amazon_url"] = canonical_url
    product["amazon_link_type"] = "product"
    product["asin_verified"] = True
    product["asin_verified_at"] = applied_at

    product["amazon_product_title"] = identity[
        "amazon_product_title"
    ]
    product["amazon_brand"] = identity["amazon_brand"]
    product["amazon_model"] = identity["amazon_model"]
    product["amazon_size"] = identity["amazon_size"]
    product["amazon_color"] = identity["amazon_color"]
    product["amazon_key_specs"] = identity["amazon_key_specs"]
    product["verification_status"] = identity[
        "verification_status"
    ]
    product["verification_source"] = identity[
        "verification_source"
    ]
    product["identity_hash"] = record["identity_hash"]
    product["identity_locked"] = True
    product["identity_applied_at"] = applied_at

    return product != before


def prepare_application(
    products_payload: Any,
    registry_payload: Any,
    *,
    applied_at: str,
) -> tuple[Any, list[str], list[str]]:
    updated_payload = deepcopy(products_payload)
    products = extract_products(updated_payload)
    registry = extract_registry(registry_payload)

    products_by_id = build_unique_index(
        products,
        source_name="products.json",
    )
    build_unique_index(
        registry,
        source_name="identity registry",
    )

    prepared = validate_locked_registry(
        registry,
        products_by_id,
    )

    changed_ids: list[str] = []
    unchanged_ids: list[str] = []

    for item in prepared:
        product_id = item["product_id"]
        product = products_by_id[product_id]
        record = item["record"]

        changed = apply_identity_to_product(
            product,
            record,
            applied_at=applied_at,
        )

        if changed:
            changed_ids.append(product_id)
        else:
            unchanged_ids.append(product_id)

    return updated_payload, changed_ids, unchanged_ids


def write_json_atomic(path: Path, payload: Any) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)


def create_backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d-%H%M%SZ"
    )
    backup_path = BACKUP_DIR / f"products-{timestamp}.json"

    shutil.copy2(path, backup_path)

    return backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply only cryptographically locked Amazon product "
            "identities from the registry to products.json."
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Write approved identity updates to products.json.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products_payload = load_json(PRODUCTS_PATH)
        registry_payload = load_json(REGISTRY_PATH)

        applied_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")

        updated_payload, changed_ids, unchanged_ids = (
            prepare_application(
                products_payload,
                registry_payload,
                applied_at=applied_at,
            )
        )
    except ApplyLockedIdentityError as exc:
        print("=" * 78)
        print("APPLY LOCKED AMAZON PRODUCT IDENTITIES")
        print("=" * 78)
        print("Result : REJECTED")

        for line in str(exc).splitlines():
            print(f"  - {line}")

        print("No files were changed.")
        return 1

    locked_count = len(changed_ids) + len(unchanged_ids)

    print("=" * 78)
    print("APPLY LOCKED AMAZON PRODUCT IDENTITIES")
    print("=" * 78)
    print(f"Locked identities : {locked_count}")
    print(f"Changed products  : {len(changed_ids)}")
    print(f"Unchanged products: {len(unchanged_ids)}")

    for product_id in changed_ids:
        print(f"  APPLY     : {product_id}")

    for product_id in unchanged_ids:
        print(f"  UNCHANGED : {product_id}")

    if not args.write:
        print("Write mode        : DRY RUN")
        print("Products file was not changed.")
        return 0

    if not changed_ids:
        print("Write mode        : NO CHANGES")
        print("Products file was not changed.")
        return 0

    backup_path = create_backup(PRODUCTS_PATH)
    write_json_atomic(PRODUCTS_PATH, updated_payload)

    print("Write mode        : WRITTEN")
    print(f"Backup            : {backup_path}")
    print(f"Products          : {PRODUCTS_PATH}")
    print("SAFE IDENTITY APPLICATION COMPLETED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
