import base64, json, os, sys, urllib.request, urllib.error
name, prompt = sys.argv[1], sys.argv[2]
key = os.environ.get('OPENAI_IMAGE_API_KEY')
if not key and os.path.exists('.env'):
    for ln in open('.env', encoding='utf-8'):
        ln = ln.strip().replace('export ', '', 1)
        if ln.startswith('OPENAI_IMAGE_API_KEY='):
            key = ln.split('=', 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit('FEHLER: OPENAI_IMAGE_API_KEY nicht gefunden')
body = {'model': 'gpt-image-2.5-flare', 'prompt': prompt, 'size': '1024x1536', 'quality': 'medium', 'n': 1}
req = urllib.request.Request('https://api.openai.com/v1/images/generations', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=240))
except urllib.error.HTTPError as e:
    sys.exit('FEHLER %s: %s' % (e.code, e.read().decode()[:300]))
out = 'assets/pinterest/backgrounds/%s.jpg' % name
open(out, 'wb').write(base64.b64decode(r['data'][0]['b64_json']))
print('OK', out, os.path.getsize(out))
