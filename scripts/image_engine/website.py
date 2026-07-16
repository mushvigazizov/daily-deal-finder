from .base import BaseImageGenerator
from .prompts import build_website_prompt


class WebsiteProductGenerator(BaseImageGenerator):
    SIZE = (1024, 1536)

    def build_prompt(self, product: dict) -> str:
        return build_website_prompt(product)
