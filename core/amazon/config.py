from __future__ import annotations

from pathlib import Path

_project_root = Path(__file__).resolve().parents[2]

PRODUCTS_PATH: Path = _project_root / "data" / "products.json"
PRODUCTS_BACKUP_DIR: Path = _project_root / "backups" / "products"
REGISTRY_PATH: Path = _project_root / "scripts" / "importers" / "asin_import_template.json"
CANDIDATES_DIR: Path = _project_root / "data" / "amazon_candidates"
CONTENT_DIR: Path = _project_root / "data" / "content"
STATE_DIR: Path = _project_root / "data" / "state"
PINTEREST_CONTENT_PATH: Path = _project_root / "data" / "pinterest_content.json"
PINTEREST_PROMPTS_PATH: Path = _project_root / "data" / "pinterest_prompts.json"
IDENTITY_SYNC_BACKUP_DIR: Path = _project_root / "backups" / "identity-sync"
DEFAULT_BACKUP_DIR: Path = _project_root / "backups"

ASIN_PATTERN: str = r"^[A-Z0-9]{10}$"
AMAZON_DOMAIN: str = "www.amazon.de"

PROTECTED_IDENTITY_FIELDS: tuple[str, ...] = (
    "verified_asin",
    "verified_amazon_url",
    "amazon_product_title",
    "amazon_brand",
    "amazon_model",
    "amazon_size",
    "amazon_color",
    "amazon_key_specs",
    "verification_status",
    "verification_source",
    "identity_hash",
    "identity_locked",
)

DERIVED_PRODUCT_FIELDS: dict[str, object] = {
    "amazon_link_type": "product",
    "asin_verified": True,
    "identity_locked": True,
}

RESOLVER_THRESHOLDS: dict[str, int] = {
    "STRONG_MIN": 90,
    "MANUAL_MIN": 70,
}

RESOLVER_WEIGHTS: dict[str, float] = {
    "TITLE": 0.45,
    "BRAND": 0.30,
    "FEATURES": 0.20,
    "MODEL": 0.05,
}

RESOLVER_GUARD_MODE: bool = True
