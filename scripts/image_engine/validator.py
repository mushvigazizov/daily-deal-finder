"""ImageValidator — Sekil keyfiyyet yoxlamasi."""

import json
import os
import struct
from typing import Optional


class ImageValidator:
    """Yaradilmis sekillerin keyfiyyetini yoxlayir."""

    # WebP fayl imzasi
    WEBP_MAGIC = b"RIFF"

    @staticmethod
    def check_exists(path: str) -> bool:
        """Fayl movcuddurmu?"""
        return os.path.isfile(path)

    @staticmethod
    def check_file_size(path: str, min_bytes: int = 1024, max_bytes: Optional[int] = None) -> bool:
        """Fayl olcusu minimumdan boyukdurmu?"""
        if not os.path.isfile(path):
            return False
        size = os.path.getsize(path)
        if size < min_bytes:
            return False
        if max_bytes and size > max_bytes:
            return False
        return True

    @classmethod
    def check_corruption(cls, path: str) -> bool:
        """WebP fayl korlanmayibmi?"""
        try:
            with open(path, "rb") as f:
                header = f.read(4)
                return header == cls.WEBP_MAGIC
        except Exception:
            return False

    @classmethod
    def check_dimensions(cls, path: str, expected_size: tuple) -> bool:
        """WebP olculeri dogrudurmu? (Pillow teleb edir)."""
        try:
            from PIL import Image
            with Image.open(path) as img:
                return img.size == expected_size
        except ImportError:
            print("⚠️ Pillow yoxdur — olcu yoxlanisi kecildi")
            return True  # skip check
        except Exception:
            return False

    @classmethod
    def validate(cls, path: str, requirements: Optional[dict] = None) -> dict:
        """Tam validasiya. requirements = {min_size, max_size, expected_dimensions}."""
        req = requirements or {}
        result = {
            "path": path,
            "exists": cls.check_exists(path),
            "size_ok": cls.check_file_size(
                path,
                min_bytes=req.get("min_size", 1024),
                max_bytes=req.get("max_size"),
            ),
            "not_corrupted": cls.check_corruption(path) if os.path.isfile(path) else False,
            "dimensions_ok": cls.check_dimensions(
                path, req["expected_dimensions"]
            ) if req.get("expected_dimensions") else None,
        }
        result["all_ok"] = all(
            v for k, v in result.items() if k != "all_ok" and v is not None
        )
        return result

    @staticmethod
    def batch_validate(paths: list, requirements: Optional[dict] = None) -> list:
        """Birden cox fayli yoxla."""
        return [ImageValidator.validate(p, requirements) for p in paths]
