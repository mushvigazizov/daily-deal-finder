"""Product Intelligence Scorer — deterministic, no side effects, no auto-lock."""

from __future__ import annotations

from datetime import date, datetime

from core.product_intelligence.schema import (
    DataQuality,
    DimensionScore,
    ProductCandidate,
    ScorerDecision,
    ScoringResult,
)
from core.product_intelligence.config import (
    CATEGORY_COMMISSION,
    COMMISSION_EUR_HIGH,
    COMMISSION_EUR_LOW,
    COMMISSION_EUR_TARGET,
    DEFAULT_COMMISSION,
    FRESHNESS_WINDOWS,
    IDENTITY_CONFIDENCE_MIN,
    PRESENTATION_MIN_IMAGE_HEIGHT,
    PRESENTATION_MIN_IMAGE_WIDTH,
    QUALITY_RATING_MIN,
    QUALITY_REVIEWS_CEIL,
    QUALITY_REVIEWS_MIN,
    SCORING_WEIGHTS,
)


def _validate_weights() -> None:
    total = sum(SCORING_WEIGHTS.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
    if any(w < 0 for w in SCORING_WEIGHTS.values()):
        raise ValueError("Scoring weights must be non-negative")


def _validate_thresholds() -> None:
    if not (COMMISSION_EUR_LOW <= COMMISSION_EUR_TARGET <= COMMISSION_EUR_HIGH):
        raise ValueError(
            f"Commission thresholds: LOW({COMMISSION_EUR_LOW}) "
            f"<= TARGET({COMMISSION_EUR_TARGET}) "
            f"<= HIGH({COMMISSION_EUR_HIGH}) violated"
        )
    if QUALITY_RATING_MIN < 0 or QUALITY_RATING_MIN > 5:
        raise ValueError(f"QUALITY_RATING_MIN must be 0-5, got {QUALITY_RATING_MIN}")
    if QUALITY_REVIEWS_MIN > QUALITY_REVIEWS_CEIL:
        raise ValueError("QUALITY_REVIEWS_MIN must be <= QUALITY_REVIEWS_CEIL")


class ProductScorer:
    def __init__(self):
        _validate_weights()
        _validate_thresholds()

    def score(self, candidate: ProductCandidate) -> ScoringResult:
        errors: list[str] = []
        reasons: list[str] = []
        dimensions: list[DimensionScore] = []

        # ── Validate candidate fields ──
        if candidate.price_eur is not None and candidate.price_eur <= 0:
            errors.append(f"Invalid price_eur: {candidate.price_eur}")
        if candidate.rating is not None and (candidate.rating < 0 or candidate.rating > 5):
            errors.append(f"Invalid rating: {candidate.rating}")
        if candidate.review_count is not None and candidate.review_count < 0:
            errors.append(f"Invalid review_count: {candidate.review_count}")
        if candidate.source_date:
            try:
                sd = date.fromisoformat(candidate.source_date)
                if sd > date.today():
                    errors.append(f"Future source_date: {candidate.source_date}")
            except ValueError:
                errors.append(f"Bad source_date format: {candidate.source_date}")

        # ── Identity ──
        if candidate.identity_confidence is not None:
            id_score = min(100.0, candidate.identity_confidence)
            dimensions.append(DimensionScore("identity", id_score, SCORING_WEIGHTS["identity"], DataQuality.OBSERVED))
        else:
            dimensions.append(DimensionScore("identity", 0.0, SCORING_WEIGHTS["identity"], DataQuality.UNKNOWN,
                                             missing_fields=["identity_confidence"]))

        # ── Affiliate ──
        if candidate.price_eur is not None and candidate.price_eur > 0:
            comm_rate = candidate.commission_rate or CATEGORY_COMMISSION.get(candidate.subcategory, DEFAULT_COMMISSION)
            estimated = candidate.price_eur * comm_rate
            # Normalize
            if estimated <= COMMISSION_EUR_LOW:
                raw_aff = 0.0
            elif estimated >= COMMISSION_EUR_HIGH:
                raw_aff = 100.0
            elif estimated <= COMMISSION_EUR_TARGET:
                raw_aff = (estimated - COMMISSION_EUR_LOW) / (COMMISSION_EUR_TARGET - COMMISSION_EUR_LOW) * 79.0
            else:
                raw_aff = 79.0 + (estimated - COMMISSION_EUR_TARGET) / (COMMISSION_EUR_HIGH - COMMISSION_EUR_TARGET) * 21.0
            # Freshness
            freshness = _source_freshness(candidate.source_date)
            # Source confidence: how much data is observed vs unknown
            source_conf = _source_confidence(candidate)
            aff_score = raw_aff * freshness * source_conf
            dimensions.append(DimensionScore("affiliate", aff_score, SCORING_WEIGHTS["affiliate"], DataQuality.DERIVED))
        else:
            dimensions.append(DimensionScore("affiliate", 0.0, SCORING_WEIGHTS["affiliate"], DataQuality.UNKNOWN,
                                             missing_fields=["price_eur"]))

        # ── Quality ──
        q_score = 0.0
        q_missing = []
        q_observed = False
        if candidate.rating is not None and candidate.review_count is not None:
            if candidate.rating >= QUALITY_RATING_MIN and candidate.review_count >= QUALITY_REVIEWS_MIN:
                rating_part = min(1.0, candidate.rating / 5.0) * 60.0
                review_part = min(1.0, candidate.review_count / QUALITY_REVIEWS_CEIL) * 40.0
                q_score = rating_part + review_part
                q_observed = True
            else:
                q_score = max(0.0, min(1.0, candidate.rating / 5.0) * 30.0)
                q_observed = True
        if not q_observed:
            if candidate.rating is None:
                q_missing.append("rating")
            if candidate.review_count is None:
                q_missing.append("review_count")

        dimensions.append(DimensionScore(
            "quality", q_score, SCORING_WEIGHTS["quality"],
            DataQuality.OBSERVED if q_observed else DataQuality.UNKNOWN,
            missing_fields=q_missing,
        ))

        # ── Presentation Readiness ──
        pres_missing = []
        pres_score = 0.0
        if candidate.has_local_image:
            pres_score += 40
        if candidate.image_count > 0:
            pres_score += min(20, candidate.image_count * 5)
        if candidate.image_min_width >= PRESENTATION_MIN_IMAGE_WIDTH and candidate.image_min_height >= PRESENTATION_MIN_IMAGE_HEIGHT:
            pres_score += 20
        if candidate.description and len(candidate.description) > 50:
            pres_score += 10
        if candidate.features and len(candidate.features) >= 3:
            pres_score += 10

        if not candidate.has_local_image:
            pres_missing.append("local_image")
        if candidate.image_count == 0:
            pres_missing.append("image_count")

        dimensions.append(DimensionScore(
            "presentation", pres_score, SCORING_WEIGHTS["presentation"],
            DataQuality.OBSERVED if candidate.has_local_image else DataQuality.UNKNOWN,
            missing_fields=pres_missing,
        ))

        # ── Completeness ──
        total_dims = len(dimensions)
        scored_dims = sum(1 for d in dimensions if d.quality != DataQuality.UNKNOWN)
        comp_score = (scored_dims / total_dims) * 100.0 if total_dims > 0 else 0.0
        missing_dim_names = [d.dimension for d in dimensions if d.quality == DataQuality.UNKNOWN]

        dimensions.append(DimensionScore("completeness", comp_score, SCORING_WEIGHTS["completeness"],
                                         DataQuality.DERIVED, missing_fields=missing_dim_names))

        # ── Quality Score (normalized over scored dimensions only) ──
        scored_weights = sum(d.weight for d in dimensions if d.quality != DataQuality.UNKNOWN)
        if scored_weights > 0:
            quality_score = min(100.0, sum(d.score * d.weight for d in dimensions) / scored_weights * 1.0)
        else:
            quality_score = 0.0

        # ── Data confidence ──
        completeness = scored_dims / total_dims if total_dims > 0 else 0.0
        freshness = _source_freshness(candidate.source_date)
        data_confidence = min(100.0, completeness * freshness * 100.0)

        # ── Decision ──
        identity_dim = next((d for d in dimensions if d.dimension == "identity"), None)
        id_conf = candidate.identity_confidence or 0

        if errors:
            reasons.append(f"Validation errors: {len(errors)}")
        if data_confidence < 70:
            reasons.append(f"Low data confidence: {data_confidence:.1f}%")

        if id_conf < IDENTITY_CONFIDENCE_MIN:
            decision = ScorerDecision.NEEDS_IDENTITY_REVIEW
            reasons.append(f"Identity confidence {id_conf:.0f}% < {IDENTITY_CONFIDENCE_MIN}% threshold")
        else:
            decision = ScorerDecision.SCORED_CANDIDATE

        return ScoringResult(
            product_id=candidate.product_id,
            decision=decision,
            quality_score=round(quality_score, 1),
            data_confidence=round(data_confidence, 1),
            score_breakdown=dimensions,
            missing_dimensions=missing_dim_names,
            reasons=reasons,
            errors=errors,
        )


def _source_freshness(source_date_str: str) -> float:
    if not source_date_str:
        return 0.3
    try:
        sd = date.fromisoformat(source_date_str)
        days = (date.today() - sd).days
        for window_days, factor in sorted(FRESHNESS_WINDOWS.items()):
            if days <= window_days:
                return factor
        return 0.1
    except ValueError:
        return 0.3


def _source_confidence(candidate: ProductCandidate) -> float:
    fields = 0
    observed = 0
    for val in [candidate.price_eur, candidate.rating, candidate.review_count, candidate.identity_confidence]:
        fields += 1
        if val is not None:
            observed += 1
    return observed / fields if fields > 0 else 0.3
