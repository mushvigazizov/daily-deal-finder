# Pin aus fertigem Szenenfoto: Foto vollflaechig + Ueberschrift oben + Seitenname unten
import argparse, os
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument('--product', required=True)
ap.add_argument('--text', required=True)
ap.add_argument('--photo', required=True)
ap.add_argument('--out')
a = ap.parse_args()

W, H = 1024, 1536
PAD = 64
FONTS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
]
FONT = next((f for f in FONTS if os.path.exists(f)), None)
if not FONT:
    raise SystemExit('FEHLER: keine Schrift gefunden')
if not os.path.exists(a.photo):
    raise SystemExit('FEHLER: Foto fehlt: ' + a.photo)

def font(size):
    return ImageFont.truetype(FONT, size)

bg = Image.open(a.photo).convert('RGB')
sc = max(W / bg.width, H / bg.height)
bg = bg.resize((int(bg.width * sc) + 1, int(bg.height * sc) + 1), Image.LANCZOS)
l, t = (bg.width - W) // 2, (bg.height - H) // 2
bg = bg.crop((l, t, l + W, t + H)).convert('RGBA')
shade = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade)
top_h, bot_h = int(H * 0.26), int(H * 0.16)
for y in range(top_h):
    sd.line([(0, y), (W, y)], fill=(0, 0, 0, int(165 * (1 - y / top_h))))
for y in range(bot_h):
    sd.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, int(185 * (1 - y / bot_h))))
bg = Image.alpha_composite(bg, shade).convert('RGB')
d = ImageDraw.Draw(bg)

def wrap(text, f, maxw):
    lines, cur = [], ''
    for w in text.split():
        tt = (cur + ' ' + w).strip()
        if d.textlength(tt, font=f) <= maxw:
            cur = tt
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

size = 80
while True:
    f = font(size)
    lines = wrap(a.text, f, W - 2 * PAD)
    if len(lines) <= 3 or size <= 52:
        break
    size -= 4
lh = int(size * 1.2)
y = 56
for ln in lines:
    wd = d.textlength(ln, font=f)
    d.text(((W - wd) / 2 + 2, y + 3), ln, font=f, fill=(0, 0, 0))
    d.text(((W - wd) / 2, y), ln, font=f, fill=(255, 255, 255))
    y += lh

ff = font(40)
foot = 'Mehr auf daily-deal-finder.com \u2192'
fw = d.textlength(foot, font=ff)
foot_y = H - 96
d.text(((W - fw) / 2 + 2, foot_y + 2), foot, font=ff, fill=(0, 0, 0))
d.text(((W - fw) / 2, foot_y), foot, font=ff, fill=(255, 214, 10))

pin = a.out or f'assets/pinterest/{a.product}-pin.webp'
bg.save(pin, quality=90)
print('OK', pin, 'szene', os.path.basename(a.photo), 'size', size, 'lines', len(lines))
