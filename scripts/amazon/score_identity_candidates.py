from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PRODUCTS_PATH = Path("data/products.json")
CANDIDATES_DIR = Path("data/amazon_candidates")


def normalize_text(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"[^\wäöüß]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def token_set(value: Any) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if len(token) >= 2
    }


def overlap_score(left: Any, right: Any) -> float:
    """
    Measure how much of the expected product text is covered
    by the candidate text.

    Candidate titles commonly contain extra marketplace words,
    so using Jaccard similarity would unfairly reduce the score.
    """
    expected_tokens = token_set(left)
    candidate_tokens = token_set(right)

    if not expected_tokens or not candidate_tokens:
        return 0.0

    intersection = expected_tokens & candidate_tokens

    return len(intersection) / len(expected_tokens)


def contains_score(needle: Any, haystack: Any) -> float:
    normalized_needle = normalize_text(needle)
    normalized_haystack = normalize_text(haystack)

    if not normalized_needle or not normalized_haystack:
        return 0.0

    return 1.0 if normalized_needle in normalized_haystack else 0.0


def candidate_score(
    product: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    product_title = product.get("title", "")
    product_brand = product.get("brand", "")
    product_features = " ".join(product.get("features") or [])

    candidate_title = candidate.get("amazon_product_title", "")
    candidate_brand = candidate.get("amazon_brand", "")
    candidate_model = candidate.get("amazon_model", "")
    candidate_specs = " ".join(
        candidate.get("amazon_key_specs") or []
    )

    title_score = overlap_score(
        product_title,
        candidate_title,
    )
    brand_score = max(
        overlap_score(product_brand, candidate_brand),
        contains_score(product_brand, candidate_title),
    )
    feature_score = overlap_score(
        product_features,
        f"{candidate_title} {candidate_specs}",
    )

    model_score = 0.0

    if candidate_model:
        model_score = contains_score(
            candidate_model,
            candidate_title,
        )

    weighted_score = (
        title_score * 0.45
        + brand_score * 0.30
        + feature_score * 0.20
        + model_score * 0.05
    )

    confidence = round(weighted_score * 100, 2)

    if confidence >= 90:
        decision = "strong_candidate"
    elif confidence >= 70:
        decision = "manual_review"
    else:
        decision = "weak_candidate"

    return {
        "asin": candidate.get("asin", ""),
        "amazon_url": candidate.get("amazon_url", ""),
        "amazon_product_title": candidate_title,
        "amazon_brand": candidate_brand,
        "amazon_model": candidate_model,
        "amazon_size": candidate.get("amazon_size", ""),
        "amazon_color": candidate.get("amazon_color", ""),
        "amazon_key_specs": candidate.get(
            "amazon_key_specs"
        ) or [],
        "score_breakdown": {
            "title": round(title_score * 100, 2),
            "brand": round(brand_score * 100, 2),
            "features": round(feature_score * 100, 2),
            "model": round(model_score * 100, 2),
        },
        "confidence": confidence,
        "decision": decision,
    }


def load_products() -> list[dict[str, Any]]:
    payload = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )

    products = payload.get("products", payload)

    if not isinstance(products, list):
        raise ValueError(
            "products.json must contain a product list"
        )

    return products


def load_candidates(
    product_id: str,
) -> list[dict[str, Any]]:
    path = CANDIDATES_DIR / f"{product_id}.json"

    if not path.exists():
        raise FileNotFoundError(
            f"candidate file not found: {path}"
        )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    candidates = payload.get("candidates", payload)

    if not isinstance(candidates, list):
        raise ValueError(
            "candidate file must contain a list or "
            "a 'candidates' list"
        )

    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score imported Amazon identity candidates "
            "without modifying project data."
        )
    )
    parser.add_argument(
        "--product-id",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    products = load_products()
    product = next(
        (
            item
            for item in products
            if item.get("id") == args.product_id
        ),
        None,
    )

    if product is None:
        print(
            f"ERROR: unknown product id: "
            f"{args.product_id}"
        )
        return 1

    try:
        candidates = load_candidates(
            args.product_id
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    scored = [
        candidate_score(product, candidate)
        for candidate in candidates
    ]
    scored.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    print("=" * 78)
    print("AMAZON IDENTITY CANDIDATE SCORING")
    print("=" * 78)
    print(f"Product ID : {args.product_id}")
    print(f"Title      : {product.get('title', '')}")
    print(f"Brand      : {product.get('brand', '')}")
    print()

    if not scored:
        print("No candidates found.")
        return 0

    for index, candidate in enumerate(
        scored,
        start=1,
    ):
        print("-" * 78)
        print(f"Rank       : {index}")
        print(f"ASIN       : {candidate['asin']}")
        print(
            f"Confidence : "
            f"{candidate['confidence']:.2f}%"
        )
        print(f"Decision   : {candidate['decision']}")
        print(
            f"Title      : "
            f"{candidate['amazon_product_title']}"
        )
        print(
            f"Brand      : "
            f"{candidate['amazon_brand']}"
        )
        print(
            f"Model      : "
            f"{candidate['amazon_model']}"
        )
        print(
            "Breakdown   : "
            + json.dumps(
                candidate["score_breakdown"],
                ensure_ascii=False,
            )
        )

    print()
    print("READ-ONLY MODE: no project files were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
