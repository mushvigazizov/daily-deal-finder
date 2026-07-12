from core.i18n.config import SUPPORTED_LANGUAGES
from core.i18n.content_loader import available_languages


def missing_languages(product_id):
    existing = set(available_languages(product_id))

    return [
        language
        for language in SUPPORTED_LANGUAGES
        if language not in existing
    ]


if __name__ == "__main__":
    product = "camp-001"

    print("Existing :", available_languages(product))
    print("Missing  :", missing_languages(product))
