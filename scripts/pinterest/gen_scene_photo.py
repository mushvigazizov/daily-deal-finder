# Erzeugt aus dem echten Amazon-Referenzbild ein fotorealistisches Szenenfoto (OpenAI gpt-image-2.5-flare, Bild-Edit)
import argparse, base64, json, os, sys, urllib.request, urllib.error, uuid

ap = argparse.ArgumentParser()
ap.add_argument('--product', required=True)
ap.add_argument('--hint', default=None)
ap.add_argument('--quality', default='medium')
ap.add_argument('--note', default='')
a = ap.parse_args()

HINTS = {
    'camping': 'green grass at the edge of a forest, soft morning sunlight through the trees, light mist, no water, no lake',
    'kitchen': 'a warm, softly lit modern kitchen, wooden table or countertop, natural window light, a cup of coffee or a few simple kitchen items nearby but not covering the product, no people',
    'home': 'a bright, cosy home interior with natural window light, a few simple decor items nearby but not covering the product, no people',
    'tech': 'a tidy modern desk by a window with natural daylight, a few simple items nearby but not covering the product, no people',
    'pets': 'a bright, cosy home interior with natural window light, a few simple items nearby but not covering the product, no people',
}
if not a.hint:
    cat = 'camping'
    try:
        _d = json.load(open('data/products.json', encoding='utf-8'))
        _p = _d['products'] if isinstance(_d, dict) else _d
        cat = next((x.get('category') for x in _p if x.get('id') == a.product), 'camping') or 'camping'
    except Exception:
        pass
    a.hint = HINTS.get(cat, HINTS['camping'])
    print('sehne kateqoriyasi:', cat)

key = os.environ.get('OPENAI_IMAGE_API_KEY')
if not key and os.path.exists('.env'):
    for ln in open('.env', encoding='utf-8'):
        ln = ln.strip().replace('export ', '', 1)
        if ln.startswith('OPENAI_IMAGE_API_KEY='):
            key = ln.split('=', 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit('FEHLER: OPENAI_IMAGE_API_KEY nicht gefunden')

ref = 'data/amazon_reference_images/%s.jpg' % a.product
if not os.path.exists(ref):
    sys.exit('FEHLER: Referenzbild fehlt: ' + ref)

prompt = (
    "Photorealistic lifestyle photograph, vertical 2:3. Use the attached reference image of the product and keep the product "
    "exactly as it is: same colours, shape, proportions, construction, markings and details. Do not add, remove or change any "
    "feature of the product (no extra windows, doors, parts or accessories on it). Place the product in a natural, realistic "
    "setting: " + a.hint + ". The product is the clear main subject, large and easy to recognise on a small phone screen, with "
    "realistic ground contact, natural shadows and matching light. A very small natural detail beside it is allowed but must "
    "not cover the product. Natural, vivid but believable colours, like a professional photographer. "
    "Reproduce any logo or printed mark on the product exactly as in the reference image, and keep nets, straps and small parts "
    "the same colour and shape as in the reference. Do not invent any new text or lettering. "
    "No text, no price, no logos added, no watermark, no cartoon or 3D-render look."
)

if a.note:
    prompt += " Additional instruction: " + a.note

fields = {'model': 'gpt-image-2.5-flare', 'prompt': prompt, 'size': '1024x1536', 'quality': a.quality, 'n': '1'}
b = uuid.uuid4().hex
body = b''
for k, v in fields.items():
    body += ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, k, v)).encode()
body += ('--%s\r\nContent-Disposition: form-data; name="image[]"; filename="ref.jpg"\r\nContent-Type: image/jpeg\r\n\r\n' % b).encode()
body += open(ref, 'rb').read() + b'\r\n'
body += ('--%s--\r\n' % b).encode()

req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body,
                             headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'multipart/form-data; boundary=' + b})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit('FEHLER %s: %s' % (e.code, e.read().decode()[:400]))
out = 'assets/pinterest/%s-scene.png' % a.product
open(out, 'wb').write(base64.b64decode(r['data'][0]['b64_json']))
print('OK', out, os.path.getsize(out))
