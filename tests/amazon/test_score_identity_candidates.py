import unittest

from scripts.amazon.score_identity_candidates import (
    candidate_score,
)


class TestScoreIdentityCandidates(unittest.TestCase):
    def setUp(self):
        self.product = {
            "id": "camp-002",
            "title": (
                "Skandika Familienzelt 4-Personen "
                "Geräumig Sturmfest"
            ),
            "brand": "Skandika",
            "features": [
                "4-Personen Kapazität",
                "Stehhöhe im Innenraum",
                "Sturmfeste Konstruktion",
                "Moskitonetz integriert",
            ],
        }

    def test_strong_matching_candidate_scores_high(self):
        candidate = {
            "asin": "B0TEST1234",
            "amazon_url": (
                "https://www.amazon.de/dp/B0TEST1234"
            ),
            "amazon_product_title": (
                "Skandika Familienzelt für 4 Personen "
                "mit Stehhöhe und Moskitonetz"
            ),
            "amazon_brand": "Skandika",
            "amazon_model": "Familienzelt",
            "amazon_key_specs": [
                "4 Personen",
                "Stehhöhe",
                "Moskitonetz",
                "sturmfeste Konstruktion",
            ],
        }

        result = candidate_score(
            self.product,
            candidate,
        )

        self.assertGreaterEqual(
            result["confidence"],
            70,
        )
        self.assertIn(
            result["decision"],
            {
                "strong_candidate",
                "manual_review",
            },
        )

    def test_wrong_brand_scores_lower(self):
        correct = {
            "asin": "B0TEST1234",
            "amazon_product_title": (
                "Skandika Familienzelt 4 Personen"
            ),
            "amazon_brand": "Skandika",
            "amazon_model": "",
            "amazon_key_specs": [
                "4 Personen",
                "Stehhöhe",
            ],
        }

        wrong = {
            "asin": "B0TEST9999",
            "amazon_product_title": (
                "Andere Marke Familienzelt 4 Personen"
            ),
            "amazon_brand": "Andere Marke",
            "amazon_model": "",
            "amazon_key_specs": [
                "4 Personen",
                "Stehhöhe",
            ],
        }

        correct_result = candidate_score(
            self.product,
            correct,
        )
        wrong_result = candidate_score(
            self.product,
            wrong,
        )

        self.assertGreater(
            correct_result["confidence"],
            wrong_result["confidence"],
        )

    def test_empty_candidate_is_weak(self):
        result = candidate_score(
            self.product,
            {},
        )

        self.assertEqual(
            result["decision"],
            "weak_candidate",
        )
        self.assertEqual(
            result["confidence"],
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
