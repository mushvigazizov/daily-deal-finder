from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.product_factory.factory import (
    ProductFactoryError,
    canonical_amazon_url,
    create_preview,
    extract_asin,
)


class ProductFactoryTests(unittest.TestCase):
    def test_extract_asin_from_dp_url(self) -> None:
        self.assertEqual(
            extract_asin(
                "https://www.amazon.de/example/dp/B0F749Z97T/ref=test"
            ),
            "B0F749Z97T",
        )

    def test_extract_asin_from_gp_product_url(self) -> None:
        self.assertEqual(
            extract_asin(
                "https://www.amazon.de/gp/product/B0DJPS3YTS"
            ),
            "B0DJPS3YTS",
        )

    def test_invalid_url_is_rejected(self) -> None:
        with self.assertRaises(ProductFactoryError):
            extract_asin(
                "https://www.amazon.de/s?k=camping"
            )

    def test_canonical_url(self) -> None:
        self.assertEqual(
            canonical_amazon_url("B081KCJ9B1"),
            "https://www.amazon.de/dp/B081KCJ9B1",
        )

    def test_create_preview_does_not_modify_products(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            data_dir.mkdir(parents=True)

            products_path = data_dir / "products.json"
            products_path.write_text(
                json.dumps(
                    {
                        "products": [
                            {
                                "id": "camp-013",
                                "title": "Existing product",
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            before = products_path.read_bytes()

            preview = create_preview(
                root=root,
                product_id="camp-013",
                amazon_url=(
                    "https://www.amazon.de/example/dp/B0F749Z97T"
                ),
            )

            after = products_path.read_bytes()

            self.assertEqual(before, after)
            self.assertTrue((preview / "manifest.json").exists())
            self.assertTrue((preview / "identity.json").exists())

            manifest = json.loads(
                (preview / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertFalse(manifest["live_site_modified"])
            self.assertTrue(
                manifest["requires_human_approval"]
            )


if __name__ == "__main__":
    unittest.main()
