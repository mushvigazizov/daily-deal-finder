import json
import re
from pathlib import Path

path = Path("data/products.json")
data = json.loads(path.read_text())
products = data.get("products", data)

required_fields = [
    "id",
    "title",
    "category",
    "amazon_asin",
    "amazon_link_type",
    "image",
    "seo_title",
    "seo_description",
    "pinterest_title",
    "pinterest_description",
]

allowed_categories = {
    "camping", "outdoor", "kitchen", "home", "tech", "beauty", "pets", "gifts"
}

asin_pattern = re.compile(r"^[A-Z0-9]{10}$")

errors = 0
warnings = 0

print("=" * 70)
print("PRODUCT QUALITY VALIDATOR")
print("=" * 70)

for product in products:
    pid = product.get("id")
    title = product.get("title")
    missing = []

    for field in required_fields:
        value = product.get(field)
        if value is None or str(value).strip() == "":
            missing.append(field)

    if missing:
        errors += 1
        print(f"[ERROR] {pid} | {title}")
        print(" Missing:", ", ".join(missing))
        continue

    category = product.get("category")
    asin = product.get("amazon_asin", "")
    link_type = product.get("amazon_link_type", "")

    if category not in allowed_categories:
        errors += 1
        print(f"[ERROR] {pid} | invalid category: {category}")

    if link_type == "product" and not asin_pattern.match(asin):
        errors += 1
        print(f"[ERROR] {pid} | product link type but invalid ASIN: {asin}")

    if link_type == "search":
        warnings += 1
        print(f"[WARN]  {pid} | search fallback link still used")

    if link_type not in {"search", "product"}:
        errors += 1
        print(f"[ERROR] {pid} | invalid amazon_link_type: {link_type}")

    if not missing and category in allowed_categories:
        print(f"[ OK ]  {pid}")

print()
print(f"Products checked      : {len(products)}")
print(f"Warnings              : {warnings}")
print(f"Products with errors  : {errors}")

if errors == 0:
    print("QUALITY CHECK PASSED")
else:
    print("QUALITY CHECK FAILED")
