import json
import tempfile
import unittest
from pathlib import Path

from core.amazon.registry import (
    RegistryError,
    get_registry_record,
    index_registry,
    load_registry,
    locked_registry_records,
    validate_registry_uniqueness,
    write_registry_atomic,
)


def registry_record(
    product_id="camp-test",
    asin="B0ABC12345",
    locked=True,
):
    return {
        "id": product_id,
        "verified_asin": asin,
        "identity_locked": locked,
    }


class TestAmazonRegistry(unittest.TestCase):
    def test_load_registry_reads_json_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(
                json.dumps([registry_record()]),
                encoding="utf-8",
            )

            registry = load_registry(path)

        self.assertEqual(len(registry), 1)
        self.assertEqual(registry[0]["id"], "camp-test")

    def test_load_registry_rejects_non_list_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(
                json.dumps({"products": []}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                RegistryError,
                "JSON list",
            ):
                load_registry(path)

    def test_atomic_write_can_be_loaded_again(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            registry = [registry_record()]

            write_registry_atomic(registry, path)
            loaded = load_registry(path)

            self.assertEqual(loaded, registry)
            self.assertFalse(
                path.with_suffix(".json.tmp").exists()
            )

    def test_index_registry_returns_product_mapping(self):
        index = index_registry(
            [
                registry_record("camp-one", "B0ABC12345"),
                registry_record(
                    "camp-two",
                    "B0XYZ67890",
                    locked=False,
                ),
            ]
        )

        self.assertEqual(
            index["camp-one"]["verified_asin"],
            "B0ABC12345",
        )
        self.assertIn("camp-two", index)

    def test_duplicate_product_id_is_rejected(self):
        registry = [
            registry_record("camp-test", "B0ABC12345"),
            registry_record("camp-test", "B0XYZ67890"),
        ]

        with self.assertRaisesRegex(
            RegistryError,
            "duplicate registry product id",
        ):
            validate_registry_uniqueness(registry)

    def test_duplicate_locked_asin_is_rejected(self):
        registry = [
            registry_record("camp-one", "B0ABC12345"),
            registry_record("camp-two", "B0ABC12345"),
        ]

        with self.assertRaisesRegex(
            RegistryError,
            "duplicate locked ASIN",
        ):
            validate_registry_uniqueness(registry)

    def test_duplicate_unlocked_asin_is_allowed(self):
        registry = [
            registry_record(
                "camp-one",
                "B0ABC12345",
                locked=False,
            ),
            registry_record(
                "camp-two",
                "B0ABC12345",
                locked=False,
            ),
        ]

        validate_registry_uniqueness(registry)

    def test_get_registry_record_returns_matching_record(self):
        registry = [
            registry_record("camp-one", "B0ABC12345"),
        ]

        record = get_registry_record(registry, "camp-one")

        self.assertIsNotNone(record)
        self.assertEqual(record["id"], "camp-one")

    def test_get_registry_record_returns_none_for_unknown_id(self):
        record = get_registry_record(
            [registry_record()],
            "camp-missing",
        )

        self.assertIsNone(record)

    def test_locked_registry_records_filters_unlocked_records(self):
        locked = locked_registry_records(
            [
                registry_record(
                    "camp-one",
                    "B0ABC12345",
                    locked=True,
                ),
                registry_record(
                    "camp-two",
                    "B0XYZ67890",
                    locked=False,
                ),
            ]
        )

        self.assertEqual(
            [record["id"] for record in locked],
            ["camp-one"],
        )


if __name__ == "__main__":
    unittest.main()
