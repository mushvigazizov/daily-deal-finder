#!/usr/bin/env python3
"""
DDF Master Skript — yeni Gruppe-A (logolos) Produkt.
Bu gün (camp-021) el ile edilen 12 addimi birlesdirir.
Insan tesdiqi qalan hisseler (sekil yoxlamasi, deploy, pin) SKRIPT ETMIR.

Istifade:
  python3 scripts/ddf_new_product.py --identity /path/to/<id>.json --ref-url "https://m.media-amazon.com/..jpg"

--identity : hazir verified_identities formatinda JSON (Claude hazirlayir).
             Icinde en azi: id, verified_asin, amazon_*, website{}, english{}
--ref-url  : Amazon reference sekil URL-i (curl ile cekilir)
--studio   : verilse, pinterest_prompt studiya (ag fon) versiyasina qoyulur
"""
import argparse, json, subprocess, sys, shutil
from pathlib import Path
from datetime import date

ROOT = Path("/docker/hermes-agent-yivo/data/daily-deal-finder")
PRODUCTS = ROOT / "data/products.json"
REGISTRY = ROOT / "scripts/importers/asin_import_template.json"
VID_DIR  = ROOT / "data/verified_identities"
REF_DIR  = ROOT / "data/amazon_reference_images"

def run(cmd):
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(f"XETA: bu addim ugursuz oldu -> {cmd}")

def backup(p: Path):
    if p.exists():
        b = p.with_suffix(p.suffix + ".bak-master")
        shutil.copy(p, b)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", required=True, help="verified_identities JSON fayli (Claude hazirlayir)")
    ap.add_argument("--ref-url", required=True, help="Amazon reference sekil URL")
    ap.add_argument("--studio", action="store_true", help="studiya (ag fon) prompt")
    args = ap.parse_args()

    idj = json.load(open(args.identity, encoding="utf-8"))
    pid = idj["id"]
    asin = idj["verified_asin"]
    w = idj["website"]
    print(f"=== DDF NEW PRODUCT: {pid} | {asin} ===")

    # onceden dublikat yoxlamasi
    prods = json.load(open(PRODUCTS, encoding="utf-8"))
    if any(x["id"]==pid for x in prods["products"]):
        sys.exit(f"XETA: {pid} artiq products.json-da var. Dayandim.")

    # studiya prompt istenirse
    if args.studio:
        w["pinterest_prompt"] = (
            f"Create a premium Pinterest vertical image for '{w['title']}'. "
            "Show the realistic product neatly presented on a clean bright white studio background, "
            "soft even lighting, product-focused, high clarity, space for a title overlay, "
            "no Amazon logo, no brand name, no text or lettering anywhere on the product, "
            "keep the product clean and unbranded."
        )

    # 1) REGISTRY
    backup(REGISTRY)
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    reg.append({
        "id": pid, "title": w["title"],
        "current_amazon_asin": asin, "verified_asin": asin,
        "verified_amazon_url": idj["verified_amazon_url"],
        "status": "verified",
        "notes": "Verified Amazon-first product identity (Gruppe A, master script).",
        "amazon_product_title": idj["amazon_product_title"],
        "amazon_brand": idj["amazon_brand"], "amazon_model": idj["amazon_model"],
        "verification_status": "verified",
        "verification_source": idj["verification_source"],
        "amazon_key_specs": idj["amazon_key_specs"],
        "manufacturer_source": idj.get("manufacturer_source",""),
        "identity_locked": False
    })
    json.dump(reg, open(REGISTRY,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[1/9] registry OK")

    # 2) PRODUCTS.JSON
    backup(PRODUCTS)
    prods["products"].append({
        "id": pid, "sku": f"DDF-{pid.upper()}",
        "title": w["title"], "brand": w["brand"],
        "category": idj.get("category","camping"),
        "subcategory": idj.get("subcategory","sicherheit"),
        "short_description": w["short_description"],
        "long_description": w["long_description"],
        "features": w["features"],
        "image": f"assets/products/{pid}.webp",
        "gallery": [], "amazon_asin": asin,
        "button_text": "Auf Amazon ansehen",
        "availability": None, "rating": None, "review_count": None,
        "featured": False, "active": True,
        "created_at": str(date.today()), "updated_at": str(date.today()),
        "tags": w.get("tags",[]),
        "amazon_link_type": "search"
    })
    json.dump(prods, open(PRODUCTS,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[2/9] products.json OK")

    # 3) verified_identities faili
    VID_DIR.mkdir(exist_ok=True)
    json.dump(idj, open(VID_DIR/f"{pid}.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[3/9] verified_identities OK")

    # 4) LOCK
    run(f"python3 scripts/amazon/finalize_verified_product.py --product-id {pid} --asin {asin}")
    print("[4/9] lock OK")

    # 5) pinterest content + prompts
    run("python3 scripts/importers/generate_pinterest_content.py")
    run("python3 scripts/importers/generate_pinterest_prompts.py")
    print("[5/9] pinterest content+prompts OK")

    # 6) SYNC
    run(f"python3 scripts/amazon/sync_verified_identity.py --product-id {pid} --write")
    print("[6/9] sync OK")

    # 7) reference sekil
    REF_DIR.mkdir(exist_ok=True)
    run(f'curl -sL "{args.ref_url}" -o data/amazon_reference_images/{pid}.jpg')
    print("[7/9] reference sekil OK")

    # 8) pinterest sekil (candidate)
    run(f"python3 scripts/generate_image.py --product {pid} --platform pinterest --candidate")
    print("[8/9] pinterest sekil (candidate) OK")

    # 9) website sekli hazirla (candidate -> products)
    src = ROOT / f"inspection/candidates/pinterest/{pid}-pin.webp"
    if src.exists():
        shutil.copy(src, ROOT / f"assets/pinterest/{pid}-pin.webp")
        shutil.copy(src, ROOT / f"assets/products/{pid}.webp")
        print("[9/9] sekiller assets-e kopyalandi OK")
    else:
        print("[9/9] XEBERDARLIQ: candidate sekil tapilmadi, elle yoxla")

    print(f"""
========================================================
HAZIR (avtomat hisse bitdi): {pid}
Indi SEN et (insan tesdiqi):
  1) Sekli yoxla:  inspection/candidates/pinterest/{pid}-pin.webp
  2) Deploy (isole worktree ile 6 fayl):
     data/products.json, data/pinterest_content.json,
     data/content/{pid}.de.json, data/content/{pid}.en.json,
     assets/pinterest/{pid}-pin.webp, assets/products/{pid}.webp
  3) Saytda yoxla: /product.html?id={pid}
  4) n8n POST+Code -> {pid}/{asin}, Execute
  5) record_publication.py
========================================================
""")

if __name__ == "__main__":
    main()
