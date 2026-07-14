import unittest

from core.amazon.identity_lock import compute_identity_hash
from scripts.amazon.apply_locked_product_identities import (
    ApplyLockedIdentityError,
    apply_identity_to_product,
    prepare_application,
)


def locked_record(
    product_id="camp-test",
    asin="B0ABC12345",
):
    record = {
        "id": product_id,
        "verified_asin": asin,
        "verified_amazon_url": (
            f"https://www.amazon.de/dp/{asin}"
        ),
        "amazon_product_title": "Example Outdoor Product",
        "amazon_brand": "Example",
        "amazon_model": "Model 100",
        "amazon_size": "40 L",
        "amazon_color": "Black",
        "amazon_key_specs": [
            "Water resistant",
            "40 litre capacity",
        ],
        "verification_status": "verified",
        "verification_source": "manual_amazon_de_review",
        "identity_locked": True,
    }
    record["identity_hash"] = compute_identity_hash(record)
    return record


def products_payload():
    return {
        "products": [
            {
                "id": "camp-test",
                "title": "Website Product",
                "amazon_asin": "s?k=Website%20Product",
                "amazon_link_type": "search",
            }
        ]
    }


class TestApplyLockedProductIdentities(unittest.TestCase):
    def test_locked_identity_is_applied(self):
        payload, changed, unchanged = prepare_application(
            products_payload(),
            [locked_record()],
            applied_at="2026-07-14T12:00:00Z",
        )

        product = payload["products"][0]

        self.assertEqual(changed, ["camp-test"])
        self.assertEqual(unchanged, [])
        self.assertEqual(
            product["amazon_asin"],
            "B0ABC12345",
        )
        self.assertEqual(
            product["verified_amazon_url"],
            "https://www.amazon.de/dp/B0ABC12345",
        )
        self.assertEqual(
            product["amazon_link_type"],
            "product",
        )
        self.assertTrue(product["asin_verified"])
        self.assertTrue(product["identity_locked"])
        self.assertEqual(
            product["amazon_brand"],
            "Example",
        )
        self.assertEqual(
            product["identity_applied_at"],
            "2026-07-14T12:00:00Z",
        )

    def test_unlocked_registry_record_is_ignored(self):
        record = locked_record()
        record["identity_locked"] = False

        payload, changed, unchanged = prepare_application(
            products_payload(),
            [record],
            applied_at="2026-07-14T12:00:00Z",
        )

        product = payload["products"][0]

        self.assertEqual(changed, [])
        self.assertEqual(unchanged, [])
        self.assertEqual(
            product["amazon_link_type"],
            "search",
        )

    def test_changed_identity_hash_is_rejected(self):
        record = locked_record()
        record["amazon_model"] = "Different Model"

        with self.assertRaisesRegex(
            ApplyLockedIdentityError,
            "identity_hash mismatch",
        ):
            prepare_application(
                products_payload(),
                [record],
                applied_at="2026-07-14T12:00:00Z",
            )

    def test_unknown_locked_product_is_rejected(self):
        record = locked_record(product_id="camp-unknown")

        with self.assertRaisesRegex(
            ApplyLockedIdentityError,
            "product does not exist",
        ):
            prepare_application(
                products_payload(),
                [record],
                applied_at="2026-07-14T12:00:00Z",
            )

    def test_duplicate_locked_asin_is_rejected(self):
        payload = {
            "products": [
                {
                    "id": "camp-one",
                    "amazon_link_type": "search",
                },
                {
                    "id": "camp-two",
                    "amazon_link_type": "search",
                },
            ]
        }

        registry = [
            locked_record(
                product_id="camp-one",
                asin="B0ABC12345",
            ),
            locked_record(
                product_id="camp-two",
                asin="B0ABC12345",
            ),
        ]

        with self.assertRaisesRegex(
            ApplyLockedIdentityError,
            "duplicate locked ASIN",
        ):
            prepare_application(
                payload,
                registry,
                applied_at="2026-07-14T12:00:00Z",
            )

    def test_duplicate_product_id_is_rejected(self):
        payload = {
            "products": [
                {"id": "camp-test"},
                {"id": "camp-test"},
            ]
        }

        with self.assertRaisesRegex(
            ApplyLockedIdentityError,
            "duplicate product id",
        ):
            prepare_application(
                payload,
                [locked_record()],
                applied_at="2026-07-14T12:00:00Z",
            )

    def test_apply_is_idempotent_for_same_timestamp(self):
        product = products_payload()["products"][0]
        record = locked_record()

        first = apply_identity_to_product(
            product,
            record,
            applied_at="2026-07-14T12:00:00Z",
        )
        second = apply_identity_to_product(
            product,
            record,
            applied_at="2026-07-14T12:00:00Z",
        )

        self.assertTrue(first)
        self.assertFalse(second)


if __name__ == "__main__":
    unittest.main()
