import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.amazon.identity_lock import compute_identity_hash



PRODUCTS_PATH = Path("data/products.json")
REGISTRY_PATH = Path("scripts/importers/asin_import_template.json")
CONTENT_DIR = Path("data/content")
STATE_DIR = Path("data/state")
PINTEREST_CONTENT_PATH = Path("data/pinterest_content.json")
PINTEREST_PROMPTS_PATH = Path("data/pinterest_prompts.json")
BACKUP_DIR = Path("backups/identity-sync")


# camp-014 daxil olmaqla butun verified identity-ler
# data/verified_identities/*.json fayllarindan yuklenir.
# Hardcoded mehsul mezmunu QADAGANDIR — kontaminasiya yaradir.
VERIFIED_IDENTITIES: dict[str, dict[str, Any]] = {}


VERIFIED_IDENTITIES_DIR = Path("data/verified_identities")


def load_external_verified_identities() -> None:
    if not VERIFIED_IDENTITIES_DIR.exists():
        return

    for identity_path in sorted(
        VERIFIED_IDENTITIES_DIR.glob("*.json")
    ):
        product_id = identity_path.stem
        identity = json.loads(
            identity_path.read_text(encoding="utf-8")
        )

        if not isinstance(identity, dict):
            raise SystemExit(
                f"ERROR: identity file must contain an object: "
                f"{identity_path}"
            )

        VERIFIED_IDENTITIES[product_id] = identity


load_external_verified_identities()



