import unittest

from scripts.project_health_check import (
    is_missing_base_field,
    is_verified_product,
)


class TestProjectHealthCheck(unittest.TestCase):
    def test_active_false_is_valid(self):
        product = {"active": False}

        self.assertFalse(
            is_missing_base_field(product, "active")
        )

    def test_active_must_be_boolean(self):
        self.assertTrue(
            is_missing_base_field({"active": ""}, "active")
        )
        self.assertTrue(
            is_missing_base_field({"active": 1}, "active")
        )
        self.assertTrue(
            is_missing_base_field({}, "active")
        )

    def test_empty_required_text_field_is_missing(self):
        self.assertTrue(
            is_missing_base_field({"title": ""}, "title")
        )

    def test_nonempty_required_field_is_valid(self):
        self.assertFalse(
            is_missing_base_field(
                {"title": "Mobicool ME24"},
                "title",
            )
        )

    def test_locked_verified_product_is_detected(self):
        product = {
            "identity_locked": True,
            "verification_status": "verified",
            "verified_asin": "B094G4Y1K3",
        }

        self.assertTrue(is_verified_product(product))

    def test_unlocked_product_is_not_verified(self):
        product = {
            "identity_locked": False,
            "verification_status": "verified",
            "verified_asin": "B094G4Y1K3",
        }

        self.assertFalse(is_verified_product(product))

    def test_verified_product_does_not_require_size_or_color(self):
        product = {
            "identity_locked": True,
            "verification_status": "verified",
            "verified_asin": "B094G4Y1K3",
            "amazon_size": "",
            "amazon_color": "",
        }

        self.assertTrue(is_verified_product(product))


if __name__ == "__main__":
    unittest.main()
