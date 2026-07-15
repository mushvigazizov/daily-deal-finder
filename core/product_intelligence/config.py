from __future__ import annotations

# ── Scoring Weights (must sum to 100) ──────────────────────────
SCORING_WEIGHTS: dict[str, float] = {
    "identity": 0.30,
    "affiliate": 0.25,
    "quality": 0.20,
    "presentation": 0.15,
    "completeness": 0.10,
}

# ── Identity Thresholds ────────────────────────────────────────
IDENTITY_CONFIDENCE_MIN: int = 80   # Below this -> NEEDS_IDENTITY_REVIEW

# ── Quality Thresholds ─────────────────────────────────────────
QUALITY_RATING_MIN: float = 3.5     # Minimum star rating
QUALITY_REVIEWS_MIN: int = 50       # Minimum review count
QUALITY_REVIEWS_CEIL: int = 500     # Review count for max score

# ── Affiliate Normalization ────────────────────────────────────
COMMISSION_EUR_LOW: float = 0.0
COMMISSION_EUR_TARGET: float = 5.0   # Target commission to reach 80%
COMMISSION_EUR_HIGH: float = 15.0    # Commission where score maxes out

# ── Affiliate Freshness Decay ──────────────────────────────────
FRESHNESS_WINDOWS: dict[int, float] = {
    7: 1.0,      # 0-7 days    -> full value
    30: 0.8,     # 8-30 days   -> 80%
    90: 0.5,     # 31-90 days  -> 50%
    365: 0.2,    # 91-365 days -> 20%
}

# ── Presentation Requirements ──────────────────────────────────
PRESENTATION_MIN_IMAGE_WIDTH: int = 800
PRESENTATION_MIN_IMAGE_HEIGHT: int = 800

# ── Commission by Category (sample/placeholder for Phase 1) ────
# Real rates to be confirmed separately
CATEGORY_COMMISSION: dict[str, float] = {
    "camping": 0.05,
    "home": 0.05,
    "kitchen": 0.05,
    "tech": 0.04,
    "beauty": 0.04,
    "pets": 0.05,
    "gifts": 0.04,
    "outdoor": 0.05,
}

DEFAULT_COMMISSION: float = 0.04
