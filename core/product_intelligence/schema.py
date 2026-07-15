from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class ScorerDecision(str, Enum):
    SCORED_CANDIDATE = "SCORED_CANDIDATE"
    NEEDS_IDENTITY_REVIEW = "NEEDS_IDENTITY_REVIEW"


class DataQuality(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    UNKNOWN = "unknown"


@dataclass
class DimensionScore:
    dimension: str
    score: float            # 0-100 for this dimension
    weight: float           # configured weight
    quality: DataQuality = DataQuality.UNKNOWN
    missing_fields: list[str] = field(default_factory=list)


@dataclass
class ScoringResult:
    product_id: str
    decision: ScorerDecision
    quality_score: float              # 0-100, normalized over scored dims
    data_confidence: float            # 0-100, completeness * freshness
    score_breakdown: list[DimensionScore] = field(default_factory=list)
    missing_dimensions: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )


@dataclass
class ProductCandidate:
    product_id: str
    asin: str
    title: str = ""
    brand: str = ""
    price_eur: float | None = None
    rating: float | None = None
    review_count: int | None = None
    features: list[str] = field(default_factory=list)
    description: str = ""
    category: str = ""
    subcategory: str = ""
    image_count: int = 0
    image_min_width: int = 0
    image_min_height: int = 0
    has_local_image: bool = False
    source_date: str = ""             # ISO date when data was collected
    commission_rate: float | None = None
    identity_confidence: float | None = None   # From AmazonIdentityResolver
