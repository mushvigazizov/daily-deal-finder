from .base import BaseImageGenerator
from .prompts import build_website_prompt


class WebsiteProductGenerator(BaseImageGenerator):
    """Website məhsul şəkli — 1024×1024."""

    SIZE = (1024, 1024)

    def build_prompt(self, product: dict) -> str:
        return build_website_prompt(product)