def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, indent=2)
        + "\n"
    )


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def content_fingerprint(product: dict[str, Any]) -> str:
    tracked = {
        key: product.get(key)
        for key in (
            "title",
            "brand",
            "short_description",
            "long_description",
            "features",
            "tags",
            "buying_angle",
            "seo_title",
            "seo_description",
            "pinterest_title",
            "pinterest_description",
            "amazon_asin",
            "verified_asin",
            "verified_amazon_url",
            "amazon_model",
            "identity_hash",
        )
    }

    serialized = json.dumps(
        tracked,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def find_record(
    records: list[dict[str, Any]],
    product_id: str,
    id_keys: tuple[str, ...],
) -> dict[str, Any] | None:
    for record in records:
        if any(
            record.get(key) == product_id
            for key in id_keys
        ):
            return record

    return None


def prepare_changes(
    product_id: str,
) -> dict[Path, Any]:
    identity = VERIFIED_IDENTITIES.get(product_id)

    if identity is None:
        raise SystemExit(
            f"ERROR: no verified identity configured for {product_id}"
        )

    timestamp = utc_now()
    computed_identity_hash = compute_identity_hash(identity)

    products_payload = load_json(PRODUCTS_PATH)
    products = products_payload.get(
        "products",
        products_payload,
    )

    product = find_record(
        products,
        product_id,
        ("id",),
    )

    if product is None:
        raise SystemExit(
            f"ERROR: product not found: {product_id}"
        )

    website = identity["website"]

    product.update({
        "title": website["title"],
        "brand": website["brand"],
        "short_description": website[
            "short_description"
        ],
        "long_description": website[
            "long_description"
        ],
        "features": website["features"],
        "tags": website["tags"],
        "buying_angle": website["buying_angle"],
        "seo_title": website["seo_title"],
        "seo_description": website[
            "seo_description"
        ],
        "pinterest_title": website[
            "pinterest_title"
        ],
        "pinterest_description": website[
            "pinterest_description"
        ],
        "amazon_asin": identity["verified_asin"],
        "verified_asin": identity["verified_asin"],
        "verified_amazon_url": identity[
            "verified_amazon_url"
        ],
        "amazon_url": identity[
            "verified_amazon_url"
        ],
        "amazon_link_type": "product",
        "asin_verified": True,
        "verification_status": "verified",
        "verification_source": identity[
            "verification_source"
        ],
        "manufacturer_source": identity[
            "manufacturer_source"
        ],
        "amazon_product_title": identity[
            "amazon_product_title"
        ],
        "amazon_brand": identity[
            "amazon_brand"
        ],
        "amazon_model": identity[
            "amazon_model"
        ],
        "amazon_key_specs": sorted(
            str(item).strip().lower()
            for item in identity["amazon_key_specs"]
        ),
        "identity_hash": computed_identity_hash,
        "identity_locked": True,
        "content_status": "verified_product_refreshed",
        "content_engine": "amazon_identity_sync_v1",
        "asin_verified_at": timestamp,
        "identity_applied_at": timestamp,
        "updated_at": timestamp[:10],
    })

    registry = load_json(REGISTRY_PATH)
    registry_item = find_record(
        registry,
        product_id,
        ("id",),
    )

    if registry_item is None:
        raise SystemExit(
            f"ERROR: registry item not found: {product_id}"
        )

    registry_item.update({
        "title": website["title"],
        "verified_asin": identity[
            "verified_asin"
        ],
        "verified_amazon_url": identity[
            "verified_amazon_url"
        ],
        "status": "verified",
        "notes": (
            "Verified Amazon-first product identity. "
            "Website content synchronized from "
            f"{identity['amazon_brand']} {identity['amazon_model']}."
        ),
        "amazon_product_title": identity[
            "amazon_product_title"
        ],
        "amazon_brand": identity[
            "amazon_brand"
        ],
        "amazon_model": identity[
            "amazon_model"
        ],
        "amazon_key_specs": identity[
            "amazon_key_specs"
        ],
        "verification_status": "verified",
        "verification_source": identity[
            "verification_source"
        ],
        "manufacturer_source": identity[
            "manufacturer_source"
        ],
        "identity_hash": computed_identity_hash,
        "identity_locked": True,
    })

    de_content = {
        "id": product_id,
        "language": "de",
        "title": website["title"],
        "short_description": website[
            "short_description"
        ],
        "long_description": website[
            "long_description"
        ],
        "features": website["features"],
        "button_text": product.get(
            "button_text",
            "Auf Amazon ansehen",
        ),
        "buying_angle": website["buying_angle"],
        "seo_title": website["seo_title"],
        "meta_description": website[
            "seo_description"
        ],
        "alt_text": website["alt_text"],
        "pinterest_title": website[
            "pinterest_title"
        ],
        "pinterest_description": website[
            "pinterest_description"
        ],
        "hashtags": website["hashtags"],
        "source": "amazon_verified_identity_v1",
        "source_language": "de",
        "identity_hash": computed_identity_hash,
        "generated_at": timestamp,
        "content_engine": "amazon_identity_sync_v1",
    }

    en_content = {
        "id": product_id,
        "language": "en",
        **identity["english"],
        "source": "localized_from_verified_de_v1",
        "source_language": "de",
        "source_hash": content_fingerprint(product),
        "identity_hash": computed_identity_hash,
        "generated_at": timestamp,
        "content_engine": "amazon_identity_sync_v1",
    }

    pinterest_payload = load_json(
        PINTEREST_CONTENT_PATH
    )
    pinterest_records = (
        pinterest_payload.get("pins")
        or pinterest_payload.get("products")
        or pinterest_payload
    )

    pinterest_item = find_record(
        pinterest_records,
        product_id,
        ("product_id", "id"),
    )

    if pinterest_item is None:
        raise SystemExit(
            f"ERROR: {product_id} Pinterest record not found."
        )

    pinterest_item.update({
        "title": website["pinterest_title"],
        "description": website[
            "pinterest_description"
        ],
        "target_url": (
            f"/product.html?id={product_id}"
        ),
        "status": "ready",
        "updated_at": timestamp[:10],
        "identity_hash": computed_identity_hash,
    })

    prompts_payload = load_json(
        PINTEREST_PROMPTS_PATH
    )
    prompt_records = (
        prompts_payload.get("prompts")
        or prompts_payload.get("products")
        or prompts_payload
    )

    prompt_item = find_record(
        prompt_records,
        product_id,
        ("product_id", "id"),
    )

    if prompt_item is None:
        raise SystemExit(
            f"ERROR: {product_id} Pinterest prompt not found."
        )

    prompt_item["prompt"] = website["pinterest_prompt"]
    prompt_item["identity_hash"] = computed_identity_hash
    prompt_item["updated_at"] = timestamp[:10]

    state = {
        "id": product_id,
        "fingerprint": content_fingerprint(product),
        "identity_hash": computed_identity_hash,
        "content_engine": "amazon_identity_sync_v1",
        "updated_at": timestamp,
    }

    products_payload["_updated"] = timestamp

    return {
        PRODUCTS_PATH: products_payload,
        REGISTRY_PATH: registry,
        CONTENT_DIR / f"{product_id}.de.json": de_content,
        CONTENT_DIR / f"{product_id}.en.json": en_content,
        PINTEREST_CONTENT_PATH: pinterest_payload,
        PINTEREST_PROMPTS_PATH: prompts_payload,
        STATE_DIR / f"{product_id}.json": state,
    }


def print_summary(
    changes: dict[Path, Any],
    product_id: str,
) -> None:
    product_payload = changes[PRODUCTS_PATH]
    products = product_payload.get(
        "products",
        product_payload,
    )
    product = find_record(
        products,
        product_id,
        ("id",),
    )

    print("=" * 78)
    print("AMAZON-FIRST VERIFIED IDENTITY SYNCHRONIZER")
    print("=" * 78)
    print(f"Product ID  : {product_id}")
    print(f"Title       : {product.get('title')}")
    print(f"ASIN        : {product.get('verified_asin')}")
    print(f"Model       : {product.get('amazon_model')}")
    print(f"Identity    : {product.get('identity_hash')}")
    print()
    print("Files:")
    for path in changes:
        print(f"  - {path}")


def write_changes(
    changes: dict[Path, Any],
) -> None:
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d-%H%M%SZ")

    backup_root = BACKUP_DIR / timestamp
    backup_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    temporary_files: list[
        tuple[Path, Path]
    ] = []

    try:
        for path, payload in changes.items():
            if path.exists():
                backup_path = backup_root / path
                backup_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                shutil.copy2(path, backup_path)

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_path = path.with_suffix(
                path.suffix + ".tmp"
            )
            temporary_path.write_text(
                dump_json(payload),
                encoding="utf-8",
            )
            temporary_files.append(
                (temporary_path, path)
            )

        for temporary_path, path in temporary_files:
            temporary_path.replace(path)

    except Exception:
        for temporary_path, _ in temporary_files:
            temporary_path.unlink(
                missing_ok=True
            )
        raise

    print(f"Backup      : {backup_root}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize website content from a verified "
            "Amazon-first product identity."
        )
    )
    parser.add_argument(
        "--product-id",
        required=True,
    )
    parser.add_argument(
        "--write",
        action="store_true",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changes = prepare_changes(
        args.product_id
    )

    print_summary(
        changes,
        args.product_id,
    )

    if not args.write:
        print()
        print("Write mode  : DRY RUN")
        print("No files were changed.")
        return 0

    write_changes(changes)

    print()
    print("Write mode  : WRITTEN")
    print("All identity-dependent files were synchronized.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
