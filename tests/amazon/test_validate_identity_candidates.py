import unittest

from scripts.amazon.validate_identity_candidates import (
    CandidateValidationError,
    extract_url_asin,
    validate_candidate_payload,
)


def valid_candidate(
    asin="B0ABC12345",
):
    return {
        "asin": asin,
        "amazon_url": (
            f"https://www.amazon.de/dp/{asin}"
        ),
        "amazon_product_title": (
            "Skandika Familienzelt für 4 Personen"
        ),
        "amazon_brand": "Skandika",
        "amazon_model": "Example Model",
        "amazon_size": "",
        "amazon_color": "",
        "amazon_key_specs": [
            "4 Personen",
            "Stehhöhe",
        ],
    }


class TestValidateIdentityCandidates(unittest.TestCase):
    def test_valid_payload_passes(self):
        payload = {
            "product_id": "camp-002",
            "candidates": [
                valid_candidate(),
            ],
        }

        candidates = validate_candidate_payload(
            payload,
            expected_product_id="camp-002",
        )

        self.assertEqual(len(candidates), 1)

    def test_product_id_mismatch_is_rejected(self):
        payload = {
            "product_id": "camp-999",
            "candidates": [],
        }

        with self.assertRaisesRegex(
            CandidateValidationError,
            "product_id mismatch",
        ):
            validate_candidate_payload(
                payload,
                expected_product_id="camp-002",
            )

    def test_invalid_asin_is_rejected(self):
        candidate = valid_candidate(
            asin="WRONG",
        )
        payload = {
            "product_id": "camp-002",
            "candidates": [candidate],
        }

        with self.assertRaisesRegex(
            CandidateValidationError,
            "invalid ASIN",
        ):
            validate_candidate_payload(
                payload,
                expected_product_id="camp-002",
            )

    def test_url_asin_mismatch_is_rejected(self):
        candidate = valid_candidate()
        candidate["amazon_url"] = (
            "https://www.amazon.de/dp/B0ZZZ99999"
        )
        payload = {
            "product_id": "camp-002",
            "candidates": [candidate],
        }

        with self.assertRaisesRegex(
            CandidateValidationError,
            "does not match candidate ASIN",
        ):
            validate_candidate_payload(
                payload,
                expected_product_id="camp-002",
            )

    def test_duplicate_asin_is_rejected(self):
        payload = {
            "product_id": "camp-002",
            "candidates": [
                valid_candidate(),
                valid_candidate(),
            ],
        }

        with self.assertRaisesRegex(
            CandidateValidationError,
            "duplicate ASIN",
        ):
            validate_candidate_payload(
                payload,
                expected_product_id="camp-002",
            )

    def test_gp_product_url_is_supported(self):
        asin = extract_url_asin(
            "https://www.amazon.de/gp/product/B0ABC12345"
        )

        self.assertEqual(
            asin,
            "B0ABC12345",
        )


if __name__ == "__main__":
    unittest.main()
