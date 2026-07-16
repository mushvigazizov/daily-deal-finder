def _product_context(product: dict) -> tuple[str, str]:
    title = str(
        product.get("amazon_product_title")
        or product.get("title")
        or ""
    ).strip()

    category = str(
        product.get("subcategory")
        or product.get("category")
        or ""
    ).strip()

    return title, category


def build_website_prompt(product: dict) -> str:
    title, category = _product_context(product)

    return f"""
Use the uploaded Amazon product image as the authoritative product reference.

Product title: {title}
Category: {category}

PRODUCT IDENTITY:
- Show exactly the same product model from the uploaded image.
- Do not create a different product or alternative design.
- Preserve its exact silhouette, proportions, colours, materials, doors,
  openings, poles, seams, panels and visible construction.
- The product must remain immediately recognizable as the original item.

COMPOSITION:
- Show the complete product fully inside the frame.
- Do not crop, cut off, hide or cover any part of it.
- Leave comfortable space around the entire product.
- Make it the clear hero and dominant subject.
- Use a natural three-quarter product-photography angle.

LIFESTYLE INTEGRATION:
- Place the exact product naturally in a fresh, beautiful lifestyle scene
  that genuinely matches the category.
- Integrate it with realistic contact shadows, ambient light, reflections,
  perspective and surrounding colours.
- It must look physically present and professionally photographed there.
- It must not look pasted, composited, floating or artificially inserted.
- Use bright natural daylight or warm golden-hour lighting.
- Keep the product itself clearly illuminated and highly visible.

VISUAL STYLE:
- Premium Pinterest-inspired outdoor lifestyle photography.
- Aspirational, polished, warm and visually rich.
- High-end DSLR commercial photography appearance.
- Realistic textures, natural colours and high clarity.
- Clean, elegant composition with no clutter.

WEBSITE TEXT RULE:
- No headline.
- No CTA.
- No Shop Now button.
- No labels, badges, specifications or extra text.

RESTRICTIONS:
- No Amazon logo.
- No fake discounts, ratings, reviews or claims.
- No distorted or duplicated product.
- No unrelated products.
- No collage, watermark or overcrowded layout.
- No dark scene, night scene, heavy fog or deep underexposure.

Final output:
A photorealistic vertical 2:3 premium lifestyle photograph showing the entire
exact Amazon product naturally integrated into the environment.
""".strip()

def build_pinterest_prompt(product: dict) -> str:
    return build_website_prompt(product)


def build_social_prompt(product: dict) -> str:
    title, category = _product_context(product)

    return (
        f"Create bright premium lifestyle photography for {title}, "
        f"category {category}. Show the complete original product, "
        "fully inside the frame, accurately preserving its identity. "
        "No Amazon logo, no fake claims and no product distortion."
    )
