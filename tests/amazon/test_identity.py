import unittest

from core.amazon.identity import audit_product_identity, is_valid_asin


class TestAmazonIdentity(unittest.TestCase):
    def test_valid_asin(self):
        self.assertTrue(is_valid_asin("B00BM7A3R0"))
        self.assertTrue(is_valid_asin("b00bm7a3r0"))

    def test_invalid_asin(self):
        self.assertFalse(is_valid_asin(""))
        self.assertFalse(is_valid_asin("s?k=product"))
        self.assertFalse(is_valid_asin("B00SHORT"))
        self.assertFalse(is_valid_asin("B00BM7A3R!"))

    def test_search_product(self):
        result = audit_product_identity(
            {
                "id": "camp-test",
                "amazon_link_type": "search",
                "amazon_asin": "s?k=test",
            }
        )

        self.assertEqual(result.status, "search")
        self.assertTrue(result.needs_search)
        self.assertFalse(result.is_verified)

    def test_product_needing_review(self):
        result = audit_product_identity(
            {
                "id": "camp-test",
                "amazon_link_type": "product",
                "amazon_asin": "B00BM7A3R0",
                "verified_amazon_url": "https://www.amazon.de/dp/B00BM7A3R0",
                "asin_verified": True,
            }
        )

        self.assertEqual(result.status, "review")
        self.assertTrue(result.needs_review)
        self.assertIn("missing amazon_product_title", result.issues)
        self.assertIn("missing amazon_brand", result.issues)
        self.assertIn("missing amazon_model", result.issues)
        self.assertIn(
            "verification_status must be verified",
            result.issues,
        )

    def test_fully_verified_product(self):
        result = audit_product_identity(
            {
                "id": "camp-test",
                "amazon_link_type": "product",
                "amazon_asin": "B00BM7A3R0",
                "verified_amazon_url": "https://www.amazon.de/dp/B00BM7A3R0",
                "asin_verified": True,
                "amazon_product_title": "Coleman Test Tent",
                "amazon_brand": "Coleman",
                "amazon_model": "Test Tent",
                "verification_status": "verified",
            }
        )

        self.assertEqual(result.status, "verified")
        self.assertTrue(result.is_verified)
        self.assertEqual(result.issues, ())

    def test_mismatched_verified_url(self):
        result = audit_product_identity(
            {
                "id": "camp-test",
                "amazon_link_type": "product",
                "amazon_asin": "B00BM7A3R0",
                "verified_amazon_url": "https://www.amazon.de/dp/B013UM88CQ",
                "asin_verified": True,
                "amazon_product_title": "Coleman Test Tent",
                "amazon_brand": "Coleman",
                "amazon_model": "Test Tent",
                "verification_status": "verified",
            }
        )

        self.assertEqual(result.status, "review")
        self.assertIn(
            "verified_amazon_url does not match amazon_asin",
            result.issues,
        )


if __name__ == "__main__":
    unittest.main()
