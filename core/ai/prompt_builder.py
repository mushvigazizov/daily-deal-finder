def build_product_prompt(product):
    title = product.get("title", "")
    brand = product.get("brand", "")
    category = product.get("category", "")
    subcategory = product.get("subcategory", "")
    features = product.get("features", [])

    if not isinstance(features, list):
        features = []

    feature_text = "\n".join(f"- {f}" for f in features)

    return f"""
You are an expert German affiliate content writer.

Write high-quality content for this product.

Product:
Title: {title}
Brand: {brand}
Category: {category}
Subcategory: {subcategory}

Features:
{feature_text}

Return the result as JSON with exactly these fields:

seo_title
seo_description
pinterest_title
pinterest_description
buying_angle

Requirements:

- Natural German
- SEO optimized
- No fake claims
- No exaggerated marketing
- Maximum 160 characters for seo_description
- Pinterest description should be engaging
"""
