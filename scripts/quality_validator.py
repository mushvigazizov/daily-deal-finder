import json
from pathlib import Path

PRODUCTS_PATH = Path("data/products.json")
MIN_FILE_SIZE = 50 * 1024  # 50 KB

def validate_product_image(product):
    pid = product.get("id")
    title = product.get("title", "")
    image = product.get("image", "")
    features = product.get("features") or []

    issues = []
    warnings = []

    if not pid:
        issues.append("missing product id")

    if not title:
        issues.append("missing title")

    if not features:
        warnings.append("no features found")

    if not image:
        issues.append("missing image path")
    elif image.endswith(".svg"):
        warnings.append("still using placeholder svg image")
    else:
        path = Path(image)

        if not path.exists():
            issues.append(f"image file does not exist: {image}")
        else:
            size = path.stat().st_size

            if size == 0:
                issues.append("image file is empty")

            if size < MIN_FILE_SIZE:
                warnings.append(f"image file is very small: {size} bytes")

            if not image.endswith(".webp"):
                warnings.append("image is not webp format")

    score = 100
    score -= len(issues) * 40
    score -= len(warnings) * 10
    score = max(score, 0)

    return {
        "id": pid,
        "title": title,
        "image": image,
        "ok": len(issues) == 0,
        "score": score,
        "issues": issues,
        "warnings": warnings,
    }

def main():
    data = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    total = 0
    ok = 0
    failed = 0
    warnings_count = 0

    for product in data["products"]:
        result = validate_product_image(product)
        total += 1

        if result["ok"]:
            ok += 1
        else:
            failed += 1

        if result["warnings"]:
            warnings_count += 1

        if result["issues"] or result["warnings"]:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("-" * 60)

    print(f"SUMMARY total={total} ok={ok} failed={failed} warnings={warnings_count}")

if __name__ == "__main__":
    main()
