import json
import re
from pathlib import Path
from typing import Any


PRODUCTS_PATH = Path("data/products.json")
REGISTRY_PATH = Path("scripts/importers/asin_import_template.json")


GENERIC_WORDS = {
    "camping",
    "outdoor",
    "leicht",
    "kompakt",
    "wasserdicht",
    "atmungsaktiv",
    "leistungsstark",
    "ergonomisch",
    "sturmfest",
    "geräumig",
    "warm",
    "ultraleicht",
    "ideal",
    "praktisch",
}


HIGH_RISK_PRODUCT_TYPES = {
    "regenjacke",
    "funktionsunterwäsche",
    "paracord",
    "klappstuhl",
    "laterne",
    "schlafsack",
}


def load_products() -> list[dict[str, Any]]:
    payload = json.loads(
        PRODUCTS_PATH.read_text(encoding="utf-8")
    )

    if isinstance(payload, dict):
        products = payload.get("products", [])
    else:
        products = payload

    if not isinstance(products, list):
        raise SystemExit("ERROR: products.json must contain a product list.")

    return products


def load_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(
        REGISTRY_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(payload, list):
        raise SystemExit("ERROR: identity registry must contain a list.")

    return {
        item.get("id"): item
        for item in payload
        if item.get("id")
    }


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def extract_numeric_signals(
    title: str,
    features: list[str],
) -> list[str]:
    text = " ".join([title, *features])

    patterns = (
        r"\b\d+(?:[.,]\d+)?\s*(?:l|liter)\b",
        r"\b\d+(?:[.,]\d+)?\s*(?:kg|g)\b",
        r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|m)\b",
        r"\b\d+\s*(?:v|w|lumen)\b",
        r"\b\d+\s*personen\b",
        r"\b\d+\s*teilig\b",
        r"\b\d+\s*funktionen\b",
        r"\bdin\s*\d+\b",
    )

    found: list[str] = []

    for pattern in patterns:
        found.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    return sorted(set(item.lower() for item in found))


def classify_product(
    product: dict[str, Any],
    registry_item: dict[str, Any],
) -> dict[str, Any]:
    product_id = product.get("id", "")
    title = normalize(product.get("title"))
    brand = normalize(product.get("brand"))
    features = [
        normalize(item)
        for item in product.get("features") or []
        if normalize(item)
    ]

    if (
        product.get("identity_locked") is True
        and product.get("asin_verified") is True
    ):
        return {
            "id": product_id,
            "group": "VERIFIED",
            "score": 100,
            "reasons": ["identity already verified and locked"],
        }

    score = 0
    reasons: list[str] = []

    if brand:
        score += 20
        reasons.append("brand is present")
    else:
        score -= 30
        reasons.append("brand is missing")

    numeric_signals = extract_numeric_signals(title, features)

    if len(numeric_signals) >= 3:
        score += 30
        reasons.append(
            f"multiple measurable specifications: {', '.join(numeric_signals)}"
        )
    elif len(numeric_signals) == 2:
        score += 20
        reasons.append(
            f"two measurable specifications: {', '.join(numeric_signals)}"
        )
    elif len(numeric_signals) == 1:
        score += 10
        reasons.append(
            f"one measurable specification: {numeric_signals[0]}"
        )
    else:
        score -= 10
        reasons.append("no measurable specification")

    model = normalize(registry_item.get("amazon_model"))

    if model:
        score += 35
        reasons.append("exact model is already present")
    else:
        reasons.append("exact model is not known")

    title_words = {
        word
        for word in re.findall(r"[a-zäöüß0-9-]+", title)
        if len(word) >= 4
    }

    generic_hits = sorted(title_words & GENERIC_WORDS)

    if len(generic_hits) >= 3:
        score -= 20
        reasons.append(
            f"title contains many generic terms: {', '.join(generic_hits)}"
        )
    elif generic_hits:
        score -= 5
        reasons.append(
            f"title contains generic terms: {', '.join(generic_hits)}"
        )

    if any(
        product_type in title
        for product_type in HIGH_RISK_PRODUCT_TYPES
    ):
        score -= 15
        reasons.append(
            "product type commonly has many visually similar variants"
        )

    if product.get("asin_verified") is False:
        score -= 10
        reasons.append("a previous candidate was rejected")

    if score >= 45:
        group = "A"
    elif score >= 15:
        group = "B"
    else:
        group = "C"

    return {
        "id": product_id,
        "group": group,
        "score": score,
        "reasons": reasons,
    }


def main() -> int:
    products = load_products()
    registry = load_registry()

    results = [
        classify_product(
            product,
            registry.get(product.get("id"), {}),
        )
        for product in products
    ]

    order = {
        "VERIFIED": 0,
        "A": 1,
        "B": 2,
        "C": 3,
    }

    results.sort(
        key=lambda item: (
            order.get(item["group"], 99),
            -item["score"],
            item["id"],
        )
    )

    print("=" * 86)
    print("AMAZON PRODUCT IDENTITY RISK CLASSIFICATION")
    print("=" * 86)

    current_group = None

    for result in results:
        if result["group"] != current_group:
            current_group = result["group"]
            print()
            print("-" * 86)
            print(f"GROUP {current_group}")
            print("-" * 86)

        print()
        print(
            f"{result['id']:<10} "
            f"score={result['score']:>4}"
        )

        for reason in result["reasons"]:
            print(f"  - {reason}")

    counts: dict[str, int] = {}

    for result in results:
        counts[result["group"]] = (
            counts.get(result["group"], 0) + 1
        )

    print()
    print("=" * 86)
    print("SUMMARY")
    print("=" * 86)

    for group in ("VERIFIED", "A", "B", "C"):
        print(f"{group:<10}: {counts.get(group, 0)}")

    output_path = Path(
        "reports/amazon_identity_risk_classification.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"Report: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
