import hashlib
import json


TRACKED_FIELDS = (
    "seo_title",
    "seo_description",
    "pinterest_title",
    "pinterest_description",
    "buying_angle",
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
