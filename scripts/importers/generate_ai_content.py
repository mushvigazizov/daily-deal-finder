import json
from pathlib import Path
from datetime import date

path = Path("data/products.json")
data = json.loads(path.read_text(encoding="utf-8"))
products = data.get("products", data)

updated = 0
year = date.today().year

print("=" * 70)
print("AI CONTENT GENERATOR")
print("=" * 70)

def clean_title(title):
    return title.replace("—", "-").strip()

def make_buying_angle(product):
    sub = product.get("subcategory", "").lower()
    title = product.get("title", "")

    if "zelt" in sub or "zelt" in title.lower():
        return "Ideal für Camper, die ein zuverlässiges Zelt für Wochenenden, Festivals oder Familienausflüge suchen."
    if "schlaf" in sub or "sleep" in title.lower():
        return "Ideal für alle, die beim Camping bequem und warm schlafen möchten."
    if "lampe" in sub or "licht" in title.lower() or "laterne" in title.lower():
        return "Ideal für bessere Sicht am Abend, im Zelt oder rund um den Campingplatz."
    if "rucksack" in sub:
        return "Ideal für Outdoor-Fans, die Ausrüstung praktisch und bequem transportieren möchten."

    return "Ideal für Outdoor-Fans, die praktische und bewährte Camping-Ausrüstung suchen."

for product in products:
    title = clean_title(product.get("title", "Camping Produkt"))
    brand = product.get("brand", "").strip()
    category = product.get("category", "camping").strip()
    features = product.get("features", [])
    first_feature = features[0] if features else "praktisch für Camping und Outdoor"

    product["seo_title"] = f"{title} Test {year} | Daily Deal Finder"
    product["seo_description"] = (
        f"{title}: {first_feature}. Entdecke Vorteile, Einsatzbereiche und warum dieses Produkt für Camping & Outdoor interessant ist."
    )

    product["pinterest_title"] = f"{title} 🏕️"
    product["pinterest_description"] = (
        f"{title} für Camping und Outdoor. Praktisch, nützlich und ideal für deine nächste Tour. "
        f"#camping #outdoor #campingausrüstung"
    )

    product["buying_angle"] = make_buying_angle(product)
    product["content_status"] = "ai_generated"
    product["updated_at"] = str(date.today())

    updated += 1

path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Products processed: {updated}")
print("AI CONTENT GENERATION COMPLETED")
