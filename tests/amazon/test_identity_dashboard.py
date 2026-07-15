import unittest

from scripts.amazon.identity_dashboard import (
    build_dashboard,
    is_publish_ready,
    is_search_fallback,
    is_verified,
)


class TestIdentityDashboard(unittest.TestCase):
    def test_verified_product_is_detected(self):
        product = {
            "identity_locked": True,
            "verification_status": "verified",
            "verified_asin": "B094G4Y1K3",
            "amazon_link_type": "product",
        }

        self.assertTrue(is_verified(product))

    def test_search_fallback_is_detected(self):
        product = {
            "amazon_asin": "s?k=camping+chair",
            "amazon_link_type": "search",
        }

        self.assertTrue(is_search_fallback(product))

    def test_publish_ready_requires_verified_identity(self):
        product = {
            "active": True,
            "identity_locked": True,
            "verification_status": "verified",
            "verified_asin": "B094G4Y1K3",
            "amazon_link_type": "product",
            "image": "assets/products/camp-014.webp",
            "seo_title": "Mobicool ME24",
            "seo_description": "Verified product",
        }

        self.assertTrue(is_publish_ready(product))

    def test_unverified_product_is_not_publish_ready(self):
        product = {
            "active": True,
            "amazon_asin": "s?k=camping+chair",
            "amazon_link_type": "search",
            "image": "assets/products/camp-002.webp",
            "seo_title": "Camping chair",
            "seo_description": "Search product",
        }

        self.assertFalse(is_publish_ready(product))

    def test_dashboard_counts_products(self):
        products = [
            {
                "id": "camp-001",
                "active": True,
                "identity_locked": True,
                "verification_status": "verified",
                "verified_asin": "B0BS954M37",
                "amazon_link_type": "product",
                "image": "assets/products/camp-001.webp",
                "seo_title": "Coleman tent",
                "seo_description": "Verified tent",
            },
            {
                "id": "camp-002",
                "active": True,
                "amazon_asin": "s?k=family+tent",
                "amazon_link_type": "search",
            },
        ]

        dashboard = build_dashboard(products)

        self.assertEqual(dashboard["total"], 2)
        self.assertEqual(dashboard["verified"], 1)
        self.assertEqual(dashboard["search_fallback"], 1)
        self.assertEqual(dashboard["publish_ready"], 1)
        self.assertEqual(dashboard["not_ready"], 1)
        self.assertEqual(dashboard["coverage"], 50.0)


if __name__ == "__main__":
    unittest.main()
