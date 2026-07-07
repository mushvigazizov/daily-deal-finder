import hashlib
import json
from pathlib import Path

PRODUCTS_PATH = Path("data/products.json")
STATE_DIR = Path("data/state")

FINGERPRINT_FIELDS = [
    "id",
    "sku",
    "title",
    "brand",
    "category",
    "subcategory",
    "short_description",
    "long_description",
    "features",
    "amazon_asin",
    "active",
]

def stable_product_data(product: dict) -> dict:
    return {key: product.get(key) for key in FINGERPRINT_FIELDS}

def fingerprint_product(product: dict) -> str:
    payload = json.dumps(
        stable_product_data(product),
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    count = 0

    for product in data["products"]:
        pid = product.get("id")
        if not pid:
            continue

        fp = fingerprint_product(product)

        state = {
            "id": pid,
            "fingerprint": fp,
        }

        path = STATE_DIR / f"{pid}.json"
        path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"SAVED {path.name}")
        count += 1

    print(f"DONE state_files={count}")


if __name__ == "__main__":
    main()

