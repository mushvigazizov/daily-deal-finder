from .base import BaseImageGenerator
from .prompts import build_pinterest_prompt


class PinterestPinGenerator(BaseImageGenerator):
    """Pinterest Pin şəkli — 1024×1536 (2:3)."""

    SIZE = (1024, 1536)

    def build_prompt(self, product: dict) -> str:
        return build_pinterest_prompt(product)
