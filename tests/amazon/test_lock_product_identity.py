import unittest

from scripts.amazon.lock_product_identity import lock_product


def valid_registry_record():
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
        "status": "needs_verification",
    }


class TestLockProductIdentity(unittest.TestCase):
    def test_valid_record_is_locked(self):
        registry = [valid_registry_record()]

        success, issues = lock_product(
            registry,
            "camp-test",
        )

        self.assertTrue(success)
        self.assertEqual(issues, ())

        record = registry[0]

        self.assertTrue(record["identity_locked"])
        self.assertEqual(len(record["identity_hash"]), 64)
        self.assertEqual(record["status"], "verified")
        self.assertEqual(
            record["verification_status"],
            "verified",
        )

    def test_invalid_record_is_not_locked(self):
        record = valid_registry_record()
        record["amazon_model"] = ""
        registry = [record]

        success, issues = lock_product(
            registry,
            "camp-test",
        )

        self.assertFalse(success)
        self.assertIn("missing amazon_model", issues)
        self.assertNotIn("identity_hash", record)
        self.assertNotIn("identity_locked", record)

    def test_unknown_product_is_rejected(self):
        success, issues = lock_product(
            [],
            "camp-missing",
        )

        self.assertFalse(success)
        self.assertEqual(
            issues,
            ("product not found: camp-missing",),
        )


if __name__ == "__main__":
    unittest.main()
