from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.amazon.identity_lock import canonical_identity
from scripts.amazon.apply_locked_product_identities import (
    ApplyLockedIdentityError,
    build_unique_index,
    extract_products,
    extract_registry,
    load_json,
    validate_locked_registry,
)


PRODUCTS_PATH = Path("data/products.json")
REGISTRY_PATH = Path(
    "scripts/importers/asin_import_template.json"
)


PROTECTED_IDENTITY_FIELDS = (
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


DERIVED_PRODUCT_FIELDS = {
    "amazon_link_type": "product",
    "asin_verified": True,
    "identity_locked": True,
}


class IdentityGuardError(ValueError):
    """Raised when locked product identity integrity is violated."""


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return [
            normalize_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: normalize_value(item)
            for key, item in value.items()
        }

    return value


def expected_product_identity(
    registry_record: dict[str, Any],
) -> dict[str, Any]:
    identity = canonical_identity(registry_record)

    expected = {
        field_name: normalize_value(
            registry_record.get(field_name)
        )
        for field_name in PROTECTED_IDENTITY_FIELDS
    }

    expected.update(
        {
            "verified_asin": identity["verified_asin"],
            "verified_amazon_url": identity[
                "verified_amazon_url"
            ],
            "amazon_product_title": identity[
                "amazon_product_title"
            ],
            "amazon_brand": identity["amazon_brand"],
            "amazon_model": identity["amazon_model"],
            "amazon_size": identity["amazon_size"],
            "amazon_color": identity["amazon_color"],
            "amazon_key_specs": identity[
                "amazon_key_specs"
            ],
            "verification_status": identity[
                "verification_status"
            ],
            "verification_source": identity[
                "verification_source"
            ],
        }
    )

    return expected


def guard_locked_identities(
    products_payload: Any,
    registry_payload: Any,
) -> list[str]:
    products = extract_products(products_payload)
    registry = extract_registry(registry_payload)

    products_by_id = build_unique_index(
        products,
        source_name="products.json",
    )
    registry_by_id = build_unique_index(
        registry,
        source_name="identity registry",
    )

    try:
        prepared = validate_locked_registry(
            registry,
            products_by_id,
        )
    except ApplyLockedIdentityError as exc:
        raise IdentityGuardError(str(exc)) from exc

    locked_registry_ids = {
        item["product_id"]
        for item in prepared
    }

    errors: list[str] = []
    verified_ids: list[str] = []

    for item in prepared:
        product_id = item["product_id"]
        registry_record = item["record"]
        product = products_by_id[product_id]

        expected = expected_product_identity(
            registry_record
        )

        try:
            actual_identity = canonical_identity(product)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(
                f"{product_id}: product identity cannot be "
                f"canonicalized ({exc})"
            )
            continue

        canonical_fields = (
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
        )

        for field_name in canonical_fields:
            expected_value = normalize_value(
                expected[field_name]
            )
            actual_value = normalize_value(
                actual_identity[field_name]
            )

            if actual_value != expected_value:
                errors.append(
                    f"{product_id}: {field_name} mismatch "
                    f"(expected {expected_value!r}, "
                    f"found {actual_value!r})"
                )

        for field_name in (
            "identity_hash",
            "identity_locked",
        ):
            expected_value = normalize_value(
                expected[field_name]
            )
            actual_value = normalize_value(
                product.get(field_name)
            )

            if actual_value != expected_value:
                errors.append(
                    f"{product_id}: {field_name} mismatch "
                    f"(expected {expected_value!r}, "
                    f"found {actual_value!r})"
                )

        asin = expected["verified_asin"]
        canonical_url = expected[
            "verified_amazon_url"
        ]

        derived_expected = {
            "amazon_asin": asin,
            "amazon_url": canonical_url,
            **DERIVED_PRODUCT_FIELDS,
        }

        for field_name, expected_value in (
            derived_expected.items()
        ):
            actual_value = normalize_value(
                product.get(field_name)
            )

            if actual_value != expected_value:
                errors.append(
                    f"{product_id}: {field_name} mismatch "
                    f"(expected {expected_value!r}, "
                    f"found {actual_value!r})"
                )

        verified_ids.append(product_id)

    for product in products:
        product_id = str(
            product.get("id", "")
        ).strip()

        product_claims_lock = (
            product.get("identity_locked") is True
        )

        if (
            product_claims_lock
            and product_id not in locked_registry_ids
        ):
            registry_record = registry_by_id.get(product_id)

            if registry_record is None:
                reason = (
                    "no matching registry record exists"
                )
            elif (
                registry_record.get("identity_locked")
                is not True
            ):
                reason = (
                    "registry record is not locked"
                )
            else:
                reason = (
                    "registry lock was not accepted"
                )

            errors.append(
                f"{product_id}: product claims a locked "
                f"identity but {reason}"
            )

    if errors:
        raise IdentityGuardError(
            "\n".join(errors)
        )

    return verified_ids


def main() -> int:
    print("=" * 78)
    print("AMAZON LOCKED IDENTITY GUARD")
    print("=" * 78)

    try:
        products_payload = load_json(PRODUCTS_PATH)
        registry_payload = load_json(REGISTRY_PATH)

        verified_ids = guard_locked_identities(
            products_payload,
            registry_payload,
        )
    except (
        ApplyLockedIdentityError,
        IdentityGuardError,
    ) as exc:
        print("Result : BLOCKED")

        for line in str(exc).splitlines():
            print(f"  - {line}")

        print("Pipeline must not continue.")
        return 1

    for product_id in verified_ids:
        print(f"[PASS] {product_id}")

    print("-" * 78)
    print(
        f"Locked identities verified: "
        f"{len(verified_ids)}"
    )
    print("Result : IDENTITY GUARD PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
