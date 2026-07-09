import json
from pathlib import Path
from datetime import date

PROMPTS_FILE = Path("data/pinterest_prompts.json")
OUTPUT_DIR = Path("assets/pinterest")

print("=" * 70)
print("PINTEREST IMAGE GENERATOR")
print("=" * 70)

if not PROMPTS_FILE.exists():
    raise FileNotFoundError(f"{PROMPTS_FILE} not found")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
prompts = data.get("prompts", [])

generated = 0
skipped = 0

for item in prompts:
    product_id = item["product_id"]
    image_path = OUTPUT_DIR / f"{product_id}.webp"

    if image_path.exists():
        print(f"[SKIP] {product_id} already exists")
        skipped += 1
        continue

    print(f"[READY] {product_id}")
    print(f"        Prompt: {item['prompt'][:80]}...")

    # OpenAI GPT Image API burada əlavə olunacaq.
    # Növbəti mərhələdə yaradılan şəkil image_path ünvanına yazılacaq.

    generated += 1

print()
print("=" * 70)
print(f"Prompts loaded : {len(prompts)}")
print(f"Ready to create: {generated}")
print(f"Skipped        : {skipped}")
print(f"Output folder  : {OUTPUT_DIR}")
print(f"Generated at   : {date.today()}")
print("=" * 70)
