#!/usr/bin/env python3
import argparse, os, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT_B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ap=argparse.ArgumentParser()
ap.add_argument('--product',required=True)
ap.add_argument('--text',required=True)
ap.add_argument('--cta',default='Mehr auf daily-deal-finder.com \u2192')
ap.add_argument('--real',action='store_true')
a=ap.parse_args()
pin=f'assets/pinterest/{a.product}-pin.webp'
odir='backups/pin-originals'; os.makedirs(odir,exist_ok=True)
orig=f'{odir}/{a.product}-pin.webp'
W,H=1024,1536
if a.real:
    src=Image.open(f'data/amazon_reference_images/{a.product}.jpg').convert('RGB')
    bg=Image.new('RGB',(W,H),(255,255,255))
    s=min(W/src.width,(H-300)/src.height,H/src.height)
    fg=src.resize((int(src.width*s),int(src.height*s)),Image.LANCZOS)
    bg.paste(fg,((W-fg.width)//2,max(0,(H-300-fg.height)//2)))
    bg.save(orig,quality=90)
    src.save(f'assets/products/{a.product}.webp',quality=90)
elif not os.path.exists(orig):
    shutil.copy2(pin,orig)
img=Image.open(orig).convert('RGBA').resize((W,H)); pad=56
d=ImageDraw.Draw(img)
def wrap(text,font):
    lines=[];cur=''
    for w in text.split():
        t=(cur+' '+w).strip()
        if d.textlength(t,font=font)<=W-2*pad: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines
size=58
while True:
    f=ImageFont.truetype(FONT_B,size); lines=wrap(a.text,f)
    if len(lines)<=2 or size<=34: break
    size-=4
fc=ImageFont.truetype(FONT_R,34)
lh=int(size*1.25)
band=pad+lh*len(lines)+12+44+pad-10
ov=Image.new('RGBA',(W,H),(0,0,0,0))
ImageDraw.Draw(ov).rectangle([0,H-band,W,H],fill=(7,22,46,215))
img=Image.alpha_composite(img,ov); d=ImageDraw.Draw(img)
y=H-band+pad-10
for ln in lines:
    d.text((pad,y),ln.strip(' ·'),font=f,fill=(255,255,255,255)); y+=lh
d.text((pad,y+12),a.cta,font=fc,fill=(245,168,0,255))
img.convert('RGB').save(pin,quality=90)
print('OK',pin,'real' if a.real else 'keep','size',size,'lines',len(lines))
