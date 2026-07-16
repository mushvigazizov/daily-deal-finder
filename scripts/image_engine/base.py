import base64
import html
import os
import re
import tempfile
import urllib.request
from pathlib import Path


class BaseImageGenerator:
    MODEL = "gpt-image-1"
    SIZE = (1024, 1536)
    QUALITY = "high"

    def __init__(self):
        self.api_key = self._load_api_key()

    @staticmethod
    def _load_api_key() -> str:
        key = os.environ.get("OPENAI_IMAGE_API_KEY", "")
        if key:
            return key

        root = Path(__file__).resolve().parents[2]
        env_path = root / ".env"

        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if (
                    line
                    and not line.startswith("#")
                    and "=" in line
                ):
                    name, value = line.split("=", 1)
                    if name.strip() == "OPENAI_IMAGE_API_KEY":
                        return value.strip().strip('"').strip("'")

        return ""

    @staticmethod
    def _request(url: str) -> urllib.request.Request:
        return urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/126 Safari/537.36"
                ),
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            },
        )

    def download_amazon_reference(
        self,
        amazon_url: str,
        product_id: str,
    ) -> str:
        if not amazon_url:
            raise RuntimeError("Amazon product URL is missing.")

        with urllib.request.urlopen(
            self._request(amazon_url),
            timeout=30,
        ) as response:
            page = response.read().decode("utf-8", errors="ignore")

        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'id=["\']landingImage["\'][^>]+data-old-hires=["\']([^"\']+)',
            r'id=["\']landingImage["\'][^>]+src=["\']([^"\']+)',
            r'"hiRes":"(https:[^"]+)"',
            r'"large":"(https:[^"]+)"',
        ]

        image_url = ""

        for pattern in patterns:
            match = re.search(pattern, page, flags=re.I)
            if match:
                image_url = html.unescape(match.group(1))
                image_url = image_url.replace("\\u0026", "&")
                image_url = image_url.replace("\\/", "/")
                break

        if not image_url:
            raise RuntimeError(
                "Amazon reference image URL could not be extracted."
            )

        suffix = Path(image_url.split("?", 1)[0]).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        reference_dir = Path("data/amazon_reference_images")
        reference_dir.mkdir(parents=True, exist_ok=True)

        output = reference_dir / f"{product_id}{suffix}"

        with urllib.request.urlopen(
            self._request(image_url),
            timeout=30,
        ) as response:
            output.write_bytes(response.read())

        if output.stat().st_size < 10_000:
            raise RuntimeError("Downloaded reference image is too small.")

        print(f"REFERENCE {output}")
        return str(output)

    def generate(
        self,
        prompt: str,
        output_path: str,
        reference_image: str | None = None,
    ) -> bool:
        if not self.api_key:
            print("OPENAI_IMAGE_API_KEY tapilmadi.")
            return False

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            if reference_image:
                with open(reference_image, "rb") as image_file:
                    response = client.images.edit(
                        model=self.MODEL,
                        image=image_file,
                        prompt=prompt,
                        size=f"{self.SIZE[0]}x{self.SIZE[1]}",
                        quality=self.QUALITY,
                        input_fidelity="high",
                        output_format="webp",
                        n=1,
                    )
            else:
                response = client.images.generate(
                    model=self.MODEL,
                    prompt=prompt,
                    size=f"{self.SIZE[0]}x{self.SIZE[1]}",
                    quality=self.QUALITY,
                    output_format="webp",
                    n=1,
                )

            image = response.data[0]
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            if getattr(image, "b64_json", None):
                output.write_bytes(
                    base64.b64decode(image.b64_json)
                )
            elif getattr(image, "url", None):
                urllib.request.urlretrieve(image.url, output)
            else:
                print("API sekil qaytarmadi.")
                return False

            print(f"OK {output.name}")
            return True

        except Exception as error:
            print(f"Xeta: {error}")
            return False

    def build_prompt(self, product: dict) -> str:
        raise NotImplementedError
