import json
from pathlib import Path
from datetime import date

products_path = Path("data/products.json")
output_path = Path("data/pinterest_content.json")

data = json.loads(products_path.read_text(encoding="utf-8"))
products = data.get("products", data)

pins = []

print("=" * 70)
print("PINTEREST CONTENT GENERATOR")
print("=" * 70)

for product in products:
    if not product.get("active", True):
        continue

    pin = {
        "product_id": product.get("id"),
        "title": product.get("pinterest_title") or product.get("title"),
        "description": product.get("pinterest_description") or product.get("seo_description"),
        "image": product.get("image"),
        "target_url": f"/product.html?id={product.get('id')}",
        "board": "Camping & Outdoor Gear",
        "status": "ready",
        "created_at": str(date.today())
    }

    pins.append(pin)

output = {
    "_schema": "1.0",
    "_generated_at": str(date.today()),
    "platform": "pinterest",
    "total_pins": len(pins),
    "pins": pins
}

output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Pinterest pins generated: {len(pins)}")
print(f"Output: {output_path}")
print("PINTEREST CONTENT GENERATION COMPLETED")
