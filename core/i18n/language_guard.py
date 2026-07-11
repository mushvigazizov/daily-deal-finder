import re
from typing import Iterable


LANGUAGE_RULES = {
    "de": {
        "forbidden_phrases": [
            "weather protection",
            "realistic outdoor use",
            "couples and weekend campers",
            "families and group campers",
            "general outdoor users",
            "practical outdoor usefulness",
            "lightweight portability",
            "fast setup",
            "compact transport",
            "camping tent",
            "sleeping bag",
            "outdoor product",
        ],
        "foreign_word_patterns": [
            r"\bideal for\b",
            r"\bperfect for\b",
            r"\bdesigned for\b",
            r"\brecommended for\b",
        ],
    },
    "en": {
        "forbidden_phrases": [
            "entdecke",
            "ideal für",
            "mit fokus auf",
            "perfekt für",
            "wasserdicht",
            "schnellaufbau",
            "wetterschutz",
            "paare und",
            "für camping",
        ],
        "foreign_word_patterns": [
            r"\bgeeignet für\b",
            r"\bmit fokus\b",
            r"\bfür outdoor\b",
        ],
    },
    "ru": {
        "forbidden_phrases": [
            "entdecke",
            "ideal für",
            "mit fokus auf",
            "perfekt für",
            "weather protection",
            "realistic outdoor use",
            "couples and weekend campers",
            "camping und outdoor",
        ],
        "foreign_word_patterns": [
            r"\bideal for\b",
            r"\bperfect for\b",
            r"\bgeeignet für\b",
        ],
    },
}


def collect_text(value) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return

    if isinstance(value, list):
        for item in value:
            yield from collect_text(item)
        return

    if isinstance(value, dict):
        for item in value.values():
            yield from collect_text(item)


def validate_language_content(content: dict, language: str) -> list[str]:
    if language not in LANGUAGE_RULES:
        return [f"Unsupported language: {language}"]

    rules = LANGUAGE_RULES[language]
    full_text = " ".join(collect_text(content)).lower()
    errors = []

    for phrase in rules["forbidden_phrases"]:
        if phrase.lower() in full_text:
            errors.append(
                f"Foreign or mixed-language phrase detected: {phrase!r}"
            )

    for pattern in rules["foreign_word_patterns"]:
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            errors.append(
                f"Foreign language pattern detected: {pattern!r}"
            )

    return errors


def assert_language_content(content: dict, language: str) -> None:
    errors = validate_language_content(content, language)

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(
            f"Language validation failed for {language}:\n{details}"
        )
