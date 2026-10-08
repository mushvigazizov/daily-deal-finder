#!/usr/bin/env bash
# DDF: Yeni mehsulu BIR JSON fayldan tam avtomatik elave edir.
# Istifade:  bash scripts/ddf_auto_add.sh /tmp/camp-0XX.json
# JSON = normal identity JSON + 2 elave sahe:
#   "ref_url":      Amazon esas sekil linki
#   "overlay_text": pin seklinin alt yazisi
# Addimlar: yoxlama -> master skript -> overlay -> tehlukesiz deploy (yalniz 6 fayl).
# Pin ATILMIR. Pin yalniz bota "camp-0XX" yazib Approve basanda gedir.
set -euo pipefail

PROJECT=/docker/hermes-agent-yivo/data/daily-deal-finder
DEPLOY=/tmp/ddf-deploy
IN="${1:-}"

fail() { echo "XETA: $*"; exit 1; }

[ -n "$IN" ] && [ -f "$IN" ] || fail "JSON fayl tapilmadi: $IN"
cd "$PROJECT"

# 1) JSON-u oxu ve yoxla; ref_url/overlay_text-i ayir (identity fayli temiz qalsin)
read -r ID REF OVL < <(python3 - "$IN" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
pid = d.get("id", "")
if not re.fullmatch(r"camp-\d{3}", pid):
    sys.exit("id formati sehvdir (camp-XXX olmalidir)")
for k in ["verified_asin", "verified_amazon_url", "amazon_brand", "amazon_model",
          "category", "website", "english", "ref_url", "overlay_text"]:
    if not d.get(k):
        sys.exit("bos ve ya yoxdur: " + k)
if not re.fullmatch(r"[A-Z0-9]{10}", d["verified_asin"]):
    sys.exit("ASIN formati sehvdir")
if d["verified_amazon_url"] != "https://www.amazon.de/dp/" + d["verified_asin"]:
    sys.exit("verified_amazon_url ASIN ile uygun deyil")
prods = json.load(open("data/products.json", encoding="utf-8"))
prods = prods.get("products", prods)
if any(p.get("id") == pid for p in prods):
    sys.exit(pid + " artiq products.json-da var")
if any(p.get("verified_asin") == d["verified_asin"] for p in prods):
    sys.exit("bu ASIN artiq saytda var")
ref, ovl = d.pop("ref_url"), d.pop("overlay_text")
note = d.pop("scene_note", "")
open("/tmp/" + pid + ".scenenote", "w", encoding="utf-8").write(note)
json.dump(d, open("/tmp/" + pid + ".identity.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(pid, ref.replace(" ", "%20"), ovl.replace(" ", "\x1f"))
PY
) || fail "JSON yoxlamasi kecmedi"
OVL="${OVL//$'\x1f'/ }"
echo "[1/5] JSON OK: $ID"

# 2) Master skript (katalog + identity + sekil)
python3 scripts/ddf_new_product.py --identity "/tmp/$ID.identity.json" \
  --ref-url "$REF" --studio > "/tmp/$ID.master.log" 2>&1 \
  || fail "master skript (log: /tmp/$ID.master.log)"
grep -q "HAZIR" "/tmp/$ID.master.log" || fail "master skript bitmedi (log: /tmp/$ID.master.log)"
echo "[2/5] master skript OK"

# 3) Real Amazon sekli + overlay
python3 scripts/pinterest/add_overlay.py --product "$ID" --real --text "$OVL" \
  > "/tmp/$ID.overlay.log" 2>&1 || fail "overlay (log: /tmp/$ID.overlay.log)"
echo "[3/5] overlay OK"

# 3b) AI foto-sehne (OpenAI, real Amazon seklinden) -> pin seklini evez edir
python3 scripts/pinterest/gen_scene_photo.py --product "$ID" --note "$(cat "/tmp/$ID.scenenote" 2>/dev/null)" \
  > "/tmp/$ID.scene.log" 2>&1 || fail "sehne sekli (log: /tmp/$ID.scene.log)"
python3 scripts/pinterest/make_pin_scene.py --product "$ID" --text "$OVL" \
  --photo "assets/pinterest/$ID-scene.png" \
  >> "/tmp/$ID.scene.log" 2>&1 || fail "pin dizayni (log: /tmp/$ID.scene.log)"
echo "[3b/5] foto-sehne OK"

# 3c) scene_note varsa: mehsul sehifesinin sekli de temiz AI sekli olsun (artiq cihazlar silinib)
if [ -s "/tmp/$ID.scenenote" ]; then
  python3 -c "from PIL import Image; Image.open('assets/pinterest/$ID-scene.png').convert('RGB').save('assets/products/$ID.webp', quality=90)" || fail "mehsul sekli"
  echo "[3c/5] mehsul sehifesi sekli: temiz AI sekli"
fi

# 4) Tehlukesizlik: diger mehsullar deyismeyib?
git fetch -q origin
git show origin/main:data/products.json > /tmp/_old_products.json
git show origin/main:data/pinterest_content.json > /tmp/_old_pc.json

# 4a) Master skript kohne qeydleri pozur: onlari origin versiyasina qaytar (yalniz pinterest_content.json)
python3 - <<'PYFIX' || fail "kohne qeydlerin berpasi alinmadi"
import json
def items(d):
    if isinstance(d, list):
        return d
    for k in ('pins', 'products'):
        if k in d:
            return d[k]
    return d
p = 'data/pinterest_content.json'
srv = json.load(open(p, encoding='utf-8'))
old = json.load(open('/tmp/_old_pc.json', encoding='utf-8'))
si, oi = items(srv), items(old)
omap = {x['product_id']: x for x in oi}
n = sum(1 for x in si if x['product_id'] in omap and x != omap[x['product_id']])
new = [x for x in si if x['product_id'] not in omap]
si[:] = oi + new
json.dump(srv, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
open(p, 'a').write(chr(10))
print('kohne qeydler qaytarildi:', n)
PYFIX
python3 - "$ID" <<'PY' || fail "diger mehsullarda gozlenilmez deyisiklik var - deploy DAYANDIRILDI"
import json, sys
pid = sys.argv[1]
def rows(path, key):
    d = json.load(open(path, encoding="utf-8"))
    d = d.get("pins", d.get("products", d)) if isinstance(d, dict) else d
    return {x[key]: x for x in d}
for old, new, key, allowed in [
    ("/tmp/_old_products.json", "data/products.json", "id", set()),
    ("/tmp/_old_pc.json", "data/pinterest_content.json", "product_id", {"created_at"}),
]:
    a, b = rows(old, key), rows(new, key)
    if set(b) - set(a) != {pid}:
        sys.exit("yeni mehsullar: %s" % sorted(set(b) - set(a)))
    if set(a) - set(b):
        sys.exit("silinen mehsullar: %s" % sorted(set(a) - set(b)))
    for k in a:
        diff = {f for f in set(a[k]) | set(b[k]) if a[k].get(f) != b[k].get(f)} - allowed
        if diff:
            sys.exit("%s deyisib: %s" % (k, sorted(diff)))
print("diff OK")
PY
echo "[4/5] yoxlama OK"

# 5) Isole worktree ile yalniz 6 fayl deploy
FILES="data/products.json data/pinterest_content.json data/content/$ID.de.json data/content/$ID.en.json assets/pinterest/$ID-pin.webp assets/products/$ID.webp"
for f in $FILES; do [ -f "$f" ] || fail "fayl yoxdur: $f"; done
rm -rf "$DEPLOY" && git worktree prune
git worktree add -q --detach "$DEPLOY" origin/main
for f in $FILES; do mkdir -p "$DEPLOY/$(dirname "$f")"; cp "$f" "$DEPLOY/$f"; done
cd "$DEPLOY"
git add $FILES
N=$(git status --short | wc -l)
[ "$N" -eq 6 ] || fail "deploy-da 6 deyil, $N fayl var"
git commit -q -m "Add $ID (auto)"
git push -q origin HEAD:main
echo "[5/5] deploy OK"

echo "HAZIR: $ID"
echo "Sehife: https://daily-deal-finder.com/product.html?id=$ID"
echo "Pin sekli: https://daily-deal-finder.com/assets/pinterest/$ID-pin.webp"
echo "2 deqiqe sonra yoxla, sonra bota yaz: $ID"
