from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping


ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

REQUIRED_VERIFIED_FIELDS = (
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
)


@dataclass(frozen=True)
class IdentityAuditResult:
    product_id: str
    status: str
    issues: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_verified(self) -> bool:
        return self.status == "verified"

    @property
    def needs_review(self) -> bool:
        return self.status == "review"

    @property
    def needs_search(self) -> bool:
        return self.status == "search"


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def is_valid_asin(value: Any) -> bool:
    asin = clean_text(value).upper()
    return bool(ASIN_PATTERN.fullmatch(asin))


def audit_product_identity(
    product: Mapping[str, Any],
) -> IdentityAuditResult:
    product_id = clean_text(product.get("id")) or "<missing-id>"
    link_type = clean_text(product.get("amazon_link_type")).lower()
    asin = clean_text(product.get("amazon_asin")).upper()

    has_product_link = link_type == "product"
    asin_verified = product.get("asin_verified") is True

    # Products still using Amazon search links are not identity candidates yet.
    if not has_product_link:
        return IdentityAuditResult(
            product_id=product_id,
            status="search",
            issues=("Real Amazon product not selected yet",),
        )

    issues: list[str] = []

    if not is_valid_asin(asin):
        issues.append("amazon_asin must be a valid 10-character ASIN")

    expected_url = f"https://www.amazon.de/dp/{asin}" if is_valid_asin(asin) else ""
    verified_url = clean_text(product.get("verified_amazon_url"))

    if not verified_url:
        issues.append("missing verified_amazon_url")
    elif expected_url and verified_url.rstrip("/") != expected_url:
        issues.append(
            "verified_amazon_url does not match amazon_asin"
        )

    if not asin_verified:
        issues.append("asin_verified must be true")

    for field_name in REQUIRED_VERIFIED_FIELDS:
        if not clean_text(product.get(field_name)):
            issues.append(f"missing {field_name}")

    verification_status = clean_text(
        product.get("verification_status")
    ).lower()

    if verification_status != "verified":
        issues.append("verification_status must be verified")

    if issues:
        return IdentityAuditResult(
            product_id=product_id,
            status="review",
            issues=tuple(issues),
        )

    return IdentityAuditResult(
        product_id=product_id,
        status="verified",
    )
