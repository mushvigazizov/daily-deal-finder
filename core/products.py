import json
from core.paths import PRODUCTS_FILE

def load_products():
    data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    return data.get("products", data)

def count_products():
    return len(load_products())
