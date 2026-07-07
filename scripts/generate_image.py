#!/usr/bin/env python3
"""
Daily Deal Finder — Sekil Generatoru (CLI)

Platformalar:
  website   — Mehsul sehifesi (1024x1024)
  pinterest — Pinterest Pin (1000x1500)
  social    — Sosial media OG (1200x630)

Istifade:
  python3 scripts/generate_image.py --test
  python3 scripts/generate_image.py --product camp-001 --platform website
  python3 scripts/generate_image.py --all --platform website
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# .env yukle
ENV_PATH = os.path.join(ROOT, ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

from scripts.image_engine.website import WebsiteProductGenerator
from scripts.image_engine.pinterest import PinterestPinGenerator
from scripts.image_engine.social import SocialMediaGenerator

GENERATORS = {
    "website": WebsiteProductGenerator,
    "pinterest": PinterestPinGenerator,
    "social": SocialMediaGenerator,
}

OUTPUT_DIRS = {
    "website": os.path.join(ROOT, "assets", "products"),
    "pinterest": os.path.join(ROOT, "assets", "pinterest"),
    "social": os.path.join(ROOT, "assets", "social"),
}


def load_products():
    path = os.path.join(ROOT, "data", "products.json")
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="AI Product Image Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true", help="Test: 1 sekil")
    group.add_argument("--product", type=str, help="Mehsul ID (mes: camp-001)")
    group.add_argument("--all", action="store_true", help="Butun mehsullar")
    parser.add_argument(
        "--platform",
        choices=["website", "pinterest", "social"],
        default="website",
        help="Platforma (default: website)",
    )
    args = parser.parse_args()

    gen_cls = GENERATORS[args.platform]
    gen = gen_cls()
    out_dir = OUTPUT_DIRS[args.platform]
    os.makedirs(out_dir, exist_ok=True)

    if args.test:
        prompt = (
            "Professional product photo of camping gear, clean natural "
            "background, soft studio lighting, Pinterest-friendly, realistic"
        )
        out = os.path.join(out_dir, f"test-{args.platform}.webp")
        ok = gen.generate(prompt, out)
        print(f"📸 {out}" if ok else "❌ Test alinmadi")
        return 0 if ok else 1

    products = load_products()["products"]

    if args.product:
        prod = next((p for p in products if p["id"] == args.product), None)
        if not prod:
            print(f"❌ Mehsul tapilmadi: {args.product}")
            return 1
        targets = [prod]
    else:
        targets = products

    ok = 0
    for p in targets:
        prompt = gen.build_prompt(p)
        suffix = {"pinterest": "-pin", "social": "-og"}.get(args.platform, "")
        filename = f"{p['id']}{suffix}.webp"
        out = os.path.join(out_dir, filename)
        if gen.generate(prompt, out):
            ok += 1

    print(f"\n✅ {ok}/{len(targets)} sekil ({args.platform})")
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
