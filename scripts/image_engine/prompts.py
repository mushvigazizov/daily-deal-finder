def build_website_prompt(product: dict) -> str:
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

    return f"""
Create a high-converting Pinterest-style product image in vertical 2:3 format
using the uploaded product image.

Product title: {title}
Category: {category}

The uploaded Amazon product image is the primary and authoritative product
reference. Keep the product accurate, recognizable and visually faithful to
the original item. Preserve its shape, proportions, color, construction,
openings, seams, poles, zippers, logo placement and recognizable details.

Place the same product in a fresh, beautiful and realistic lifestyle scene
that naturally matches the category. Do not copy the original background or
composition.

Creative direction:
- Make the product the clear hero
- Use a realistic premium lifestyle environment
- Aspirational, polished and Pinterest-friendly
- Warm, attractive, visually rich photography
- High clarity and no clutter
- Do not distort or redesign the product

Text overlay:
- Add exactly ONE short bold headline
- Headline must contain 3 to 6 words
- Add exactly ONE short CTA button or CTA label
- Use a CTA such as Get the Look, Shop Now, See More, Discover More or View the Find
- Text must be large, clean, correctly spelled and mobile-readable
- Do not cover the product excessively
- Do not add specifications, dimensions, bullets or additional text

Restrictions:
- No Amazon logo
- No fake discount
- No fake rating or review
- No misleading claim
- No messy collage
- No distorted product
- No unrelated product
- No typo-filled text
- No repeated text
- No overcrowded layout

Premium commercial lifestyle photography, vertical 2:3 composition.
""".strip()


def build_pinterest_prompt(product: dict) -> str:
    return build_website_prompt(product)


def build_social_prompt(product: dict) -> str:
    title = product.get("title", "")
    return (
        f"Premium realistic product lifestyle photography for {title}. "
        "Wide composition, no misleading claims, no Amazon logo."
    )
