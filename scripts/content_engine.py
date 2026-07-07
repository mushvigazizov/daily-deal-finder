import json
from pathlib import Path

from scripts.product_intelligence import analyze_product

PRODUCTS_PATH = Path("data/products.json")
CONTENT_DIR = Path("data/content")

def build_content(product: dict) -> dict:
    intel = analyze_product(product)

    title = product.get("title", "")
    brand = product.get("brand", "")
    product_type = intel.get("product_type", "outdoor product")
    benefit = intel.get("primary_benefit", "practical outdoor use")
    keywords = intel.get("seo_keywords", [])[:6]

    seo_title = f"{brand} {product_type} – {benefit}".strip()
    meta_description = (
        f"Entdecke {title}: ideal für {intel.get('target_user')}, "
        f"mit Fokus auf {benefit}. Perfekt für Camping und Outdoor-Abenteuer."
    )

    return {
        "id": product.get("id"),
        "seo_title": seo_title[:70],
        "meta_description": meta_description[:160],
        "alt_text": f"{title} in realistic outdoor use",
        "pinterest_title": f"{product_type.title()} für Camping & Outdoor",
        "pinterest_description": meta_description,
        "hashtags": [f"#{k.replace('-', '')}" for k in keywords[:5]],
        "source": "content_engine_v1"
    }

def main():
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    count = 0

    for product in data["products"]:
        pid = product.get("id")
        if not pid:
            continue

        content = build_content(product)
        out = CONTENT_DIR / f"{pid}.de.json"
        out.write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        count += 1
        print(f"WROTE {out}")

    print(f"DONE content_files={count}")

if __name__ == "__main__":
    main()
