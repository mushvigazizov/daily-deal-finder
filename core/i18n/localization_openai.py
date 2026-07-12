import json
import os
from pathlib import Path

from core.ai.config import OPENAI_TEXT_MODEL
from core.i18n.german_content_builder import (
    normalize_text,
    truncate_text,
)
from core.i18n.language_guard import validate_language_content
LOCALIZATION_TEMPERATURE = 0.2


from core.i18n.localization_prompt_builder import (
    LANGUAGE_PROFILES,
    OUTPUT_FIELDS,
    build_localization_prompt,
)


LOCALIZED_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
        },
        "language": {
            "type": "string",
            "enum": ["en", "ru"],
        },
        "seo_title": {
            "type": "string",
        },
        "meta_description": {
            "type": "string",
        },
        "alt_text": {
            "type": "string",
        },
        "pinterest_title": {
            "type": "string",
        },
        "pinterest_description": {
            "type": "string",
        },
        "hashtags": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 1,
            "maxItems": 5,
        },
        "source": {
            "type": "string",
            "enum": ["localized_from_de_v1"],
        },
    },
    "required": OUTPUT_FIELDS,
    "additionalProperties": False,
}


FIELD_LIMITS = {
    "seo_title": 70,
    "meta_description": 160,
    "alt_text": 160,
    "pinterest_title": 100,
    "pinterest_description": 500,
}


def get_api_key():
    key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_IMAGE_API_KEY")
    )

    if key:
        return key.strip()

    env_path = Path(__file__).resolve().parents[2] / ".env"

    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)

        if name.strip() in {
            "OPENAI_API_KEY",
            "OPENAI_IMAGE_API_KEY",
        }:
            value = value.strip().strip('"').strip("'")

            if value:
                return value

    return None


def normalize_localized_content(content):
    if not isinstance(content, dict):
        return content

    normalized = dict(content)

    for field, max_length in FIELD_LIMITS.items():
        value = normalized.get(field)

        if isinstance(value, str):
            normalized[field] = truncate_text(
                value,
                max_length,
            )

    if normalized.get("language") == "ru":
        pinterest_description = normalized.get(
            "pinterest_description"
        )

        if isinstance(pinterest_description, str):
            russian_replacements = {
                "Сохрани этот находку": "Сохрани эту находку",
                "Сохраните этот находку": "Сохраните эту находку",
                "Сохрани этот совет": "Сохрани эту идею",
                "Запомните этот вариант": "Сохраните эту идею",
                "Запомни этот вариант": "Сохрани эту идею",
            }

            for incorrect, corrected in russian_replacements.items():
                pinterest_description = (
                    pinterest_description.replace(
                        incorrect,
                        corrected,
                    )
                )

            normalized["pinterest_description"] = (
                pinterest_description
            )

    hashtags = normalized.get("hashtags")

    if isinstance(hashtags, list):
        cleaned = []

        for hashtag in hashtags:
            if not isinstance(hashtag, str):
                cleaned.append(hashtag)
                continue

            value = normalize_text(hashtag)

            if not value:
                continue

            if value not in cleaned:
                cleaned.append(value)

        normalized["hashtags"] = cleaned[:5]

    return normalized


def validate_localized_content(
    content,
    product_id,
    target_language,
):
    errors = []

    if not isinstance(content, dict):
        return ["Localized response must be a JSON object"]

    missing_fields = [
        field
        for field in OUTPUT_FIELDS
        if field not in content
    ]

    if missing_fields:
        errors.append(
            "Missing fields: " + ", ".join(missing_fields)
        )

    extra_fields = sorted(
        set(content) - set(OUTPUT_FIELDS)
    )

    if extra_fields:
        errors.append(
            "Unexpected fields: " + ", ".join(extra_fields)
        )

    if content.get("id") != product_id:
        errors.append(
            f"Invalid id: expected {product_id!r}, "
            f"received {content.get('id')!r}"
        )

    if content.get("language") != target_language:
        errors.append(
            f"Invalid language: expected {target_language!r}, "
            f"received {content.get('language')!r}"
        )

    if content.get("source") != "localized_from_de_v1":
        errors.append(
            "Invalid source value"
        )

    for field, max_length in FIELD_LIMITS.items():
        value = content.get(field)

        if not isinstance(value, str):
            errors.append(
                f"{field} must be a string"
            )
            continue

        if not value.strip():
            errors.append(
                f"{field} must not be empty"
            )

        if len(value) > max_length:
            errors.append(
                f"{field} exceeds {max_length} characters: "
                f"{len(value)}"
            )

    hashtags = content.get("hashtags")

    if not isinstance(hashtags, list):
        errors.append("hashtags must be a list")
    else:
        if not 1 <= len(hashtags) <= 5:
            errors.append(
                "hashtags must contain between 1 and 5 items"
            )

        for index, hashtag in enumerate(hashtags):
            if not isinstance(hashtag, str):
                errors.append(
                    f"hashtags[{index}] must be a string"
                )
                continue

            if not hashtag.startswith("#"):
                errors.append(
                    f"hashtags[{index}] must start with #"
                )

    if target_language in LANGUAGE_PROFILES:
        errors.extend(
            validate_language_content(
                content,
                target_language,
            )
        )

    return errors


def generate_localized_content(
    master_content,
    target_language,
):
    if target_language not in LANGUAGE_PROFILES:
        supported = ", ".join(
            sorted(LANGUAGE_PROFILES)
        )
        raise ValueError(
            f"Unsupported target language: "
            f"{target_language}. "
            f"Supported languages: {supported}"
        )

    product_id = str(
        master_content.get("id") or ""
    ).strip()

    if not product_id:
        raise ValueError(
            "Master content must contain a product id"
        )

    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY or OPENAI_IMAGE_API_KEY "
            "was not found"
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The openai Python package is not installed"
        ) from exc

    client = OpenAI(api_key=api_key)
    prompt = build_localization_prompt(
        master_content,
        target_language,
    )

    response = client.chat.completions.create(
        model=OPENAI_TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise ecommerce localization "
                    "editor. Return only valid JSON matching "
                    "the supplied schema."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": (
                    f"localized_product_content_"
                    f"{target_language}"
                ),
                "schema": LOCALIZED_CONTENT_SCHEMA,
                "strict": True,
            },
        },
        temperature=LOCALIZATION_TEMPERATURE,
    )

    text = response.choices[0].message.content

    if not text:
        raise RuntimeError(
            "OpenAI returned an empty localization response"
        )

    try:
        content = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OpenAI returned invalid JSON"
        ) from exc

    content = normalize_localized_content(content)

    errors = validate_localized_content(
        content,
        product_id,
        target_language,
    )

    if errors:
        details = "\n".join(
            f"- {error}"
            for error in errors
        )
        raise ValueError(
            f"Localization validation failed for "
            f"{product_id}.{target_language}:\n"
            f"{details}"
        )

    return content
