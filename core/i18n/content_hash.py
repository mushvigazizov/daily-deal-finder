import hashlib
import json


TRACKED_FIELDS = (
    "title",
    "short_description",
    "long_description",
    "features",
    "button_text",
    "buying_angle",
    "seo_title",
    "meta_description",
    "alt_text",
    "pinterest_title",
    "pinterest_description",
    "hashtags",
)


def build_source_hash(content: dict) -> str:
    payload = {
        key: content.get(key)
        for key in TRACKED_FIELDS
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()
