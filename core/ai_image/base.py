import os
import urllib.request
import base64

class BaseImageGenerator:
    """Abstrakt sekil generatoru."""

    MODEL = "gpt-image-1"
    SIZE = (1024, 1024)
    QUALITY = "high"

    def __init__(self):
        self.api_key = self._load_api_key()

    @staticmethod
    def _load_api_key() -> str:
        key = os.environ.get("OPENAI_IMAGE_API_KEY", "")
        if not key:
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                ".env",
            )
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "OPENAI_IMAGE_API_KEY":
                                key = v.strip().strip('"').strip("\'")
                                break
        return key

    def generate(self, prompt: str, output_path: str) -> bool:
        if not self.api_key:
            print("OPENAI_IMAGE_API_KEY tapilmadi.")
            return False
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.images.generate(
                model=self.MODEL,
                prompt=prompt,
                size=f"{self.SIZE[0]}x{self.SIZE[1]}",
                quality=self.QUALITY,
                n=1,
            )
            img = resp.data[0]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if getattr(img, "b64_json", None):
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img.b64_json))
            elif getattr(img, "url", None):
                urllib.request.urlretrieve(img.url, output_path)
            else:
                print("API sekil qaytarmadi.")
                return False
            print(f"OK {os.path.basename(output_path)}")
            return True
        except ImportError:
            print("openai paketi yoxdur.")
            return False
        except Exception as e:
            print(f"Xeta: {e}")
            return False

    def build_prompt(self, product: dict) -> str:
        raise NotImplementedError
