from __future__ import annotations

import unittest

from scripts.importers.product_quality_validator import validate_product


def base_product() -> dict:
    return {
        "id": "camp-001",
        "title": "Coleman Tent",
        "category": "camping",
        "amazon_asin": "B0BS954M37",
        "amazon_link_type": "product",
        "amazon_url": "https://www.amazon.de/dp/B0BS954M37",
        "verified_amazon_url": "https://www.amazon.de/dp/B0BS954M37",
        "asin_verified": True,
        "asin_verified_at": "2026-07-14T17:10:44Z",
        "verification_status": "verified",
        "verification_source": "manual",
        "image": "assets/products/camp-001.webp",
        "seo_title": "Coleman Tent",
        "seo_description": "Tent description",
        "pinterest_title": "Coleman Tent",
        "pinterest_description": "Tent description",
    }


class TestProductQualityValidator(unittest.TestCase):
    def test_verified_product_is_valid(self) -> None:
        errors, warnings = validate_product(base_product())

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_search_product_produces_warning(self) -> None:
        product = base_product()
        product["amazon_asin"] = "s?k=Coleman+Tent"
        product["amazon_link_type"] = "search"

        errors, warnings = validate_product(product)

        self.assertEqual(errors, [])
        self.assertEqual(
            warnings,
            ["search fallback link still used"],
        )

    def test_invalid_verified_url_is_rejected(self) -> None:
        product = base_product()
        product["verified_amazon_url"] = (
            "https://www.amazon.de/dp/B000000000"
        )

        errors, _warnings = validate_product(product)

        self.assertIn(
            "verified_amazon_url does not match amazon_asin",
            errors,
        )

    def test_unverified_product_link_is_rejected(self) -> None:
        product = base_product()
        product["asin_verified"] = False
        product["verification_status"] = "needs_verification"

        errors, _warnings = validate_product(product)

        self.assertIn("asin_verified must be true", errors)
        self.assertIn(
            "verification_status must be verified",
            errors,
        )

    def test_invalid_category_is_rejected(self) -> None:
        product = base_product()
        product["category"] = "unknown"

        errors, _warnings = validate_product(product)

        self.assertIn("invalid category: unknown", errors)

    def test_missing_required_field_is_rejected(self) -> None:
        product = base_product()
        product["seo_title"] = ""

        errors, _warnings = validate_product(product)

        self.assertIn(
            "missing required fields: seo_title",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
