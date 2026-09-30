"""Generate public/og.png (1200x630 social share image) and public/icon-180.png (apple-touch-icon).
On-brand navy, matching the site's --hero palette. Re-run only when the branding changes.
Requires Pillow.  Usage: python3 scripts/make-og.py
"""
import pathlib, glob
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).resolve().parents[1]
pub = root / 'public'; pub.mkdir(exist_ok=True)

def font(bold, size):
    cands = ([
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    ] if bold else [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ])
    cands += sorted(glob.glob('/usr/share/fonts/**/*.ttf', recursive=True))
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)

# ---- OG image: diagonal navy gradient ----
W, H = 1200, 630
c1, c2 = (0x16, 0x29, 0x4A), (0x2F, 0x4E, 0x7A)   # --hero2 range
img = Image.new('RGB', (W, H), c1)
px = img.load()
for y in range(H):
    for x in range(0, W, 2):
        t = (x / W * 0.55 + y / H * 0.45)
        col = lerp(c1, c2, min(1, t))
        px[x, y] = col
        if x + 1 < W:
            px[x + 1, y] = col
d = ImageDraw.Draw(img)

# HS badge (matches favicon)
rounded(d, (80, 74, 158, 152), 18, (0x0F, 0x17, 0x2A))
fb = font(True, 40)
d.text((119, 113), 'HS', font=fb, fill='white', anchor='mm')

# Title (two lines)
tf = font(True, 92)
d.text((80, 250), 'Nepal HS Code', font=tf, fill='white', anchor='lm')
d.text((80, 350), 'Finder', font=tf, fill='white', anchor='lm')

# Subtitle — auto-shrink to fit within the right margin
sub = 'Customs Tariff 2026/27  ·  Import Duty  ·  VAT  ·  Landed Cost'
maxw = W - 82 - 70
ssz = 40
while ssz > 22:
    sf = font(False, ssz)
    if d.textlength(sub, font=sf) <= maxw:
        break
    ssz -= 2
d.text((82, 452), sub, font=sf, fill=(0xCB, 0xD5, 0xE1))

# Accent underline
d.rounded_rectangle((82, 300, 82 + 120, 300 + 8), radius=4, fill=(0x54, 0x70, 0xC6))

# URL bottom-left
uf = font(True, 34)
d.text((82, 548), 'customsnepal.com', font=uf, fill=(0x9E, 0xB4, 0xE6))

img.save(pub / 'og.png', 'PNG')

# ---- apple-touch-icon 180x180 ----
ic = Image.new('RGB', (180, 180), (0x0F, 0x17, 0x2A))
di = ImageDraw.Draw(ic)
di.text((90, 96), 'HS', font=font(True, 78), fill='white', anchor='mm')
ic.save(pub / 'icon-180.png', 'PNG')

print('wrote public/og.png (1200x630) and public/icon-180.png')
