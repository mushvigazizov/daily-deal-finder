import json
from pathlib import Path

from core.i18n.config import (
    CONTENT_DIRECTORY,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


CONTENT_PATH = Path(CONTENT_DIRECTORY)


def normalize_language(language):
    if language in SUPPORTED_LANGUAGES:
        return language

    return DEFAULT_LANGUAGE


def content_file_path(product_id, language):
    language = normalize_language(language)
    return CONTENT_PATH / f"{product_id}.{language}.json"


def available_languages(product_id):
    languages = []

    for language in SUPPORTED_LANGUAGES:
        if content_file_path(product_id, language).exists():
            languages.append(language)

    return languages


def resolve_content_file(product_id, language):
    requested_language = normalize_language(language)

    candidates = [
        requested_language,
        DEFAULT_LANGUAGE,
        "de",
        "en",
        "ru",
    ]

    checked = set()

    for candidate in candidates:
        if candidate in checked:
            continue

        checked.add(candidate)
        path = content_file_path(product_id, candidate)

        if path.exists():
            return path, candidate

    raise FileNotFoundError(
        f"No multilingual content found for product: {product_id}"
    )


def load_product_content(product_id, language=DEFAULT_LANGUAGE):
    path, resolved_language = resolve_content_file(
        product_id,
        language,
    )

    data = json.loads(path.read_text(encoding="utf-8"))

    return {
        "product_id": product_id,
        "requested_language": normalize_language(language),
        "resolved_language": resolved_language,
        "source_file": str(path),
        "content": data,
    }
