DEFAULT_CONTEXT = "realistic product lifestyle photography"

SUBCATEGORY_CONTEXT = {
    "zelte": "realistic camping tent in an outdoor campsite setting",
    "schlafsacke": "realistic sleeping bag in a cozy camping environment",
    "lampen": "realistic camping light or headlamp used outdoors",
    "rucksacke": "realistic hiking backpack in a mountain or forest trail setting",
    "mobel": "realistic camping furniture in an outdoor relaxation setting",
    "kuche": "realistic camping cooking gear in an outdoor kitchen setting",
    "sicherheit": "realistic outdoor safety and survival gear setting",
    "kleidung": "realistic outdoor clothing in a hiking or camping setting",
    "zubehor": "realistic camping accessory in a practical outdoor scene",
}

def _features(product: dict, limit: int = 4) -> str:
    items = product.get("features") or []
    if not items:
        return ""
    return ", ".join(items[:limit])

def _base_product_prompt(product: dict) -> str:
    title = product.get("title", "")
    brand = product.get("brand", "")
    sub = product.get("subcategory", "")
    ctx = SUBCATEGORY_CONTEXT.get(sub, DEFAULT_CONTEXT)
    short = product.get("short_description", "")
    features = _features(product)

    return (
        f"{ctx}. "
        f"Product title: {title}. "
        f"Brand reference: {brand}. "
        f"Key features: {features}. "
        f"Short product description: {short}. "
        f"Create a photorealistic commercial lifestyle image that accurately represents the product type, size, function, and intended use. "
        f"The product must look realistic, useful, and trustworthy. "
        f"Do not exaggerate capacity, size, material, or features. "
        f"Do not copy Amazon product photography. "
        f"No brand logos, no text, no watermark, no price tags."
    )

def build_website_prompt(product: dict) -> str:
    """Website məhsul kartı üçün prompt."""
    return (
        _base_product_prompt(product)
        + " Horizontal website product card composition, product centered and clearly visible, natural light, clean background, premium outdoor e-commerce style."
    )

def build_pinterest_prompt(product: dict) -> str:
    """Pinterest Pin üçün prompt."""
    return (
        _base_product_prompt(product)
        + " Vertical 2:3 Pinterest composition, attractive lifestyle setting, strong visual focus on the product, clean copy space near the top, warm natural light."
    )

def build_social_prompt(product: dict) -> str:
    """Social media / OG üçün prompt."""
    return (
        _base_product_prompt(product)
        + " Wide social media composition, professional outdoor lifestyle photography, vibrant but natural colors, clean and shareable image."
    )
