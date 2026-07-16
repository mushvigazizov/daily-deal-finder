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
Create a high-converting Pinterest-style product image in vertical 2:3 format
using the uploaded Amazon product image.

Product title: {title}
Category: {category}

REFERENCE IMAGE RULES:
- The uploaded Amazon product image is the single source of truth.
- Preserve the exact product identity.
- Keep the same model, shape, proportions, color, materials and construction.
- Preserve visible openings, poles, seams, zippers, panels and accessories.
- Do not redesign, simplify, replace or reinterpret the product.
- The generated product must remain immediately recognizable as the same item.

PRODUCT VISIBILITY:
- Show the entire product fully inside the frame.
- Do not crop, cut off or hide any part of the product.
- Keep comfortable space around the complete product.
- Make the product large, clear and the main hero.
- Use a natural three-quarter viewing angle.
- Do not place unrelated products in front of it.

LIGHTING AND SCENE:
- Use bright natural daylight or warm golden-hour light.
- The product must be clearly visible and correctly exposed.
- Avoid darkness, night scenes, deep shadows, fog and underexposure.
- Create a realistic, fresh and beautiful lifestyle scene matching the category.
- Use an aspirational premium Pinterest aesthetic.
- Rich but natural colors, realistic textures and high clarity.
- Clean composition with no clutter.
- Do not copy the original Amazon background.

TEXT OVERLAY:
- Add exactly ONE short bold headline.
- Headline must contain 3 to 6 correctly spelled words.
- Create the headline from the product's strongest emotional appeal.
- Add exactly ONE CTA button or CTA label.
- CTA examples: Get the Look, Shop Now, See More, Discover More, View the Find.
- Text must be large, clean and mobile-readable.
- Do not cover the product with text.
- Do not add specifications, dimensions, bullet points or extra text.

RESTRICTIONS:
- No Amazon logo.
- No fake discount.
- No fake rating or review.
- No misleading claim.
- No messy collage.
- No distorted product.
- No duplicated product.
- No typo-filled text.
- No repeated text.
- No overcrowded layout.
- No unrelated product stealing attention.

Final result:
A bright, polished, realistic premium lifestyle product pin in vertical 2:3
format, with the entire original product clearly visible, one headline and one CTA.
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
