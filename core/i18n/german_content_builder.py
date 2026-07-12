import re


DEFAULT_HASHTAGS = [
    "#camping",
    "#outdoor",
]


def normalize_text(value):
    return " ".join(str(value or "").split()).strip()


def normalize_text_list(values):
    if not isinstance(values, list):
        return []

    normalized = []

    for value in values:
        text = normalize_text(value)

        if text and text not in normalized:
            normalized.append(text)

    return normalized


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
    hashtags = re.findall(
        r"#[A-Za-zÄÖÜäöüß0-9_]+",
        text or "",
    )

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
        raise ValueError(
            f"Product title is required: {product_id}"
        )

    short_description = normalize_text(
        product.get("short_description")
        or product.get("seo_description")
        or title
    )

    long_description = normalize_text(
        product.get("long_description")
        or short_description
    )

    features = normalize_text_list(
        product.get("features")
    )

    button_text = normalize_text(
        product.get("button_text")
        or "Auf Amazon ansehen"
    )

    buying_angle = normalize_text(
        product.get("buying_angle")
        or short_description
    )

    seo_title = normalize_text(
        product.get("seo_title")
        or title
    )

    meta_description = normalize_text(
        product.get("seo_description")
        or short_description
        or long_description
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

    hashtags = extract_hashtags(
        pinterest_description
    )

    if not hashtags:
        hashtags = DEFAULT_HASHTAGS.copy()

    return {
        "id": product_id,
        "language": "de",
        "title": title,
        "short_description": short_description,
        "long_description": long_description,
        "features": features,
        "button_text": button_text,
        "buying_angle": buying_angle,
        "seo_title": truncate_text(seo_title, 70),
        "meta_description": truncate_text(
            meta_description,
            160,
        ),
        "alt_text": truncate_text(title, 160),
        "pinterest_title": truncate_text(
            pinterest_title,
            100,
        ),
        "pinterest_description": truncate_text(
            pinterest_description,
            500,
        ),
        "hashtags": hashtags,
        "source": "products_json_de_v2",
    }
