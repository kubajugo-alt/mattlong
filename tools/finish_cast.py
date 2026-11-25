"""Finish generated cast images: cut out the chroma-green background, remove green spill, force
greyscale (only Inéz's lips may stay red), crop, and build a lineup at real relative heights.

python3 tools/finish_cast.py <dir with <id>.png from Gemini> art/cast
Writes art/cast/final/<id>.png (transparent) and art/cast/lineup*.jpg.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

src, dst = sys.argv[1:3]
cast = json.load(open(os.path.join(dst, 'cast.json')))
os.makedirs(os.path.join(dst, 'final'), exist_ok=True)


def finish(cid, keep_red):
    a = np.asarray(Image.open(os.path.join(src, cid + '.png')).convert('RGB')).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    greenness = g - np.maximum(r, b)                  # how much greener than the other channels
    alpha = np.clip(1 - (greenness - 25) / 70, 0, 1)  # soft key: 25 = fully opaque, 95 = fully clear
    fg = alpha > 0.5
    lab, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.02])
        alpha = alpha * ndimage.binary_dilation(keep, iterations=3)
    # despill, then greyscale by luminance of the despilled colour
    g2 = np.minimum(g, np.maximum(r, b))
    lum = 0.299 * r + 0.587 * g2 + 0.114 * b
    out = np.dstack([lum, lum, lum])
    if keep_red:
        red = (r > 110) & (r > g2 * 1.6) & (r > b * 1.6) & (alpha > 0.5)
        red = ndimage.binary_opening(red, iterations=1)
        out[red] = a[red]
    rgba = np.dstack([out, alpha * 255]).clip(0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 0.05)
    pad = 12
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, a.shape[1]), min(ys.max() + pad, a.shape[0]))
    im = Image.fromarray(rgba, 'RGBA').crop(box)
    im.save(os.path.join(dst, 'final', cid + '.png'), optimize=True)
    return im


def lineup(chars, out, title):
    px_per_cm = 4.2
    ims = []
    for c in chars:
        im = Image.open(os.path.join(dst, 'final', c['id'] + '.png'))
        target = (c['height_cm'] + (9 if c['hat'] else 0)) * px_per_cm
        s = target / im.height
        ims.append((c, im.resize((max(1, int(im.width * s)), int(target)), Image.LANCZOS)))
    H = int(205 * px_per_cm) + 120
    W = sum(i.width for _, i in ims) + 40 * (len(ims) + 1)
    sheet = Image.new('RGBA', (W, H), (34, 33, 38, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
        ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
    except OSError:
        f = ft = None
    base = H - 70
    for cm in range(150, 201, 10):
        y = base - cm * px_per_cm
        d.line((0, y, W, y), fill=(60, 58, 64, 255), width=1)
        d.text((6, y - 24), f'{cm} cm', fill=(110, 106, 116, 255), font=f)
    d.line((0, base, W, base), fill=(90, 88, 96, 255), width=2)
    x = 40
    for c, im in ims:
        sheet.alpha_composite(im, (x, base - im.height))
        name = c['name'].split(' (')[0]
        d.text((x, base + 14), name, fill=(220, 216, 224, 255), font=f)
        x += im.width + 40
    d.text((40, 16), title, fill=(236, 233, 238, 255), font=ft)
    sheet.convert('RGB').save(out, quality=88)


for c in cast['characters']:
    finish(c['id'], c.get('accent') == 'lips')
main = [c for c in cast['characters'] if c['group'] in ('main', 'variant')]
minor = [c for c in cast['characters'] if c['group'] == 'minor']
lineup(main, os.path.join(dst, 'lineup-main.jpg'), 'Matt Long: The Bloody Angle — main cast')
lineup(minor, os.path.join(dst, 'lineup-minor.jpg'), 'Matt Long: The Bloody Angle — minor cast')
print('finished', len(cast['characters']))
