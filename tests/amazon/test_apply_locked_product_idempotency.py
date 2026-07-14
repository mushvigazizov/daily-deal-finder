from __future__ import annotations

import unittest

from scripts.amazon.apply_locked_product_identities import apply_identity_to_product


class TestApplyLockedProductIdentityIdempotency(unittest.TestCase):
    def test_reapplying_same_locked_identity_does_not_touch_timestamps(self) -> None:
        product = {
            "id": "camp-001",
            "amazon_asin": "B0BS954M37",
            "verified_asin": "B0BS954M37",
            "verified_amazon_url": "https://www.amazon.de/dp/B0BS954M37",
            "amazon_url": "https://www.amazon.de/dp/B0BS954M37",
            "amazon_link_type": "product",
            "asin_verified": True,
            "asin_verified_at": "2026-07-14T17:10:44Z",
            "amazon_product_title": "Coleman Darwin 2",
            "amazon_brand": "Coleman",
            "amazon_model": "Darwin 2",
            "amazon_size": "",
            "amazon_color": "",
            "amazon_key_specs": ["2-person", "waterproof"],
            "verification_status": "verified",
            "verification_source": "amazon_de_manual_review",
            "identity_hash": "caa0f620c3bc496fcc3885498467f65ce5bf94a53cb48afcb2a8117c245b06b8",
            "identity_locked": True,
            "identity_applied_at": "2026-07-14T17:10:44Z",
        }

        record = {
            "id": "camp-001",
            "verified_asin": "B0BS954M37",
            "verified_amazon_url": "https://www.amazon.de/dp/B0BS954M37",
            "amazon_product_title": "Coleman Darwin 2",
            "amazon_brand": "Coleman",
            "amazon_model": "Darwin 2",
            "amazon_size": "",
            "amazon_color": "",
            "amazon_key_specs": ["2-person", "waterproof"],
            "verification_status": "verified",
            "verification_source": "amazon_de_manual_review",
            "identity_hash": "caa0f620c3bc496fcc3885498467f65ce5bf94a53cb48afcb2a8117c245b06b8",
            "identity_locked": True,
        }

        changed = apply_identity_to_product(
            product,
            record,
            applied_at="2026-07-14T18:55:53Z",
        )

        self.assertFalse(changed)
        self.assertEqual(product["asin_verified_at"], "2026-07-14T17:10:44Z")
        self.assertEqual(product["identity_applied_at"], "2026-07-14T17:10:44Z")


if __name__ == "__main__":
    unittest.main()
