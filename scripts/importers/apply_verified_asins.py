import json
from pathlib import Path

products_path = Path("data/products.json")
template_path = Path("scripts/importers/asin_import_template.json")

products_data = json.loads(products_path.read_text())
products = products_data.get("products", products_data)

updates = json.loads(template_path.read_text())
updates_by_id = {item["id"]: item for item in updates}

changed = 0

for product in products:
    product_id = product.get("id")
    update = updates_by_id.get(product_id)

    if not update:
        continue

    asin = update.get("verified_asin", "").strip()

    if not asin:
        continue

    product["amazon_asin"] = asin
    product["amazon_link_type"] = "product"
    product["verified_amazon_url"] = update.get("verified_amazon_url", "").strip()
    changed += 1

products_path.write_text(json.dumps(products_data, ensure_ascii=False, indent=2))

print(f"Updated products: {changed}")
