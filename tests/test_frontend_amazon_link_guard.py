from pathlib import Path
import unittest


PRODUCTS_JS = Path("js/products.js")


class FrontendAmazonLinkGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PRODUCTS_JS.read_text(encoding="utf-8")

    def test_legacy_amazon_url_builder_is_removed(self):
        self.assertNotIn(
            "function buildAmazonUrl",
            self.source,
        )

    def test_search_fallback_logic_is_removed(self):
        forbidden_fragments = (
            "startsWith('s?k=')",
            'startsWith("s?k=")',
            "buildAmazonUrl(p.amazon_asin)",
            "buildAmazonUrl(product.amazon_asin)",
        )

        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, self.source)

    def test_verified_identity_guard_is_required(self):
        required_fragments = (
            "function getVerifiedAmazonUrl(product)",
            "product.identity_locked === true",
            'verificationStatus === "verified"',
            'linkType === "product"',
            "verifiedUrl === expectedUrl",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

    def test_buttons_use_verified_product_guard(self):
        self.assertIn(
            '${renderAmazonButton(p)}',
            self.source,
        )
        self.assertIn(
            '${renderAmazonButton(product, "button cta")}',
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
