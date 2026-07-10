import json
import shutil
from datetime import date, datetime
from pathlib import Path

PRODUCTS_PATH = Path("data/products.json")
BACKUP_DIR = Path("backups/products")


def load_products():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products = data.get("products", data)

    if not isinstance(products, list):
        raise ValueError("Products data must be a list.")

    return data, products


def save_products(data):
    PRODUCTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"products-refresh-{timestamp}.json"

    shutil.copy2(PRODUCTS_PATH, backup_path)
    return backup_path


def clean(value):
    return " ".join(str(value or "").split()).strip()


def build_derived_content(product):
    title = clean(product.get("title"))
    brand = clean(product.get("brand"))
    category = clean(product.get("category"))
    subcategory = clean(product.get("subcategory"))
    features = [
        clean(item)
        for item in product.get("features", [])
        if clean(item)
    ]

    feature_text = ", ".join(features[:3])
    year = date.today().year

    seo_title = (
        f"{title} Test {year} | Camping & Outdoor Empfehlung"
    )

    seo_description = (
        f"{title} von {brand} im Überblick: {feature_text}. "
        f"Eine praktische Empfehlung für Camping und Outdoor."
    )

    if len(seo_description) > 160:
        shortened = seo_description[:157]
        shortened = shortened.rsplit(" ", 1)[0]
        seo_description = shortened.rstrip(" ,.-") + "..."

    pinterest_title = f"{title} für Camping 🏕️"

    pinterest_description = (
        f"{title} von {brand}: eine praktische Idee für Camping, "
        f"Outdoor und Wochenendtrips. Merke dir diesen Fund für deine "
        f"nächste Tour. #camping #outdoor #campingausrüstung"
    )

    buying_angle = (
        f"Interessant für Käufer, die bei "
        f"{subcategory or category} besonders auf folgende Eigenschaften "
        f"achten: {feature_text}."
    )

    return {
        "seo_title": seo_title,
        "seo_description": seo_description,
        "pinterest_title": pinterest_title,
        "pinterest_description": pinterest_description,
        "buying_angle": buying_angle,
        "content_status": "verified_product_refreshed",
        "content_engine": "product_refresh_v1",
    }


def refresh_verified_products(product_id=None, dry_run=False):
    data, products = load_products()

    prepared = []

    for product in products:
        current_id = product.get("id")

        if product_id and current_id != product_id:
            continue

        if not product.get("asin_verified"):
            continue

        if product.get("amazon_link_type") != "product":
            continue

        updates = build_derived_content(product)

        changed_fields = {
            key: value
            for key, value in updates.items()
            if product.get(key) != value
        }

        if not changed_fields:
            continue

        prepared.append(
            {
                "product": product,
                "product_id": current_id,
                "updates": updates,
                "changed_fields": changed_fields,
            }
        )

    result = {
        "prepared": len(prepared),
        "updated": 0,
        "backup": None,
        "items": prepared,
        "dry_run": dry_run,
    }

    if dry_run or not prepared:
        return result

    backup_path = create_backup()

    refreshed_at = datetime.now().isoformat(timespec="seconds")
    updated_at = date.today().isoformat()

    for item in prepared:
        item["product"].update(item["updates"])
        item["product"]["content_refreshed_at"] = refreshed_at
        item["product"]["updated_at"] = updated_at
        result["updated"] += 1

    save_products(data)

    result["backup"] = str(backup_path)
    return result
