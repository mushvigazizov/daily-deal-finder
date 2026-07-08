import json
from pathlib import Path

path = Path("data/products.json")
data = json.loads(path.read_text())
products = data.get("products", data)

updated = 0

print("=" * 70)
print("AI CONTENT GENERATOR (PLACEHOLDER)")
print("=" * 70)

for product in products:
    title = product.get("title", "").strip()

    if not product.get("seo_title"):
        product["seo_title"] = f"{title} | Daily Deal Finder"

    if not product.get("seo_description"):
        product["seo_description"] = (
            f"Discover the {title}. Read our overview and see why it is worth considering."
        )

    if not product.get("pinterest_title"):
        product["pinterest_title"] = title

    if not product.get("pinterest_description"):
        product["pinterest_description"] = (
            f"Explore {title} and discover why outdoor enthusiasts recommend it."
        )

    updated += 1

path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

print(f"Products processed: {updated}")
print("AI CONTENT GENERATION COMPLETED")
