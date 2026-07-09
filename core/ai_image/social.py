from .base import BaseImageGenerator
from .prompts import build_social_prompt


class SocialMediaGenerator(BaseImageGenerator):
    """Sosial media şəkli — 1200×630 (OG)."""

    SIZE = (1200, 630)

    def build_prompt(self, product: dict) -> str:
        return build_social_prompt(product)
