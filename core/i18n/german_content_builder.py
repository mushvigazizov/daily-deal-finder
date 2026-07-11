import re


DEFAULT_HASHTAGS = [
    "#camping",
    "#outdoor",
]


def extract_hashtags(text):
    hashtags = re.findall(r"#[A-Za-zÄÖÜäöüß0-9_]+", text or "")

    unique = []
    for hashtag in hashtags:
        normalized = hashtag.lower()

        if normalized not in unique:
            unique.append(normalized)

    return unique[:5]


def build_german_content(product):
    product_id = str(product.get("id") or "").strip()
    title = str(product.get("title") or "").strip()

    if not product_id:
        raise ValueError("Product id is required")

    if not title:
        raise ValueError(f"Product title is required: {product_id}")

    seo_title = str(
        product.get("seo_title")
        or title
    ).strip()

    meta_description = str(
        product.get("seo_description")
        or product.get("short_description")
        or product.get("long_description")
        or title
    ).strip()

    pinterest_title = str(
        product.get("pinterest_title")
        or title
    ).strip()

    pinterest_description = str(
        product.get("pinterest_description")
        or meta_description
    ).strip()

    hashtags = extract_hashtags(pinterest_description)

    if not hashtags:
        hashtags = DEFAULT_HASHTAGS.copy()

    return {
        "id": product_id,
        "language": "de",
        "seo_title": seo_title[:70],
        "meta_description": meta_description[:160],
        "alt_text": title,
        "pinterest_title": pinterest_title[:100],
        "pinterest_description": pinterest_description[:500],
        "hashtags": hashtags,
        "source": "products_json_de_v1",
    }
