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

class ProductFactoryHydrateTests(unittest.TestCase):
    def test_hydrate_verified_locked_product(self):
        from core.product_factory.factory import hydrate_preview

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            (root / "data/product_factory/previews/camp-008").mkdir(
                parents=True
            )
            (root / "data/amazon_reference_images").mkdir(parents=True)
            (
                root
                / "inspection/candidates/website"
            ).mkdir(parents=True)

            products = {
                "products": [
                    {
                        "id": "camp-008",
                        "title": "Berghaus Arrow U30",
                        "verification_status": "verified",
                        "identity_locked": True,
                        "verified_asin": "B0DJPS3YTS",
                        "verified_amazon_url": (
                            "https://www.amazon.de/dp/B0DJPS3YTS"
                        ),
                        "amazon_product_title": "Berghaus Arrow",
                        "amazon_brand": "Berghaus",
                        "amazon_model": "Arrow 30L Pack",
                        "amazon_size": "30 Liter",
                        "amazon_color": "Jet Black",
                        "amazon_key_specs": ["30 Liter"],
                        "identity_hash": "test-hash",
                        "features": [],
                        "tags": [],
                    }
                ]
            }

            (root / "data/products.json").write_text(
                json.dumps(products),
                encoding="utf-8",
            )

            preview = (
                root
                / "data/product_factory/previews/camp-008"
            )
            (preview / "manifest.json").write_text(
                json.dumps(
                    {
                        "status": "draft",
                        "live_site_modified": False,
                        "requires_human_approval": True,
                    }
                ),
                encoding="utf-8",
            )

            (
                root
                / "data/amazon_reference_images/camp-008.jpg"
            ).write_bytes(b"reference")

            (
                root
                / "inspection/candidates/website/camp-008.webp"
            ).write_bytes(b"candidate")

            result = hydrate_preview(
                root=root,
                product_id="camp-008",
            )

            identity = json.loads(
                (result / "identity.json").read_text(
                    encoding="utf-8"
                )
            )
            media = json.loads(
                (result / "media.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(identity["asin"], "B0DJPS3YTS")
            self.assertTrue(identity["identity_locked"])
            self.assertFalse(identity["human_approved"])
            self.assertEqual(media["status"], "candidate_ready")

    def test_hydrate_rejects_unverified_product(self):
        from core.product_factory.factory import (
            ProductFactoryError,
            hydrate_preview,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            preview = (
                root
                / "data/product_factory/previews/camp-004"
            )
            preview.mkdir(parents=True)

            (root / "data/products.json").write_text(
                json.dumps(
                    {
                        "products": [
                            {
                                "id": "camp-004",
                                "verification_status": "draft",
                                "identity_locked": False,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ProductFactoryError):
                hydrate_preview(
                    root=root,
                    product_id="camp-004",
                )

class ProductFactoryApprovalPublishTests(unittest.TestCase):
    def create_ready_preview(self, root: Path) -> Path:
        from core.product_factory.factory import create_preview, hydrate_preview

        (root / "data").mkdir(parents=True, exist_ok=True)
        (root / "data/amazon_reference_images").mkdir(parents=True)
        (root / "inspection/candidates/website").mkdir(parents=True)
        (root / "assets/products").mkdir(parents=True)

        (root / "data/products.json").write_text(
            json.dumps(
                {
                    "products": [
                        {
                            "id": "camp-008",
                            "title": "Berghaus Arrow",
                            "verification_status": "verified",
                            "identity_locked": True,
                            "verified_asin": "B0DJPS3YTS",
                            "verified_amazon_url": (
                                "https://www.amazon.de/dp/B0DJPS3YTS"
                            ),
                            "amazon_product_title": "Berghaus Arrow",
                            "amazon_brand": "Berghaus",
                            "amazon_model": "Arrow 30L",
                            "amazon_size": "30 Liter",
                            "amazon_color": "Jet Black",
                            "amazon_key_specs": ["30 Liter"],
                            "identity_hash": "test-hash",
                            "features": [],
                            "tags": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        (root / "data/amazon_reference_images/camp-008.jpg").write_bytes(
            b"reference"
        )
        (
            root
            / "inspection/candidates/website/camp-008.webp"
        ).write_bytes(b"new-candidate")

        create_preview(
            root=root,
            product_id="camp-008",
            amazon_url="https://www.amazon.de/dp/B0DJPS3YTS",
            reference_image=str(
                root
                / "data/amazon_reference_images/camp-008.jpg"
            ),
        )

        return hydrate_preview(
            root=root,
            product_id="camp-008",
        )

    def test_publish_is_blocked_without_approval(self):
        from core.product_factory.factory import (
            ProductFactoryError,
            publish_preview,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_ready_preview(root)

            with self.assertRaises(ProductFactoryError):
                publish_preview(
                    root=root,
                    product_id="camp-008",
                )

    def test_approve_does_not_modify_live_image(self):
        from core.product_factory.factory import approve_preview

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_ready_preview(root)

            live = root / "assets/products/camp-008.webp"
            live.write_bytes(b"old-live")

            approve_preview(
                root=root,
                product_id="camp-008",
                approved_by="Mushvig",
                approval_note="Visual match confirmed.",
            )

            self.assertEqual(live.read_bytes(), b"old-live")

    def test_publish_approved_candidate_and_create_backup(self):
        from core.product_factory.factory import (
            approve_preview,
            publish_preview,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_ready_preview(root)

            live = root / "assets/products/camp-008.webp"
            live.write_bytes(b"old-live")

            approve_preview(
                root=root,
                product_id="camp-008",
                approved_by="Mushvig",
            )

            destination = publish_preview(
                root=root,
                product_id="camp-008",
            )

            backup = (
                root
                / "assets/products/camp-008.webp.factory-backup"
            )

            self.assertEqual(
                destination.read_bytes(),
                b"new-candidate",
            )
            self.assertEqual(
                backup.read_bytes(),
                b"old-live",
            )
