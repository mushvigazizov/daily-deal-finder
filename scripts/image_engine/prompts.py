SUBCATEGORY_CONTEXT = {
    "zelte": "professional camping tent on clean natural outdoor background",
    "schlafsacke": "premium sleeping bag laid on wooden cabin floor, soft lighting",
    "lampen": "LED camping lantern on wooden picnic table at dusk, warm glow",
    "rucksacke": "hiking backpack against mountain landscape, adventure vibe",
    "mobel": "folding camping chair on grassy field, sunny day, lifestyle shot",
    "kuche": "camping stove and cookware set on outdoor table, natural light",
    "sicherheit": "first aid kit and water filter on camping gear flat lay",
    "kleidung": "outdoor waterproof jacket on rustic wooden hook, studio quality",
    "zubehor": "camping multi-tool and paracord on rustic wood surface, detail shot",
}

DEFAULT_CONTEXT = "premium camping gear product photo"


def build_website_prompt(product: dict) -> str:
    """Website məhsul səhifəsi üçün prompt."""
    sub = product.get("subcategory", "")
    ctx = SUBCATEGORY_CONTEXT.get(sub, DEFAULT_CONTEXT)
    return (
        f"{ctx}, "
        f"{product['title']}, "
        f"clean natural background, 1024x1024 square, "
        f"soft studio lighting, professional product photography, "
        f"Pinterest-friendly, realistic, no text overlays, no brand logos"
    )


def build_pinterest_prompt(product: dict) -> str:
    """Pinterest Pin üçün prompt."""
    sub = product.get("subcategory", "")
    ctx = SUBCATEGORY_CONTEXT.get(sub, DEFAULT_CONTEXT)
    return (
        f"{ctx}, "
        f"{product['title']}, "
        f"vertical 2:3 ratio, lifestyle setting, natural light, "
        f"warm tones, Pinterest aesthetic, clean composition, "
        f"copy space on top for text overlay, no brand logos"
    )


def build_social_prompt(product: dict) -> str:
    """Social media (OG / Instagram) üçün prompt."""
    sub = product.get("subcategory", "")
    ctx = SUBCATEGORY_CONTEXT.get(sub, DEFAULT_CONTEXT)
    return (
        f"{ctx}, "
        f"{product['title']}, "
        f"wide composition, outdoor lifestyle, vibrant but natural colors, "
        f"professional photography, suitable for social media sharing, "
        f"no text overlays, no brand logos"
    )
