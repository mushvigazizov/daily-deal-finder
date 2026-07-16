#!/usr/bin/env python3

import json
from pathlib import Path

products = json.loads(
    Path("data/products.json").read_text(encoding="utf-8")
)["products"]

print("=" * 110)
print(f"{'ID':8} {'VERIFIED':10} {'LOCKED':8} {'REF':5} {'IMAGE':7} {'TITLE'}")
print("=" * 110)

for p in products:
    pid = p["id"]

    ref = Path(f"data/amazon_reference_images/{pid}.jpg").exists() \
       or Path(f"data/amazon_reference_images/{pid}.png").exists() \
       or Path(f"data/amazon_reference_images/{pid}.webp").exists()

    img = Path(f"assets/products/{pid}.webp").exists()

    print(
        f"{pid:8}"
        f"{str(p.get('verification_status')=='verified'):10}"
        f"{str(p.get('identity_locked') is True):8}"
        f"{str(ref):5}"
        f"{str(img):7}"
        f"{p.get('title','')[:55]}"
    )

print("=" * 110)
