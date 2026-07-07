import json
from pathlib import Path

products_path = Path("data/products.json")
assets_dir = Path("assets/products")

data = json.loads(products_path.read_text(encoding="utf-8"))
changed = 0

for p in data["products"]:
    pid = p.get("id")
    if not pid:
        continue

    webp = assets_dir / f"{pid}.webp"
    if webp.exists():
        new_image = f"assets/products/{pid}.webp"
        if p.get("image") != new_image:
            p["image"] = new_image
            changed += 1
            print(f"UPDATED {pid} -> {new_image}")

products_path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)

print(f"DONE changed={changed}")
