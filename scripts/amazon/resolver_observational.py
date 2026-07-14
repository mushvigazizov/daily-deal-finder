#!/usr/bin/env python3
"""Observational resolver — prints candidate evaluation without modifying files."""

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from core.amazon.resolver import AmazonIdentityResolver
from core.amazon.io import load_json

PRODUCTS_PATH = PROJECT / "data" / "products.json"
CANDIDATES_DIR = PROJECT / "data" / "amazon_candidates"

resolver = AmazonIdentityResolver()
products_data = load_json(PRODUCTS_PATH)
products = products_data.get("products", products_data)

print("=" * 78)
print("AMAZON IDENTITY RESOLVER — OBSERVATIONAL")
print("=" * 78)

resolved = 0
for product in products:
    pid = product.get("id", "")
    cand_path = CANDIDATES_DIR / f"{pid}.json"
    if not cand_path.exists():
        continue

    candidates_data = load_json(cand_path)
    candidates = candidates_data.get("candidates", candidates_data)
    if not isinstance(candidates, list):
        continue

    result = resolver.resolve(product, candidates)
    resolved += 1

    print()
    print(f"[{pid}] {product.get('title', '')}")
    print(f"  Decision   : {result.decision.value}")
    print(f"  Confidence : {result.confidence:.2f}%")
    best = result.best_candidate
    print(f"  Best ASIN  : {best['asin'] if best else 'N/A'}")
    if best:
        print(f"  Best Title : {best['amazon_product_title']}")
    print(f"  Should Lock: {result.should_lock}")

    if result.reasons:
        for r in result.reasons:
            print(f"  Reason     : {r}")
    if result.errors:
        for e in result.errors:
            print(f"  Error      : {e}")

print()
print(f"Resolved {resolved} products.")
print("READ-ONLY: no project files were changed.")
