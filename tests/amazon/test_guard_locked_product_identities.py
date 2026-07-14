import unittest

from core.amazon.identity_lock import compute_identity_hash
from scripts.amazon.guard_locked_product_identities import (
    IdentityGuardError,
    guard_locked_identities,
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
        "amazon_product_title": (
            "Example Outdoor Product"
        ),
        "amazon_brand": "Example",
        "amazon_model": "Model 100",
        "amazon_size": "40 L",
        "amazon_color": "Black",
        "amazon_key_specs": [
            "Water resistant",
            "40 litre capacity",
        ],
        "verification_status": "verified",
        "verification_source": (
            "manual_amazon_de_review"
        ),
        "identity_locked": True,
    }
    record["identity_hash"] = compute_identity_hash(
        record
    )
    return record


def matching_product(record):
    asin = record["verified_asin"]
    url = record["verified_amazon_url"]

    return {
        "id": record["id"],
        "title": "Website Product",
        "amazon_asin": asin,
        "amazon_url": url,
        "amazon_link_type": "product",
        "verified_asin": asin,
        "verified_amazon_url": url,
        "asin_verified": True,
        "amazon_product_title": record[
            "amazon_product_title"
        ],
        "amazon_brand": record["amazon_brand"],
        "amazon_model": record["amazon_model"],
        "amazon_size": record["amazon_size"],
        "amazon_color": record["amazon_color"],
        "amazon_key_specs": record[
            "amazon_key_specs"
        ],
        "verification_status": record[
            "verification_status"
        ],
        "verification_source": record[
            "verification_source"
        ],
        "identity_hash": record["identity_hash"],
        "identity_locked": True,
        "asin_verified_at": (
            "2026-07-14T12:00:00Z"
        ),
        "identity_applied_at": (
            "2026-07-14T12:00:00Z"
        ),
    }


class TestGuardLockedProductIdentities(
    unittest.TestCase
):
    def test_matching_locked_identity_passes(self):
        record = locked_record()
        payload = {
            "products": [
                matching_product(record)
            ]
        }

        verified = guard_locked_identities(
            payload,
            [record],
        )

        self.assertEqual(
            verified,
            ["camp-test"],
        )

    def test_changed_model_is_blocked(self):
        record = locked_record()
        product = matching_product(record)
        product["amazon_model"] = "Wrong Model"

        with self.assertRaisesRegex(
            IdentityGuardError,
            "amazon_model mismatch",
        ):
            guard_locked_identities(
                {"products": [product]},
                [record],
            )

    def test_changed_asin_is_blocked(self):
        record = locked_record()
        product = matching_product(record)
        product["amazon_asin"] = "B0WRONG123"

        with self.assertRaisesRegex(
            IdentityGuardError,
            "amazon_asin mismatch",
        ):
            guard_locked_identities(
                {"products": [product]},
                [record],
            )

    def test_search_link_type_is_blocked(self):
        record = locked_record()
        product = matching_product(record)
        product["amazon_link_type"] = "search"

        with self.assertRaisesRegex(
            IdentityGuardError,
            "amazon_link_type mismatch",
        ):
            guard_locked_identities(
                {"products": [product]},
                [record],
            )

    def test_changed_registry_hash_is_blocked(self):
        record = locked_record()
        product = matching_product(record)

        record["amazon_model"] = "Tampered Model"

        with self.assertRaisesRegex(
            IdentityGuardError,
            "identity_hash mismatch",
        ):
            guard_locked_identities(
                {"products": [product]},
                [record],
            )

    def test_fake_product_lock_is_blocked(self):
        product = {
            "id": "camp-fake",
            "identity_locked": True,
        }

        with self.assertRaisesRegex(
            IdentityGuardError,
            "product claims a locked identity",
        ):
            guard_locked_identities(
                {"products": [product]},
                [],
            )

    def test_timestamps_are_not_identity_fields(self):
        record = locked_record()
        product = matching_product(record)

        product["asin_verified_at"] = (
            "2030-01-01T00:00:00Z"
        )
        product["identity_applied_at"] = (
            "2030-01-02T00:00:00Z"
        )

        verified = guard_locked_identities(
            {"products": [product]},
            [record],
        )

        self.assertEqual(
            verified,
            ["camp-test"],
        )


if __name__ == "__main__":
    unittest.main()
