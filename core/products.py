import json
from core.paths import PRODUCTS_FILE

def load_product_data():
    return json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))

def save_product_data(data):
    PRODUCTS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def load_products():
    data = load_product_data()
    return data.get("products", data)

def count_products():
    return len(load_products())
