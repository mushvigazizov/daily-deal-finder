import re


DEFAULT_HASHTAGS = [
    "#camping",
    "#outdoor",
]


def normalize_text(value):
    return " ".join(str(value or "").split()).strip()


def truncate_text(value, max_length):
    text = normalize_text(value)

    if len(text) <= max_length:
        return text

    candidate = text[: max_length + 1]
    last_space = candidate.rfind(" ")

    if last_space > 0:
        candidate = candidate[:last_space]
    else:
        candidate = candidate[:max_length]

    return candidate.rstrip(" ,.;:-–—")


def extract_hashtags(text):
    hashtags = re.findall(r"#[A-Za-zÄÖÜäöüß0-9_]+", text or "")

    unique = []
    for hashtag in hashtags:
        normalized = hashtag.lower()

        if normalized not in unique:
            unique.append(normalized)

    return unique[:5]


def build_german_content(product):
    product_id = normalize_text(product.get("id"))
    title = normalize_text(product.get("title"))

    if not product_id:
        raise ValueError("Product id is required")

    if not title:
        raise ValueError(f"Product title is required: {product_id}")

    seo_title = normalize_text(
        product.get("seo_title")
        or title
    )

    meta_description = normalize_text(
        product.get("seo_description")
        or product.get("short_description")
        or product.get("long_description")
        or title
    )

    pinterest_title = normalize_text(
        product.get("pinterest_title")
        or title
    )

    pinterest_description = normalize_text(
        product.get("pinterest_description")
        or meta_description
    )

    hashtags = extract_hashtags(pinterest_description)

    if not hashtags:
        hashtags = DEFAULT_HASHTAGS.copy()

    return {
        "id": product_id,
        "language": "de",
        "seo_title": truncate_text(seo_title, 70),
        "meta_description": truncate_text(meta_description, 160),
        "alt_text": truncate_text(title, 160),
        "pinterest_title": truncate_text(pinterest_title, 100),
        "pinterest_description": truncate_text(pinterest_description, 500),
        "hashtags": hashtags,
        "source": "products_json_de_v1",
    }
