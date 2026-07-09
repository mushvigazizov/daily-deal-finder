REQUIRED_FIELDS = [
    "seo_title",
    "seo_description",
    "pinterest_title",
    "pinterest_description",
    "buying_angle",
]

def validate_ai_content(content):
    if not isinstance(content, dict):
        return None

    cleaned = {}

    for field in REQUIRED_FIELDS:
        value = content.get(field)

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        cleaned[field] = value

    return cleaned
