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
    """Website məhsul kartı üçün premium editorial prompt."""
    return (
        _base_product_prompt(product)
        + " Create a premium editorial hero image for a modern affiliate shopping website. "
        + "The image should feel like high-end outdoor magazine photography, not a plain catalog photo. "
        + "Use cinematic natural light, realistic textures, warm atmosphere, depth of field, and a clean premium composition. "
        + "Show the product in a believable real-life use scene with environment and context, while keeping the product clearly visible as the main subject. "
        + "Avoid flat studio backgrounds. Avoid generic stock-photo look. Avoid clutter. "
        + "No people faces, no text, no logos, no watermark, no price labels. "
        + "Square 1024x1024 composition suitable for a premium product card."
    )

def build_pinterest_prompt(product: dict) -> str:
    """Pinterest Pin üçün prompt."""

    return (
        _base_product_prompt(product)
        + "Create a premium photorealistic Pinterest image with a 2:3 vertical composition. "
        + "The product must be the clear main subject in realistic outdoor use. "
        + "Use natural lighting, premium lifestyle photography, realistic textures, shallow depth of field and clean composition. "
        + "Leave subtle negative space suitable for adding text later. "
        + "Do NOT include any text, letters, words, typography, captions, "
        + "logos, watermarks, price tags, UI elements, badges or labels "
        + "anywhere in the image. "
        + "The image should look like a high-end commercial outdoor advertisement. "
        + "The image must be visually clean, elegant and suitable for a premium Pinterest brand."
    )




def build_social_prompt(product: dict) -> str:
    """Social media / OG üçün prompt."""
    return (
        _base_product_prompt(product)
        + " Wide social media composition, professional outdoor lifestyle photography, vibrant but natural colors, clean and shareable image."
    )
