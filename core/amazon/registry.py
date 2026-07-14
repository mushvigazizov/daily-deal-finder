from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from core.amazon.config import REGISTRY_PATH


class RegistryError(ValueError):
    """Raised when the Amazon identity registry is invalid."""


def load_registry(
    path: Path = REGISTRY_PATH,
) -> list[dict[str, Any]]:
    """Load and validate the Amazon identity registry."""

    if not path.exists():
        raise RegistryError(f"registry not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryError(
            f"invalid JSON in registry {path}: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise RegistryError("registry must contain a JSON list")

    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise RegistryError(
                f"registry record at index {index} must be an object"
            )

    validate_registry_uniqueness(payload)
    return payload


def write_registry_atomic(
    registry: list[dict[str, Any]],
    path: Path = REGISTRY_PATH,
) -> None:
    """Validate and atomically write the Amazon identity registry."""

    validate_registry_uniqueness(registry)

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary_path.write_text(
            json.dumps(
                registry,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def index_registry(
    registry: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return registry records indexed by product ID."""

    result: dict[str, dict[str, Any]] = {}

    for index, record in enumerate(registry):
        product_id = record.get("id")

        if not isinstance(product_id, str) or not product_id.strip():
            raise RegistryError(
                f"registry record at index {index} has no valid id"
            )

        product_id = product_id.strip()

        if product_id in result:
            raise RegistryError(
                f"duplicate registry product id: {product_id}"
            )

        result[product_id] = record

    return result


def validate_registry_uniqueness(
    registry: Iterable[dict[str, Any]],
) -> None:
    """Reject duplicate product IDs and duplicate locked ASINs."""

    records = list(registry)
    index_registry(records)

    locked_asins: dict[str, str] = {}

    for record in records:
        if record.get("identity_locked") is not True:
            continue

        product_id = str(record.get("id", "")).strip()
        asin = str(record.get("verified_asin", "")).strip().upper()

        if not asin:
            raise RegistryError(
                f"locked registry record has no verified ASIN: {product_id}"
            )

        previous_product_id = locked_asins.get(asin)

        if previous_product_id is not None:
            raise RegistryError(
                "duplicate locked ASIN "
                f"{asin}: {previous_product_id}, {product_id}"
            )

        locked_asins[asin] = product_id


def get_registry_record(
    registry: Iterable[dict[str, Any]],
    product_id: str,
) -> dict[str, Any] | None:
    """Return one registry record, or None when it does not exist."""

    normalized_product_id = product_id.strip()

    if not normalized_product_id:
        raise RegistryError("product_id must not be empty")

    return index_registry(registry).get(normalized_product_id)


def locked_registry_records(
    registry: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return all locked records after registry validation."""

    records = list(registry)
    validate_registry_uniqueness(records)

    return [
        record
        for record in records
        if record.get("identity_locked") is True
    ]
