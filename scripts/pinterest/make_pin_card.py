# Pin-Karte: Natur-Hintergrund + weisse Karte mit echtem Amazon-Bild + grosse Ueberschrift
import argparse, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('--product', required=True)
ap.add_argument('--text', required=True)
ap.add_argument('--bg', default='wald-see')
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

def font(size):
    return ImageFont.truetype(FONT, size)

bgp = f'assets/pinterest/backgrounds/{a.bg}.jpg'
if not os.path.exists(bgp):
    raise SystemExit('FEHLER: Hintergrund fehlt: ' + bgp)
bg = Image.open(bgp).convert('RGB')
sc = max(W / bg.width, H / bg.height)
bg = bg.resize((int(bg.width * sc) + 1, int(bg.height * sc) + 1), Image.LANCZOS)
l, t = (bg.width - W) // 2, (bg.height - H) // 2
bg = bg.crop((l, t, l + W, t + H)).convert('RGBA')
shade = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade)
top_h, bot_h = int(H * 0.30), int(H * 0.20)
for y in range(top_h):
    sd.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / top_h))))
for y in range(bot_h):
    sd.line([(0, H - 1 - y), (W, H - 1 - y)], fill=(0, 0, 0, int(170 * (1 - y / bot_h))))
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

size = 84
while True:
    f = font(size)
    lines = wrap(a.text, f, W - 2 * PAD)
    if len(lines) <= 3 or size <= 52:
        break
    size -= 4
lh = int(size * 1.22)
y = 70
for ln in lines:
    wd = d.textlength(ln, font=f)
    d.text(((W - wd) / 2 + 2, y + 3), ln, font=f, fill=(0, 0, 0))
    d.text(((W - wd) / 2, y), ln, font=f, fill=(255, 255, 255))
    y += lh
head_bottom = y

ff = font(40)
foot = 'Mehr auf daily-deal-finder.com \u2192'
fw = d.textlength(foot, font=ff)
foot_y = H - 120
d.text(((W - fw) / 2 + 2, foot_y + 2), foot, font=ff, fill=(0, 0, 0))
d.text(((W - fw) / 2, foot_y), foot, font=ff, fill=(255, 214, 10))

src = Image.open(f'data/amazon_reference_images/{a.product}.jpg').convert('RGB')
CP = 14
region_top = head_bottom + 44
region_bot = foot_y - 44
max_w = W - 2 * 16 - 2 * CP
max_h = region_bot - region_top - 2 * CP
s = min(max_w / src.width, max_h / src.height)
fw_, fh_ = int(src.width * s), int(src.height * s)
fg = src.resize((fw_, fh_), Image.LANCZOS)
cw, ch = fw_ + 2 * CP, fh_ + 2 * CP
cx = (W - cw) // 2
cy = region_top + (region_bot - region_top - ch) // 2

sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([cx, cy + 14, cx + cw, cy + ch + 14], radius=30, fill=(0, 0, 0, 120))
sh = sh.filter(ImageFilter.GaussianBlur(22))
out = Image.alpha_composite(bg.convert('RGBA'), sh)
ImageDraw.Draw(out).rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=30, fill=(255, 255, 255, 255))
out.paste(fg, (cx + CP, cy + CP))

pin = f'assets/pinterest/{a.product}-pin.webp'
out.convert('RGB').save(pin, quality=90)
print('OK', pin, 'foto-karte', a.bg, 'size', size, 'lines', len(lines))
