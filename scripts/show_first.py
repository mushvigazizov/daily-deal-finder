import json
with open('data/products.json') as f:
    products = json.load(f)
    print(json.dumps(products[0], indent=4))
