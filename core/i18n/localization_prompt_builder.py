import json


LANGUAGE_PROFILES = {
    "en": {
        "name": "English",
        "locale": "en-US",
        "audience": "English-speaking shoppers interested in camping and outdoor products",
        "style": (
            "Natural, professional English. Clear and helpful, without exaggerated "
            "sales language or literal German sentence structure."
        ),
    },
    "ru": {
        "name": "Russian",
        "locale": "ru-RU",
        "audience": "Russian-speaking shoppers interested in camping and outdoor products",
        "style": (
            "Natural, professional Russian. Clear and fluent, without German or "
            "English sentence structure and without exaggerated advertising claims."
        ),
    },
}


OUTPUT_FIELDS = [
    "id",
    "language",
    "seo_title",
    "meta_description",
    "alt_text",
    "pinterest_title",
    "pinterest_description",
    "hashtags",
    "source",
]


def build_localization_prompt(master_content: dict, target_language: str) -> str:
    profile = LANGUAGE_PROFILES.get(target_language)

    if not profile:
        supported = ", ".join(sorted(LANGUAGE_PROFILES))
        raise ValueError(
            f"Unsupported target language: {target_language}. "
            f"Supported languages: {supported}"
        )

    product_id = str(master_content.get("id") or "").strip()

    if not product_id:
        raise ValueError("Master content must contain a product id")

    source_json = json.dumps(
        master_content,
        ensure_ascii=False,
        indent=2,
    )

    field_list = "\n".join(f"- {field}" for field in OUTPUT_FIELDS)

    return f"""
You are a professional ecommerce localization editor.

Your task is to localize German product content into {profile["name"]}
for {profile["audience"]}.

Target locale: {profile["locale"]}

Writing style:
{profile["style"]}

Important rules:

1. Write every user-visible field entirely in {profile["name"]}.
2. Do not mix German, English, Russian, or any other language.
3. Do not translate mechanically word for word.
4. Preserve the factual meaning of the German source.
5. Do not invent specifications, prices, ratings, certifications, or claims.
6. Keep brand names and official product names unchanged when appropriate.
7. Make the text natural for the target-language audience.
8. SEO title must be no longer than 70 characters.
9. Meta description must be no longer than 160 characters.
10. Pinterest title must be no longer than 100 characters.
11. Pinterest description must be no longer than 500 characters.
12. Hashtags must be natural and relevant in the target language.
13. Return valid JSON only.
14. Do not include markdown, explanations, or code fences.

Return exactly these fields:

{field_list}

Required fixed values:

- id: "{product_id}"
- language: "{target_language}"
- source: "localized_from_de_v1"

German master content:

{source_json}
""".strip()
