"""Unit tests for Product Intelligence Scorer."""

from datetime import date, timedelta
import unittest

from core.product_intelligence.scorer import ProductScorer
from core.product_intelligence.schema import (
    DataQuality,
    ProductCandidate,
    ScorerDecision,
)


TODAY = date.today().isoformat()
OLD_60D = (date.today() - timedelta(days=60)).isoformat()
OLD_120D = (date.today() - timedelta(days=120)).isoformat()


def make_candidate(**overrides):
    defaults = {
        "product_id": "test-001",
        "asin": "B0TEST1234",
        "title": "Test Product",
        "brand": "TestBrand",
        "price_eur": 49.99,
        "rating": 4.3,
        "review_count": 200,
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "description": "A great test product with sufficient description length to pass the minimum threshold.",
        "category": "camping",
        "subcategory": "camping",
        "image_count": 4,
        "image_min_width": 1024,
        "image_min_height": 1024,
        "has_local_image": True,
        "source_date": TODAY,
        "identity_confidence": 92.0,
    }
    defaults.update(overrides)
    return ProductCandidate(**defaults)


class TestDeterministicQualityScore(unittest.TestCase):
    def setUp(self):
        self.scorer = ProductScorer()

    def test_full_observed_data_scores_high(self):
        c = make_candidate()
        result = self.scorer.score(c)
        self.assertGreater(result.quality_score, 70)
        self.assertEqual(result.decision, ScorerDecision.SCORED_CANDIDATE)
        for d in result.score_breakdown:
            self.assertNotEqual(d.quality, DataQuality.UNKNOWN,
                                f"{d.dimension} should be observed/derived")

    def test_missing_price_affiliate_is_zero(self):
        c = make_candidate(price_eur=None)
        result = self.scorer.score(c)
        aff = next(d for d in result.score_breakdown if d.dimension == "affiliate")
        self.assertEqual(aff.score, 0.0)
        self.assertEqual(aff.quality, DataQuality.UNKNOWN)

    def test_old_price_lowers_affiliate(self):
        fresh = make_candidate(source_date=TODAY)
        old = make_candidate(source_date=OLD_60D)
        self.assertGreater(
            self.scorer.score(fresh).score_breakdown[1].score,
            self.scorer.score(old).score_breakdown[1].score,
        )

    def test_commission_normalization(self):
        c = make_candidate(price_eur=100, commission_rate=0.05)
        aff_dim = self.scorer.score(c).score_breakdown[1]
        self.assertGreater(aff_dim.score, 60)

    def test_low_identity_leads_to_needs_review(self):
        c = make_candidate(identity_confidence=70)
        result = self.scorer.score(c)
        self.assertEqual(result.decision, ScorerDecision.NEEDS_IDENTITY_REVIEW)

    def test_no_auto_lock_at_any_score(self):
        for conf in [80, 85, 92, 98]:
            c = make_candidate(identity_confidence=float(conf))
            result = self.scorer.score(c)
            self.assertIn(result.decision, [ScorerDecision.SCORED_CANDIDATE,
                                             ScorerDecision.NEEDS_IDENTITY_REVIEW])

    def test_scorer_never_returns_verified_locked_publish(self):
        c = make_candidate(identity_confidence=95)
        result = self.scorer.score(c)
        forbidden = {"IDENTITY_VERIFIED", "IDENTITY_LOCKED", "PUBLISH_READY", "DISCOVERED"}
        self.assertNotIn(result.decision.value, forbidden)
        self.assertTrue(isinstance(result.decision, ScorerDecision))

    def test_invalid_data_rejected(self):
        for kwargs, label in [
            ({"price_eur": -10}, "negative price"),
            ({"rating": 6.0}, "rating over 5"),
            ({"review_count": -5}, "negative reviews"),
            ({"source_date": "2099-01-01"}, "future date"),
        ]:
            with self.subTest(label=label):
                result = self.scorer.score(make_candidate(**kwargs))
                self.assertTrue(len(result.errors) > 0, f"Expected errors for {label}")

    def test_weight_and_threshold_validation(self):
        from core.product_intelligence import config
        w = sum(config.SCORING_WEIGHTS.values())
        self.assertAlmostEqual(w, 1.0, msg="Weights must sum to 1.0")
        self.assertTrue(all(v >= 0 for v in config.SCORING_WEIGHTS.values()),
                        "Weights must be non-negative")
        self.assertLessEqual(config.COMMISSION_EUR_LOW, config.COMMISSION_EUR_TARGET)
        self.assertLessEqual(config.COMMISSION_EUR_TARGET, config.COMMISSION_EUR_HIGH)
        self.assertGreaterEqual(config.QUALITY_RATING_MIN, 0)
        self.assertLessEqual(config.QUALITY_RATING_MIN, 5)

    def test_missing_rating_doesnt_zero_quality(self):
        c = make_candidate(rating=None, review_count=None)
        result = self.scorer.score(c)
        self.assertGreater(result.quality_score, 0)

    def test_scored_candidate_state_returned(self):
        c = make_candidate(identity_confidence=88)
        self.assertEqual(self.scorer.score(c).decision, ScorerDecision.SCORED_CANDIDATE)

    def test_data_confidence_reflects_missing(self):
        full = make_candidate()
        sparse = make_candidate(price_eur=None, rating=None, review_count=None)
        self.assertGreater(
            self.scorer.score(full).data_confidence,
            self.scorer.score(sparse).data_confidence,
        )


if __name__ == "__main__":
    unittest.main()
