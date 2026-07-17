#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.product_factory.factory import (  # noqa: E402
    ProductFactoryError,
    create_preview,
    hydrate_preview,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Daily Deal Finder Product Factory. "
            "Preview-only V1: never modifies the live catalog."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create_parser = subparsers.add_parser(
        "create",
        help="Create an isolated product preview package.",
    )
    create_parser.add_argument(
        "--product-id",
        required=True,
    )
    create_parser.add_argument(
        "--amazon-url",
        required=True,
    )
    create_parser.add_argument(
        "--reference-image",
    )

    hydrate_parser = subparsers.add_parser(
        "hydrate",
        help="Fill a preview from a verified and locked product.",
    )
    hydrate_parser.add_argument(
        "--product-id",
        required=True,
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect an existing preview package.",
    )
    inspect_parser.add_argument(
        "--product-id",
        required=True,
    )

    args = parser.parse_args()

    if args.command == "create":
        preview = create_preview(
            root=ROOT,
            product_id=args.product_id,
            amazon_url=args.amazon_url,
            reference_image=args.reference_image,
        )

        manifest = json.loads(
            (preview / "manifest.json").read_text(encoding="utf-8")
        )

        print("=" * 78)
        print("PRODUCT FACTORY PREVIEW CREATED")
        print("=" * 78)
        print("Product ID      :", manifest["product_id"])
        print("ASIN            :", manifest["asin"])
        print("Amazon URL      :", manifest["canonical_amazon_url"])
        print("Preview         :", preview.relative_to(ROOT))
        print("Live modified   :", manifest["live_site_modified"])
        print("Approval needed :", manifest["requires_human_approval"])
        print("=" * 78)
        return 0

    if args.command == "hydrate":
        preview = hydrate_preview(
            root=ROOT,
            product_id=args.product_id,
        )

        print("=" * 78)
        print("PRODUCT FACTORY PREVIEW HYDRATED")
        print("=" * 78)
        print("Product ID :", args.product_id)
        print("Preview    :", preview.relative_to(ROOT))
        print("Live site  : unchanged")
        print("Approval   : required")
        print("=" * 78)
        return 0

    preview = (
        ROOT
        / "data"
        / "product_factory"
        / "previews"
        / args.product_id
    )

    if not preview.exists():
        raise ProductFactoryError(
            f"Preview was not found: {args.product_id}"
        )

    print("=" * 78)
    print("PRODUCT FACTORY PREVIEW")
    print("=" * 78)

    for filename in [
        "manifest.json",
        "identity.json",
        "product.json",
        "media.json",
        "approval.json",
    ]:
        path = preview / filename
        print(f"\n----- {filename} -----")
        print(path.read_text(encoding="utf-8").rstrip())

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProductFactoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
