from datetime import date

YEAR = date.today().year

def clean_text(value, fallback=""):
    if value is None:
        return fallback
    return str(value).replace("—", "-").strip() or fallback

def build_product_summary(product):
    title = clean_text(product.get("title"), "Camping Produkt")
    brand = clean_text(product.get("brand"), "")
    category = clean_text(product.get("category"), "Camping")
    subcategory = clean_text(product.get("subcategory"), "Outdoor")
    features = product.get("features", [])

    if not isinstance(features, list):
        features = []

    feature_text = ", ".join(str(f).strip() for f in features[:3] if str(f).strip())
    if not feature_text:
        feature_text = "praktisch für Camping und Outdoor"

    return {
        "title": title,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "features": feature_text,
    }

def generate_local_content(product):
    summary = build_product_summary(product)

    title = summary["title"]
    brand = summary["brand"]
    subcategory = summary["subcategory"]
    features = summary["features"]

    brand_part = f" von {brand}" if brand else ""

    return {
        "seo_title": f"{title} Test {YEAR} | Camping & Outdoor Empfehlung",
        "seo_description": (
            f"{title}{brand_part} im Überblick: {features}. "
            f"Eine praktische Option für alle, die passende Ausrüstung für {subcategory} und Outdoor-Aktivitäten suchen."
        ),
        "pinterest_title": f"{title} für Camping 🏕️",
        "pinterest_description": (
            f"{title}{brand_part}: eine nützliche Idee für Camping, Outdoor und Wochenendtrips. "
            f"Merke dir diesen Fund für deine nächste Tour. #camping #outdoor #campingausrüstung"
        ),
        "buying_angle": (
            f"Besonders interessant für Camper, die bei {subcategory} auf praktische Eigenschaften achten: {features}."
        ),
        "content_status": "ai_engine_generated",
        "content_engine": "local_v1",
        "updated_at": str(date.today()),
    }
