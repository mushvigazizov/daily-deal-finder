import json
import os

from core.ai.prompt_builder import build_product_prompt
from core.ai.config import (
    OPENAI_TEXT_MODEL,
    OPENAI_TEMPERATURE,
)

CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "seo_title": {"type": "string"},
        "seo_description": {"type": "string"},
        "pinterest_title": {"type": "string"},
        "pinterest_description": {"type": "string"},
        "buying_angle": {"type": "string"},
    },
    "required": [
        "seo_title",
        "seo_description",
        "pinterest_title",
        "pinterest_description",
        "buying_angle",
    ],
    "additionalProperties": False,
}

def generate_openai_content(product):
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_IMAGE_API_KEY")
    model = OPENAI_TEXT_MODEL

    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    try:
        client = OpenAI(api_key=api_key)
        prompt = build_product_prompt(product)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You write concise, honest German affiliate content. Return only valid JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "affiliate_product_content",
                    "schema": CONTENT_SCHEMA,
                    "strict": True,
                },
            },
            temperature=OPENAI_TEMPERATURE,
        )

        text = response.choices[0].message.content
        return json.loads(text)

    except Exception as error:
        print(f"[AI fallback] OpenAI content generation failed: {error}")
        return None
