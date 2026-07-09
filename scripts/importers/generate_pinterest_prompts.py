import json
from pathlib import Path
from datetime import date

products = json.loads(
    Path("data/products.json").read_text(encoding="utf-8")
)["products"]

prompts = []

print("=" * 70)
print("PINTEREST IMAGE PROMPT GENERATOR")
print("=" * 70)

for product in products:
    prompt = {
        "product_id": product["id"],
        "image": product["image"],
        "style": "Pinterest Vertical 1000x1500",
        "prompt": (
            f"Create a premium Pinterest vertical image for "
            f"'{product['title']}'. "
            "Realistic outdoor lifestyle photography, natural lighting, "
            "professional composition, clean background, high click-through design, "
            "space for title overlay, premium quality, no Amazon logo."
        ),
        "created_at": str(date.today())
    }

    prompts.append(prompt)

output = {
    "_schema": "1.0",
    "_generated_at": str(date.today()),
    "total_prompts": len(prompts),
    "prompts": prompts
}

Path("data/pinterest_prompts.json").write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Prompts generated: {len(prompts)}")
print("PINTEREST PROMPT GENERATION COMPLETED")
