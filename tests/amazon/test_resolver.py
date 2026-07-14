"""Unit tests for AmazonIdentityResolver."""

import unittest

from core.amazon.resolver import (
    AmazonIdentityResolver,
    ResolutionDecision,
    ResolutionResult,
)


PRODUCT = {
    "id": "camp-014",
    "title": "Mobicool ME24 Elektrische Kuhlbox 23L 12V & 230V",
    "brand": "Mobicool",
    "features": ["23L Nutzinhalt", "12V DC & 230V AC Betrieb", "Thermoelektrisches Kuhlsystem"],
}

STRONG_CANDIDATE = {
    "asin": "B094G4Y1K3",
    "amazon_url": "https://www.amazon.de/dp/B094G4Y1K3",
    "amazon_product_title": "Mobicool ME24 elektrische Kuhlbox, 12V und 230V, 23L, blau",
    "amazon_brand": "Mobicool",
    "amazon_model": "ME24",
    "amazon_key_specs": ["Nutzinhalt: 23 Liter", "Stromversorgung: 12V DC und 230V AC"],
}

MEDIUM_CANDIDATE = {
    "asin": "B09XYZ1234",
    "amazon_url": "https://www.amazon.de/dp/B09XYZ1234",
    "amazon_product_title": "Mobicool Elektrische Kuhlbox 24L, 12V und 230V, tragbar, blau",
    "amazon_brand": "Mobicool",
    "amazon_model": "TC24",
    "amazon_key_specs": ["24 Liter Kapazitat", "12V und 230V Anschluss", "Thermoelektrisches Kuhlsystem"],
}

WEAK_CANDIDATE = {
    "asin": "B01WEAK999",
    "amazon_url": "https://www.amazon.de/dp/B01WEAK999",
    "amazon_product_title": "Mini Ventilator USB",
    "amazon_brand": "NoName",
    "amazon_model": "",
    "amazon_key_specs": ["USB powered", "small"],
}

INVALID_CANDIDATE = {
    "asin": "BAD",
    "amazon_url": "",
    "amazon_product_title": "",
    "amazon_brand": "",
}


class TestResolverVerified(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver()

    def test_verified_strong_match(self):
        result = self.resolver.resolve(PRODUCT, [STRONG_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.VERIFIED)
        self.assertGreaterEqual(result.confidence, 90)
        self.assertTrue(result.should_lock)
        self.assertEqual(result.best_candidate["asin"], "B094G4Y1K3")
        self.assertEqual(len(result.errors), 0)


class TestResolverReviewRequired(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver()

    def test_review_required(self):
        result = self.resolver.resolve(PRODUCT, [MEDIUM_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.REVIEW_REQUIRED)
        self.assertGreaterEqual(result.confidence, 70)
        self.assertLess(result.confidence, 90)
        self.assertFalse(result.should_lock)


class TestResolverRejected(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver()

    def test_rejected_weak(self):
        result = self.resolver.resolve(PRODUCT, [WEAK_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.REJECTED)
        self.assertLess(result.confidence, 70)
        self.assertFalse(result.should_lock)


class TestResolverBlocked(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver()

    def test_blocked_no_candidates(self):
        result = self.resolver.resolve(PRODUCT, [])
        self.assertEqual(result.decision, ResolutionDecision.BLOCKED)
        self.assertIn("no candidates", result.errors[0] if result.errors else "")

    def test_blocked_all_invalid(self):
        result = self.resolver.resolve(PRODUCT, [INVALID_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.BLOCKED)
        self.assertGreater(len(result.errors), 0)


class TestResolverConflict(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver(guard_mode=True)

    def test_conflict_locked_identity(self):
        product = {**PRODUCT, "verified_asin": "B094G4Y1K3", "identity_locked": True}
        result = self.resolver.resolve(product, [STRONG_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.VERIFIED)

    def test_conflict_mismatch(self):
        product = {**PRODUCT, "verified_asin": "B999999999", "identity_locked": True}
        result = self.resolver.resolve(product, [STRONG_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.CONFLICT)


class TestResolverGuardOff(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver(guard_mode=False)

    def test_guard_mode_disabled(self):
        product = {**PRODUCT, "verified_asin": "B999999999", "identity_locked": True}
        result = self.resolver.resolve(product, [STRONG_CANDIDATE])
        self.assertEqual(result.decision, ResolutionDecision.VERIFIED)


class TestResolverIdempotent(unittest.TestCase):
    def setUp(self):
        self.resolver = AmazonIdentityResolver()

    def test_idempotent(self):
        r1 = self.resolver.resolve(PRODUCT, [STRONG_CANDIDATE])
        r2 = self.resolver.resolve(PRODUCT, [STRONG_CANDIDATE])
        self.assertEqual(r1.decision, r2.decision)
        self.assertEqual(r1.confidence, r2.confidence)
        self.assertEqual(r1.should_lock, r2.should_lock)


if __name__ == "__main__":
    unittest.main()
