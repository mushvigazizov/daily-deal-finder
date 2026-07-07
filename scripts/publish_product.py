import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd=ROOT):
    print("RUN:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print("FAILED:", " ".join(cmd))
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True)
    args = parser.parse_args()

    product_id = args.product

    run(["python3", "scripts/generate_image.py", "--product", product_id])
    run(["python3", "scripts/sync_product_images.py"])

    image_path = f"assets/products/{product_id}.webp"

    run(["git", "add", "data/products.json", image_path, "scripts/publish_product.py"])
    run(["git", "commit", "-m", f"Add AI image for {product_id}"])

    print("")
    print("✅ READY TO PUSH")
    print("Exit container, then on host run:")
    print("cd /docker/hermes-agent-yivo/data/daily-deal-finder")
    print("git push origin main")

if __name__ == "__main__":
    main()
