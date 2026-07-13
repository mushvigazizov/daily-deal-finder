import unittest

from core.amazon.identity_lock import (
    canonical_identity,
    compute_identity_hash,
    validate_identity_for_lock,
    verify_existing_lock,
)


def valid_record():
    return {
        "id": "camp-test",
        "verified_asin": "B0ABC12345",
        "verified_amazon_url": "https://www.amazon.de/dp/B0ABC12345",
        "amazon_product_title": "Example Outdoor Product",
        "amazon_brand": "Example",
        "amazon_model": "Model 100",
        "amazon_size": "40 L",
        "amazon_color": "Black",
        "amazon_key_specs": [
            "40 litre capacity",
            "Water resistant",
        ],
        "verification_status": "verified",
        "verification_source": "manual_amazon_de_review",
    }


class TestAmazonIdentityLock(unittest.TestCase):
    def test_valid_identity_can_be_locked(self):
        result = validate_identity_for_lock(valid_record())

        self.assertTrue(result.valid)
        self.assertEqual(len(result.identity_hash), 64)
        self.assertEqual(result.issues, ())

    def test_missing_brand_is_rejected(self):
        record = valid_record()
        record["amazon_brand"] = ""

        result = validate_identity_for_lock(record)

        self.assertFalse(result.valid)
        self.assertIn("missing amazon_brand", result.issues)

    def test_missing_key_specs_is_rejected(self):
        record = valid_record()
        record["amazon_key_specs"] = []

        result = validate_identity_for_lock(record)

        self.assertFalse(result.valid)
        self.assertIn("missing amazon_key_specs", result.issues)

    def test_wrong_amazon_url_is_rejected(self):
        record = valid_record()
        record["verified_amazon_url"] = (
            "https://www.amazon.de/dp/B0WRONG123"
        )

        result = validate_identity_for_lock(record)

        self.assertFalse(result.valid)
        self.assertIn(
            "verified_amazon_url does not match verified_asin",
            result.issues,
        )

    def test_hash_is_stable_for_spec_order(self):
        first = valid_record()
        second = valid_record()
        second["amazon_key_specs"] = list(
            reversed(second["amazon_key_specs"])
        )

        self.assertEqual(
            compute_identity_hash(first),
            compute_identity_hash(second),
        )

    def test_changed_model_breaks_existing_lock(self):
        record = valid_record()
        record["identity_hash"] = compute_identity_hash(record)
        record["identity_locked"] = True

        original = verify_existing_lock(record)
        self.assertTrue(original.valid)

        record["amazon_model"] = "Model 200"

        changed = verify_existing_lock(record)

        self.assertFalse(changed.valid)
        self.assertIn("identity_hash mismatch", changed.issues)

    def test_lock_flag_is_required(self):
        record = valid_record()
        record["identity_hash"] = compute_identity_hash(record)
        record["identity_locked"] = False

        result = verify_existing_lock(record)

        self.assertFalse(result.valid)
        self.assertIn("identity_locked must be true", result.issues)

    def test_canonical_identity_normalizes_values(self):
        record = valid_record()
        record["verified_asin"] = "b0abc12345"
        record["amazon_brand"] = "  Example   Brand "
        record["amazon_key_specs"] = [
            "Water Resistant",
            "water resistant",
            " 40 litre capacity ",
        ]

        identity = canonical_identity(record)

        self.assertEqual(identity["verified_asin"], "B0ABC12345")
        self.assertEqual(identity["amazon_brand"], "Example Brand")
        self.assertEqual(
            identity["amazon_key_specs"],
            ["40 litre capacity", "water resistant"],
        )


if __name__ == "__main__":
    unittest.main()
