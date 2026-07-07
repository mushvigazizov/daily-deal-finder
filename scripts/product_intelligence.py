import json
import re
from pathlib import Path

PRODUCTS_PATH = Path("data/products.json")

def text_blob(product):
    parts = [
        product.get("title", ""),
        product.get("brand", ""),
        product.get("category", ""),
        product.get("subcategory", ""),
        product.get("short_description", ""),
        product.get("long_description", ""),
        " ".join(product.get("features") or []),
    ]
    return " ".join(parts).lower()

def infer_capacity(text):
    m = re.search(r"(\d+)[-\s]?(personen|person|persons)", text)
    if m:
        return f"{m.group(1)} persons"
    if "65l" in text or "65 l" in text:
        return "65 liters"
    if "24l" in text or "24 l" in text:
        return "24 liters"
    return "not specified"

def infer_product_type(product, text):
    sub = product.get("subcategory", "").lower()

    if "pop-up" in text or "2-sekunden" in text:
        return "pop-up camping tent"
    if "zelt" in text or sub == "zelte":
        return "camping tent"
    if "schlafsack" in text or sub == "schlafsacke":
        return "sleeping bag"
    if "stirnlampe" in text:
        return "headlamp"
    if "lampe" in text or sub == "lampen":
        return "camping light"
    if "rucksack" in text or sub == "rucksacke":
        return "hiking backpack"
    if "stuhl" in text:
        return "camping chair"
    if "tisch" in text:
        return "camping table"
    if "kocher" in text:
        return "camping stove"
    if "kochset" in text:
        return "camping cookware set"
    if "kühlbox" in text:
        return "portable electric cooler"
    if "erste-hilfe" in text or "first aid" in text:
        return "outdoor first aid kit"
    if "wasserfilter" in text:
        return "portable water filter"
    if "regenjacke" in text:
        return "waterproof rain jacket"
    if "thermo" in text or "funktionsunterwäsche" in text:
        return "thermal base layer clothing"
    if "multitool" in text:
        return "outdoor multitool"
    if "paracord" in text:
        return "survival paracord"

    return "outdoor product"

def infer_target_user(text):
    if "familie" in text or "4-personen" in text or "4 personen" in text:
        return "families and group campers"
    if "festival" in text:
        return "festival campers and casual weekend users"
    if "ultraleicht" in text or "trekking" in text or "rucksack" in text:
        return "hikers and lightweight backpackers"
    if "2-personen" in text or "2 personen" in text:
        return "couples and weekend campers"
    if "outdoor" in text:
        return "outdoor and camping users"
    return "general outdoor users"

def infer_primary_benefit(text):
    if "2-sekunden" in text or "selbstaufbau" in text:
        return "fast setup"
    if "ultraleicht" in text or "leicht" in text:
        return "lightweight portability"
    if "wasserdicht" in text or "wasserfest" in text:
        return "weather protection"
    if "65l" in text:
        return "large storage capacity"
    if "komfort" in text or "bequem" in text:
        return "comfort"
    if "kompakt" in text:
        return "compact transport"
    if "4000l" in text:
        return "long-lasting water filtration"
    return "practical outdoor usefulness"

def infer_scene(product_type, text):
    if "festival" in text:
        return "summer festival campsite"
    if "rucksack" in text or "trekking" in text:
        return "mountain or forest hiking trail"
    if "schlafsack" in text:
        return "cozy tent interior at a campsite"
    if "kocher" in text or "kochset" in text or "kühlbox" in text:
        return "outdoor camping kitchen setup"
    if "stuhl" in text or "tisch" in text:
        return "relaxed campsite seating area"
    if "wasserfilter" in text:
        return "clear mountain stream hiking scene"
    if "regenjacke" in text or "thermo" in text:
        return "hiking trail in cool outdoor weather"
    if "zelt" in text or "tent" in product_type:
        return "realistic forest campsite near a lake"
    return "realistic outdoor camping environment"

def extract_keywords(product):
    words = []
    for item in product.get("features") or []:
        words.extend([w.strip(" ,.;:-").lower() for w in item.split()])
    base = [w for w in words if len(w) > 3]
    unique = []
    for w in base:
        if w not in unique:
            unique.append(w)
    return unique[:10]

def analyze_product(product):
    text = text_blob(product)
    product_type = infer_product_type(product, text)
    primary_benefit = infer_primary_benefit(text)

    return {
        "id": product.get("id"),
        "title": product.get("title"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "subcategory": product.get("subcategory"),
        "product_type": product_type,
        "capacity": infer_capacity(text),
        "target_user": infer_target_user(text),
        "experience_level": "beginner to intermediate",
        "primary_benefit": primary_benefit,
        "secondary_benefits": product.get("features") or [],
        "recommended_scene": infer_scene(product_type, text),
        "camera_angle": "eye level",
        "lighting": "natural golden hour light",
        "composition": "product clearly visible in the foreground with realistic outdoor context",
        "visual_priority": f"highlight {primary_benefit} while keeping the product realistic",
        "must_show": [
            product_type,
            "realistic proportions",
            "practical outdoor use",
            "clear product focus"
        ],
        "must_avoid": [
            "brand logos",
            "text overlays",
            "watermarks",
            "price tags",
            "misleading size or capacity",
            "copying Amazon product photos",
            "unrealistic materials or impossible features"
        ],
        "seo_keywords": extract_keywords(product),
        "pinterest_keywords": extract_keywords(product)[:6],
    }

def main():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    for product in data["products"][:3]:
        print(json.dumps(analyze_product(product), ensure_ascii=False, indent=2))
        print("-" * 60)

if __name__ == "__main__":
    main()
