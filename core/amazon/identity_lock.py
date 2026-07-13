from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping


ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

IDENTITY_FIELDS = (
    "verified_asin",
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
    "amazon_size",
    "amazon_color",
    "amazon_key_specs",
)

REQUIRED_IDENTITY_FIELDS = (
    "verified_asin",
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
    "amazon_key_specs",
)


@dataclass(frozen=True)
class IdentityLockResult:
    valid: bool
    identity_hash: str = ""
    issues: tuple[str, ...] = field(default_factory=tuple)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return " ".join(value.strip().split())

    return " ".join(str(value).strip().split())


def normalize_asin(value: Any) -> str:
    return clean_text(value).upper()


def normalize_key_specs(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        parts = [value]
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = [value]

    normalized = {
        clean_text(item).lower()
        for item in parts
        if clean_text(item)
    }

    return sorted(normalized)


def canonical_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    asin = normalize_asin(record.get("verified_asin"))

    return {
        "verified_asin": asin,
        "verified_amazon_url": clean_text(
            record.get("verified_amazon_url")
        ).rstrip("/"),
        "amazon_product_title": clean_text(
            record.get("amazon_product_title")
        ),
        "amazon_brand": clean_text(
            record.get("amazon_brand")
        ),
        "amazon_model": clean_text(
            record.get("amazon_model")
        ),
        "amazon_size": clean_text(
            record.get("amazon_size")
        ),
        "amazon_color": clean_text(
            record.get("amazon_color")
        ),
        "amazon_key_specs": normalize_key_specs(
            record.get("amazon_key_specs")
        ),
        "verification_source": clean_text(
            record.get("verification_source")
        ),
        "verification_status": clean_text(
            record.get("verification_status")
        ).lower(),
    }


def compute_identity_hash(record: Mapping[str, Any]) -> str:
    identity = canonical_identity(record)

    hash_payload = {
        key: identity[key]
        for key in (
            "verified_asin",
            "amazon_product_title",
            "amazon_brand",
            "amazon_model",
            "amazon_size",
            "amazon_color",
            "amazon_key_specs",
        )
    }

    serialized = json.dumps(
        hash_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_identity_for_lock(
    record: Mapping[str, Any],
) -> IdentityLockResult:
    identity = canonical_identity(record)
    issues: list[str] = []

    asin = identity["verified_asin"]

    if not ASIN_PATTERN.fullmatch(asin):
        issues.append(
            "verified_asin must be a valid 10-character ASIN"
        )

    expected_url = (
        f"https://www.amazon.de/dp/{asin}"
        if ASIN_PATTERN.fullmatch(asin)
        else ""
    )

    verified_url = identity["verified_amazon_url"]

    if not verified_url:
        issues.append("missing verified_amazon_url")
    elif expected_url and verified_url != expected_url:
        issues.append(
            "verified_amazon_url does not match verified_asin"
        )

    for field_name in REQUIRED_IDENTITY_FIELDS:
        value = identity[field_name]

        if field_name == "amazon_key_specs":
            if not value:
                issues.append("missing amazon_key_specs")
        elif not clean_text(value):
            issues.append(f"missing {field_name}")

    if identity["verification_status"] != "verified":
        issues.append("verification_status must be verified")

    if not identity["verification_source"]:
        issues.append("missing verification_source")

    if issues:
        return IdentityLockResult(
            valid=False,
            issues=tuple(issues),
        )

    return IdentityLockResult(
        valid=True,
        identity_hash=compute_identity_hash(identity),
    )


def verify_existing_lock(
    record: Mapping[str, Any],
) -> IdentityLockResult:
    validation = validate_identity_for_lock(record)

    if not validation.valid:
        return validation

    stored_hash = clean_text(record.get("identity_hash")).lower()

    if not stored_hash:
        return IdentityLockResult(
            valid=False,
            issues=("missing identity_hash",),
        )

    if stored_hash != validation.identity_hash:
        return IdentityLockResult(
            valid=False,
            identity_hash=validation.identity_hash,
            issues=("identity_hash mismatch",),
        )

    if record.get("identity_locked") is not True:
        return IdentityLockResult(
            valid=False,
            identity_hash=validation.identity_hash,
            issues=("identity_locked must be true",),
        )

    return IdentityLockResult(
        valid=True,
        identity_hash=validation.identity_hash,
    )
