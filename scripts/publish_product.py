import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "data" / "products.json"
ASSETS_DIR = ROOT / "assets" / "products"

def run(cmd):
    print("RUN:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print("FAILED:", " ".join(cmd))
        sys.exit(result.returncode)

def load_products():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    return data["products"]

def has_ai_image(product_id):
    return (ASSETS_DIR / f"{product_id}.webp").exists()

def products_missing_images():
    missing = []
    for p in load_products():
        pid = p.get("id")
        if pid and not has_ai_image(pid):
            missing.append(pid)
    return missing

def publish_one(product_id):
    run(["python3", "scripts/generate_image.py", "--product", product_id])
    run(["python3", "scripts/sync_product_images.py"])

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product", type=str)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Max products for --all")
    args = parser.parse_args()

    if args.product:
        product_ids = [args.product]
    else:
        product_ids = products_missing_images()
        if args.limit and args.limit > 0:
            product_ids = product_ids[:args.limit]

    if not product_ids:
        print("✅ No missing product images.")
        return

    print("Products to publish:", ", ".join(product_ids))

    for pid in product_ids:
        publish_one(pid)

    run(["git", "add", "data/products.json", "assets/products", "scripts/publish_product.py", "scripts/sync_product_images.py"])

    if len(product_ids) == 1:
        msg = f"Add AI image for {product_ids[0]}"
    else:
        msg = f"Add AI images for {len(product_ids)} products"

    run(["git", "commit", "-m", msg])

    print("")
    print("✅ READY TO PUSH")
    print("Exit container, then on host run:")
    print("cd /docker/hermes-agent-yivo/data/daily-deal-finder")
    print("git push origin main")

if __name__ == "__main__":
    main()
