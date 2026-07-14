from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CANDIDATES_DIR = Path("data/amazon_candidates")
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


class CandidateValidationError(ValueError):
    """Raised when an Amazon candidate file is invalid."""


def canonical_amazon_url(asin: str) -> str:
    return f"https://www.amazon.de/dp/{asin}"


def extract_url_asin(value: Any) -> str:
    url = str(value or "").strip()

    if not url:
        return ""

    parsed = urlparse(url)

    if parsed.netloc.lower() not in {
        "amazon.de",
        "www.amazon.de",
    }:
        return ""

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    for marker in ("dp", "gp"):
        if marker not in parts:
            continue

        index = parts.index(marker)

        if marker == "dp" and index + 1 < len(parts):
            return parts[index + 1].upper()

        if (
            marker == "gp"
            and index + 2 < len(parts)
            and parts[index + 1] == "product"
        ):
            return parts[index + 2].upper()

    return ""


def validate_candidate(
    candidate: dict[str, Any],
    *,
    index: int,
) -> list[str]:
    prefix = f"candidate #{index}"
    errors: list[str] = []

    asin = str(candidate.get("asin", "")).strip().upper()
    url = str(candidate.get("amazon_url", "")).strip()
    title = str(
        candidate.get("amazon_product_title", "")
    ).strip()
    brand = str(candidate.get("amazon_brand", "")).strip()

    if not ASIN_PATTERN.fullmatch(asin):
        errors.append(
            f"{prefix}: invalid ASIN {asin!r}"
        )

    if not url:
        errors.append(
            f"{prefix}: missing amazon_url"
        )
    else:
        url_asin = extract_url_asin(url)

        if not url_asin:
            errors.append(
                f"{prefix}: amazon_url is not a supported "
                f"Amazon.de product URL"
            )
        elif asin and url_asin != asin:
            errors.append(
                f"{prefix}: URL ASIN {url_asin} does not "
                f"match candidate ASIN {asin}"
            )

    if not title:
        errors.append(
            f"{prefix}: missing amazon_product_title"
        )

    if not brand:
        errors.append(
            f"{prefix}: missing amazon_brand"
        )

    specs = candidate.get("amazon_key_specs", [])

    if specs is not None and not isinstance(specs, list):
        errors.append(
            f"{prefix}: amazon_key_specs must be a list"
        )

    return errors


def validate_candidate_payload(
    payload: Any,
    *,
    expected_product_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise CandidateValidationError(
            "candidate file must contain a JSON object"
        )

    product_id = str(
        payload.get("product_id", "")
    ).strip()

    if product_id != expected_product_id:
        raise CandidateValidationError(
            f"product_id mismatch: expected "
            f"{expected_product_id!r}, found {product_id!r}"
        )

    candidates = payload.get("candidates")

    if not isinstance(candidates, list):
        raise CandidateValidationError(
            "'candidates' must contain a list"
        )

    errors: list[str] = []
    seen_asins: dict[str, int] = {}

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        if not isinstance(candidate, dict):
            errors.append(
                f"candidate #{index}: must be a JSON object"
            )
            continue

        errors.extend(
            validate_candidate(
                candidate,
                index=index,
            )
        )

        asin = str(
            candidate.get("asin", "")
        ).strip().upper()

        if asin:
            previous_index = seen_asins.get(asin)

            if previous_index is not None:
                errors.append(
                    f"candidate #{index}: duplicate ASIN "
                    f"{asin}; already used by candidate "
                    f"#{previous_index}"
                )
            else:
                seen_asins[asin] = index

    if errors:
        raise CandidateValidationError(
            "\n".join(errors)
        )

    return candidates


def validate_candidate_file(
    product_id: str,
) -> list[dict[str, Any]]:
    path = CANDIDATES_DIR / f"{product_id}.json"

    if not path.exists():
        raise CandidateValidationError(
            f"candidate file not found: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise CandidateValidationError(
            f"invalid JSON in {path}: {exc}"
        ) from exc

    return validate_candidate_payload(
        payload,
        expected_product_id=product_id,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate imported Amazon identity candidates "
            "before candidate scoring."
        )
    )
    parser.add_argument(
        "--product-id",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 78)
    print("AMAZON IDENTITY CANDIDATE VALIDATOR")
    print("=" * 78)
    print(f"Product ID : {args.product_id}")

    try:
        candidates = validate_candidate_file(
            args.product_id
        )
    except CandidateValidationError as exc:
        print("Result     : REJECTED")

        for line in str(exc).splitlines():
            print(f"  - {line}")

        return 1

    print(f"Candidates : {len(candidates)}")

    for candidate in candidates:
        print(
            f"[PASS] {candidate['asin']} — "
            f"{candidate['amazon_product_title']}"
        )

    print("Result     : CANDIDATE VALIDATION PASSED")
    print("READ-ONLY MODE: no project files were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
