import json
from pathlib import Path
from collections import Counter

path = Path("data/products.json")
data = json.loads(path.read_text())
products = data.get("products", data)

def norm(value):
    return str(value or "").strip().lower()

ids = [norm(p.get("id")) for p in products]
titles = [norm(p.get("title")) for p in products]
asins = [norm(p.get("amazon_asin")) for p in products if norm(p.get("amazon_asin"))]

errors = 0

print("=" * 70)
print("PRODUCT DUPLICATE CHECK")
print("=" * 70)

def report_duplicates(label, values):
    global errors
    counts = Counter(values)
    duplicates = [v for v, c in counts.items() if v and c > 1]

    if duplicates:
        for item in duplicates:
            errors += 1
            print(f"[ERROR] duplicate {label}: {item}")
    else:
        print(f"[ OK ] no duplicate {label}")

report_duplicates("id", ids)
report_duplicates("title", titles)
report_duplicates("amazon_asin", asins)

print()
print(f"Products checked: {len(products)}")
print(f"Duplicate errors: {errors}")

if errors == 0:
    print("DUPLICATE CHECK PASSED")
else:
    print("DUPLICATE CHECK FAILED")
    raise SystemExit(1)
