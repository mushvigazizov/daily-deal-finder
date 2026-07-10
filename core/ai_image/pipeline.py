"""ImagePipeline — Tam orkestrasiya: generate → validate → optimize."""

import json
import os
import sys
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from core.ai_image.website import WebsiteProductGenerator
from core.ai_image.pinterest import PinterestPinGenerator
from core.ai_image.social import SocialMediaGenerator
from core.ai_image.validator import ImageValidator
from core.ai_image.optimizer import ImageOptimizer
from core.ai_image.config import SIZES, PLATFORM_DIR


GENERATORS = {
    "website": WebsiteProductGenerator,
    "pinterest": PinterestPinGenerator,
    "social": SocialMediaGenerator,
}


class ImagePipeline:
    """Tam sekil pipeline-i: yarat + yoxla + optimallasdir."""

    def __init__(self, platform: str = "website"):
        self.platform = platform
        gen_cls = GENERATORS.get(platform, WebsiteProductGenerator)
        self.generator = gen_cls()
        self.validator = ImageValidator()
        self.optimizer = ImageOptimizer()
        self.expected_size = SIZES.get(platform, (1024, 1024))
        self.out_dir = os.path.join(ROOT, PLATFORM_DIR.get(platform, "assets/products"))
        os.makedirs(self.out_dir, exist_ok=True)

    # ── Yüklemeler ───────────────────────────────────────
    def _load_products(self) -> List[dict]:
        path = os.path.join(ROOT, "data", "products.json")
        with open(path) as f:
            return json.load(f)["products"]

    def _find_product(self, product_id: str) -> Optional[dict]:
        products = self._load_products()
        return next((p for p in products if p.get("id") == product_id), None)

    def _output_path(self, product_id: str) -> str:
        suffix = {"pinterest": "-pin", "social": "-og"}.get(self.platform, "")
        return os.path.join(self.out_dir, f"{product_id}{suffix}.webp")

    # ── Run Single ───────────────────────────────────────
    def run_single(self, product_id: str) -> Dict:
        """Bir mehsul ucun tam pipeline."""
        result = {"product_id": product_id, "platform": self.platform, "steps": {}}

        product = self._find_product(product_id)
        if not product:
            result["error"] = f"Mehsul tapilmadi: {product_id}"
            return result

        out = self._output_path(product_id)

        generated_req = {
            "min_size": 1024,
            "expected_dimensions": self.expected_size,
        }

        existing_req = {
            "min_size": 1024,
        }

        # Step 0: Reuse an existing healthy image.
        # Existing website assets may be larger than the generator target,
        # for example 1200x1200 instead of 1024x1024.
        if os.path.isfile(out):
            existing_validation = self.validator.validate(
                out,
                existing_req,
            )

            if existing_validation.get("all_ok"):
                result["steps"]["generate"] = {
                    "ok": True,
                    "path": out,
                    "skipped": True,
                    "reason": "existing_valid_image",
                }
                result["steps"]["validate"] = existing_validation
                result["steps"]["optimize"] = {
                    "ok": True,
                    "path": out,
                    "skipped": True,
                }
                result["steps"]["status"] = "SKIPPED_EXISTING"
                return result

        # Step 1: Generate only when no healthy image exists.
        prompt = self.generator.build_prompt(product)
        ok = self.generator.generate(prompt, out)
        result["steps"]["generate"] = {
            "ok": ok,
            "path": out if ok else None,
            "skipped": False,
        }

        if not ok:
            result["steps"]["status"] = "GENERATION_FAILED"
            return result

        # Step 2: Validate
        validation = self.validator.validate(
            out,
            generated_req,
        )
        result["steps"]["validate"] = validation

        if not validation.get("all_ok"):
            result["steps"]["status"] = "VALIDATION_FAILED"
            return result

        # Step 3: Optimize
        optimized = self.optimizer.optimize(out, out, quality=85)
        result["steps"]["optimize"] = {
            "ok": optimized is not None,
            "path": optimized,
            "skipped": False,
        }

        result["steps"]["status"] = "DONE"
        return result

    # ── Run Batch ────────────────────────────────────────
    def run_batch(self, product_ids: Optional[List[str]] = None) -> List[Dict]:
        """Birden cox mehsul ucun pipeline."""
        if product_ids is None:
            product_ids = [p["id"] for p in self._load_products() if p.get("active", True)]
        return [self.run_single(pid) for pid in product_ids]

    # ── Dry Run ──────────────────────────────────────────
    def dry_run(self) -> Dict:
        """Hech bir API cagirisi etmeden plan goster."""
        products = self._load_products()
        plan = {
            "platform": self.platform,
            "generator": type(self.generator).__name__,
            "output_dir": self.out_dir,
            "expected_size": f"{self.expected_size[0]}x{self.expected_size[1]}",
            "products": [],
            "total": len(products),
        }
        for p in products:
            plan["products"].append({
                "id": p["id"],
                "title": p["title"],
                "output": self._output_path(p["id"]),
            })
        return plan

    # ── Generate Report ──────────────────────────────────
    @staticmethod
    def generate_report(results: List[Dict]) -> Dict:
        """Batch neticelerinden hesabat cixar."""
        total = len(results)

        generated = sum(
            1
            for r in results
            if r.get("steps", {}).get("generate", {}).get("ok")
            and not r.get("steps", {}).get("generate", {}).get("skipped")
        )

        skipped_existing = sum(
            1
            for r in results
            if r.get("steps", {}).get("status") == "SKIPPED_EXISTING"
        )

        validated = sum(
            1
            for r in results
            if r.get("steps", {}).get("validate", {}).get("all_ok")
        )

        optimized = sum(
            1
            for r in results
            if r.get("steps", {}).get("optimize", {}).get("ok")
            and not r.get("steps", {}).get("optimize", {}).get("skipped")
        )

        complete = sum(
            1
            for r in results
            if r.get("steps", {}).get("status")
            in {"DONE", "SKIPPED_EXISTING"}
        )

        failed = total - complete

        return {
            "total": total,
            "generated": generated,
            "skipped_existing": skipped_existing,
            "validated": validated,
            "optimized": optimized,
            "complete": complete,
            "failed": failed,
            "success_rate": round(complete / total * 100, 1) if total else 0,
            "errors": [
                r
                for r in results
                if r.get("steps", {}).get("status")
                not in {"DONE", "SKIPPED_EXISTING"}
            ],
        }
