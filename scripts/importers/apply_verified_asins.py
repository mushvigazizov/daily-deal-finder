import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

PRODUCTS_PATH = Path("data/products.json")
TEMPLATE_PATH = Path("scripts/importers/asin_import_template.json")
BACKUP_DIR = Path("backups/products")

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$", re.IGNORECASE)

URL_PATTERNS = [
    re.compile(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_asin_from_url(url):
    url = url.strip()

    if not url:
        return ""

    for pattern in URL_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1).upper()

    return ""


def normalize_asin(value):
    value = value.strip().upper()

    if ASIN_PATTERN.fullmatch(value):
        return value

    return ""


def is_amazon_de_url(url):
    if not url:
        return False

    try:
        hostname = urlparse(url).hostname or ""
    except ValueError:
        return False

    hostname = hostname.lower()

    return (
        hostname == "amazon.de"
        or hostname.endswith(".amazon.de")
        or hostname == "amzn.eu"
        or hostname.endswith(".amzn.eu")
    )


def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"products-{timestamp}.json"

    shutil.copy2(PRODUCTS_PATH, backup_path)
    return backup_path


def main():
    if not PRODUCTS_PATH.exists():
        print(f"ERROR: Products file not found: {PRODUCTS_PATH}")
        return 1

    if not TEMPLATE_PATH.exists():
        print(f"ERROR: ASIN template not found: {TEMPLATE_PATH}")
        return 1

    products_data = load_json(PRODUCTS_PATH)
    template_data = load_json(TEMPLATE_PATH)

    products = products_data.get("products", products_data)

    if not isinstance(products, list):
        print("ERROR: Products data must contain a list.")
        return 1

    if not isinstance(template_data, list):
        print("ERROR: ASIN template must contain a list.")
        return 1

    products_by_id = {
        product.get("id"): product
        for product in products
        if product.get("id")
    }

    changed = 0
    skipped = 0
    errors = 0
    seen_asins = {}

    prepared_updates = []

    print("=" * 70)
    print("APPLY VERIFIED AMAZON ASINS")
    print("=" * 70)

    for item in template_data:
        product_id = str(item.get("id", "")).strip()
        manual_asin = str(item.get("verified_asin", "")).strip()
        verified_url = str(item.get("verified_amazon_url", "")).strip()

        if not product_id:
            print("ERROR: Template entry without product id")
            errors += 1
            continue

        product = products_by_id.get(product_id)

        if not product:
            print(f"ERROR: Product not found: {product_id}")
            errors += 1
            continue

        asin = normalize_asin(manual_asin)

        if not asin and verified_url:
            asin = extract_asin_from_url(verified_url)

        if not asin:
            print(f"SKIP : {product_id} - no valid ASIN")
            skipped += 1
            continue

        if verified_url and not is_amazon_de_url(verified_url):
            print(f"ERROR: {product_id} - URL is not an Amazon.de URL")
            errors += 1
            continue

        if asin in seen_asins and seen_asins[asin] != product_id:
            print(
                f"ERROR: Duplicate ASIN {asin}: "
                f"{seen_asins[asin]} and {product_id}"
            )
            errors += 1
            continue

        seen_asins[asin] = product_id

        canonical_url = f"https://www.amazon.de/dp/{asin}"

        prepared_updates.append(
            {
                "product": product,
                "template_item": item,
                "product_id": product_id,
                "asin": asin,
                "canonical_url": canonical_url,
            }
        )

    if errors:
        print("-" * 70)
        print(f"Updates prepared : {len(prepared_updates)}")
        print(f"Skipped          : {skipped}")
        print(f"Errors           : {errors}")
        print("No files changed because errors were found.")
        return 1

    if not prepared_updates:
        print("-" * 70)
        print("No verified ASIN data found.")
        print("Products file was not changed.")
        return 0

    backup_path = create_backup()

    for update in prepared_updates:
        product = update["product"]
        template_item = update["template_item"]
        asin = update["asin"]
        canonical_url = update["canonical_url"]

        product["amazon_asin"] = asin
        product["amazon_link_type"] = "product"
        product["verified_amazon_url"] = canonical_url
        product["amazon_url"] = canonical_url
        product["asin_verified"] = True
        product["asin_verified_at"] = datetime.now().isoformat(
            timespec="seconds"
        )

        template_item["verified_asin"] = asin
        template_item["verified_amazon_url"] = canonical_url
        template_item["status"] = "verified"
        template_item["notes"] = "ASIN validated and applied automatically."

        changed += 1
        print(f"APPLY: {update['product_id']} -> {asin}")

    save_json(PRODUCTS_PATH, products_data)
    save_json(TEMPLATE_PATH, template_data)

    print("-" * 70)
    print(f"Updated products : {changed}")
    print(f"Skipped          : {skipped}")
    print(f"Errors           : {errors}")
    print(f"Backup           : {backup_path}")
    print("ASIN IMPORT COMPLETED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
