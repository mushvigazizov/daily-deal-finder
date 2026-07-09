from core.products import load_product_data, save_product_data
from core.ai.content_engine import generate_content

data = load_product_data()
products = data.get("products", data)

updated = 0

print("=" * 70)
print("AI CONTENT GENERATOR")
print("=" * 70)

for product in products:
    content = generate_content(product)
    product.update(content)
    updated += 1

save_product_data(data)

print(f"Products processed: {updated}")
print("AI CONTENT GENERATION COMPLETED")
