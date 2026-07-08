import json
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

errors = 0

print("=" * 70)
print("PRODUCT QUALITY VALIDATOR")
print("=" * 70)

for product in products:
    missing = []

    for field in required_fields:
        value = product.get(field)
        if value is None or str(value).strip() == "":
            missing.append(field)

    if missing:
        errors += 1
        print(f"[ERROR] {product.get('id')} ({product.get('title')})")
        print(" Missing:", ", ".join(missing))
    else:
        print(f"[ OK ] {product.get('id')}")

print()
print(f"Products checked : {len(products)}")
print(f"Products with issues : {errors}")

if errors == 0:
    print("QUALITY CHECK PASSED")
else:
    print("QUALITY CHECK FAILED")
