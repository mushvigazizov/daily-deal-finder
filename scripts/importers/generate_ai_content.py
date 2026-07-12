from core.products import load_product_data, save_product_data
from core.ai.content_engine import generate_content

data = load_product_data()
products = data.get("products", data)

updated = 0

print("=" * 70)
print("AI CONTENT GENERATOR")
print("=" * 70)

skipped_verified = 0

for product in products:
    if (
        product.get("asin_verified")
        and product.get("amazon_link_type") == "product"
    ):
        skipped_verified += 1
        continue

    content = generate_content(product)
    product.update(content)
    updated += 1

save_product_data(data)

print(f"Products processed: {updated}")
print(f"Verified products skipped: {skipped_verified}")
print("AI CONTENT GENERATION COMPLETED")
