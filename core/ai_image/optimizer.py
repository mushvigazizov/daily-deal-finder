"""ImageOptimizer — Sekil optimallasdirma (compress, resize, convert)."""

import os
import shutil
from typing import Optional


class ImageOptimizer:
    """Sekilleri sixir, olculendirir, format deyisir."""

    DEFAULT_QUALITY = 85
    DEFAULT_MAX_WIDTH = 1200

    # ── Pillow yoxlamasi ─────────────────────────────────
    @staticmethod
    def _has_pillow() -> bool:
        try:
            import PIL.Image
            return True
        except ImportError:
            return False

    # ── Compress ─────────────────────────────────────────
    @classmethod
    def compress(cls, source: str, dest: Optional[str] = None, quality: int = DEFAULT_QUALITY) -> Optional[str]:
        """WebP sekili six. dest=None → eyni faylin uzerine yaz."""
        if not cls._has_pillow():
            print("⚠️ Pillow yoxdur — compress kecildi")
            return source
        try:
            from PIL import Image
            target = dest or source
            with Image.open(source) as img:
                img.save(target, "WEBP", quality=quality)
            return target
        except Exception as e:
            print(f"❌ Compress xetasi: {e}")
            return None

    # ── Resize ───────────────────────────────────────────
    @classmethod
    def resize(cls, source: str, dest: Optional[str] = None,
               width: Optional[int] = None, height: Optional[int] = None) -> Optional[str]:
        """Sekili olculendir. Eni max DEFAULT_MAX_WIDTH, nisbet qorunur."""
        if not cls._has_pillow():
            print("⚠️ Pillow yoxdur — resize kecildi")
            return source
        try:
            from PIL import Image
            target = dest or source
            with Image.open(source) as img:
                w, h = img.size
                if width and height:
                    new_size = (width, height)
                elif width:
                    ratio = width / w
                    new_size = (width, int(h * ratio))
                elif height:
                    ratio = height / h
                    new_size = (int(w * ratio), height)
                else:
                    new_size = (w, h)
                img = img.resize(new_size, Image.LANCZOS)
                img.save(target, "WEBP", quality=90)
            return target
        except Exception as e:
            print(f"❌ Resize xetasi: {e}")
            return None

    # ── Convert to WebP ──────────────────────────────────
    @classmethod
    def convert_to_webp(cls, source: str, dest: Optional[str] = None, quality: int = 85) -> Optional[str]:
        """Her hansi format → WebP."""
        if not cls._has_pillow():
            print("⚠️ Pillow yoxdur — convert kecildi")
            return source
        try:
            from PIL import Image
            target = dest or os.path.splitext(source)[0] + ".webp"
            with Image.open(source) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(target, "WEBP", quality=quality)
            return target
        except Exception as e:
            print(f"❌ Convert xetasi: {e}")
            return None

    # ── Strip Metadata ───────────────────────────────────
    @classmethod
    def strip_metadata(cls, source: str, dest: Optional[str] = None) -> Optional[str]:
        """EXIF ve metadata temizle."""
        if not cls._has_pillow():
            print("⚠️ Pillow yoxdur — strip kecildi")
            return source
        try:
            from PIL import Image
            target = dest or source
            with Image.open(source) as img:
                data = list(img.getdata())
                clean = Image.new(img.mode, img.size)
                clean.putdata(data)
                clean.save(target, "WEBP", quality=90)
            return target
        except Exception as e:
            print(f"❌ Strip xetasi: {e}")
            return None

    # ── Optimize (hepsi bir yerde) ───────────────────────
    @classmethod
    def optimize(cls, source: str, dest: Optional[str] = None,
                 quality: int = DEFAULT_QUALITY,
                 max_width: int = DEFAULT_MAX_WIDTH) -> Optional[str]:
        """Tam optimallasdirma: resize + strip + compress."""
        if not cls._has_pillow():
            print("⚠️ Pillow yoxdur — optimize kecildi, orijinal fayl saxlanildi")
            if dest and dest != source:
                shutil.copy2(source, dest)
            return dest or source

        # Pipe: resize → strip → compress
        tmp1 = source
        tmp2 = source + ".tmp.webp"

        # Resize (eger lazimdirsa)
        resized = cls.resize(tmp1, tmp2, width=max_width)
        if resized:
            tmp1 = resized

        # Strip
        stripped = cls.strip_metadata(tmp1, tmp2)
        if stripped:
            tmp1 = stripped

        # Compress to final
        result = cls.compress(tmp1, dest or source, quality)

        # Cleanup temp
        for t in [tmp2]:
            if os.path.exists(t) and t != (dest or source):
                os.remove(t)

        return result
