"""Make the teacup on Pete and Kate's table something Matt can pick up.

python3 tools/teacup_patch.py
The cup is painted into both table sprites (kate-at-table: 36 animation frames; table-set-empty). Gemini painted
the table top without it (art/props/teacup/*-clean.png, from a 240x240 crop at `crop`). This pastes the clean
table into every frame, inside a feathered ellipse round the cup, and cuts the original cup out as its own
sprite (occ/teacup-kate.png, occ/teacup-empty.png), which the game hides when Matt takes it.
Reads the *.orig.png copies it keeps, so it can be run again.
"""
import json, os, shutil
import numpy as np
from PIL import Image
from scipy import ndimage

D = 'art/scenes/pete-kate-flat'
JOBS = [  # sprite, clean image, crop origin (local), cup box (local), cup sprite name
    ('kate-at-table', 'art/props/teacup/kate-table-clean.png', (577, 100), (686, 178, 784, 236), 'teacup-kate'),
    ('table-set-empty', 'art/props/teacup/empty-table-clean.png', (574, 10), (688, 103, 788, 163), 'teacup-empty'),
]
sc_p = f'{D}/scene.json'; sc = json.load(open(sc_p))
objs = {o['name']: o for o in sc['objects']}
for name, clean_p, (cx, cy), (x0, y0, x1, y1), cup_name in JOBS:
    src = f'{D}/occ/{name}.png'; orig = f'{D}/occ/{name}.orig.png'
    if not os.path.exists(orig): shutil.copy(src, orig)
    sheet = np.asarray(Image.open(orig).convert('RGBA')).astype(np.float32)
    o = objs[name]; fw, fh = o['bbox'][2] - o['bbox'][0], o['bbox'][3] - o['bbox'][1]
    cols = o.get('anim', {}).get('cols', 1); n = o.get('anim', {}).get('frames', 1)
    clean = np.asarray(Image.open(clean_p).convert('RGB').resize((240, 240), Image.LANCZOS)).astype(np.float32)
    # where the clean picture is the flat grey ground, the sprite is transparent (the cup stood up past the table's edge)
    flat = (np.abs(clean - 128).max(2) < 7) & (ndimage.generic_filter(clean.mean(2), np.std, 5) < 2.5)
    # the region to replace: an ellipse round the cup, feathered
    yy, xx = np.mgrid[0:fh, 0:fw]
    ex, ey, ax, ay = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 6, (y1 - y0) / 2 + 6
    m = np.clip((1 - np.sqrt(((xx - ex) / ax) ** 2 + ((yy - ey) / ay) ** 2)) * 6, 0, 1)
    # tone match on a ring just outside the ellipse, frame 0
    f0 = sheet[0:fh, 0:fw]
    ring = (m == 0) & (np.sqrt(((xx - ex) / (ax + 10)) ** 2 + ((yy - ey) / (ay + 10)) ** 2) < 1) & (f0[..., 3] > 250)
    big = np.zeros((fh, fw, 3), np.float32); big[cy:cy + 240, cx:cx + 240] = clean[:fh - cy, :fw - cx]
    bgm = np.zeros((fh, fw), bool); bgm[cy:cy + 240, cx:cx + 240] = flat[:fh - cy, :fw - cx]
    gain = f0[..., :3][ring].mean(0) / np.maximum(1, big[ring].mean(0))
    big = np.clip(big * gain, 0, 255)
    # the cup sprite: the original pixels inside the ellipse
    cup = f0.copy(); cup[..., 3] *= m
    bb = (x0 - 8, y0 - 8, x1 + 8, y1 + 8)
    Image.fromarray(cup.clip(0, 255).astype(np.uint8)).crop(bb).save(f'{D}/occ/{cup_name}.png')
    out = sheet.copy()
    for i in range(n):
        ox, oy = (i % cols) * fw, (i // cols) * fh
        fr = out[oy:oy + fh, ox:ox + fw]
        a_new = np.where(bgm, 0, fr[..., 3])
        fr[..., :3] = fr[..., :3] * (1 - m[..., None]) + big * m[..., None]
        fr[..., 3] = fr[..., 3] * (1 - m) + a_new * m
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(src)
    # the cup as its own object, drawn just after the table, gone once taken (or with the other table version)
    gx, gy = o['bbox'][0] + bb[0], o['bbox'][1] + bb[1]
    objs[cup_name] = {'name': cup_name, 'bbox': [gx, gy, gx + bb[2] - bb[0], gy + bb[3] - bb[1]], 'baseline': o['baseline'] + 1,
                      'prop': True, 'no_shadow': True, 'with': 'kate' if name == 'kate-at-table' else 'nokate'}
    print(name, n, 'frames patched;', cup_name, objs[cup_name]['bbox'])
names = [x['name'] for x in sc['objects'] if x['name'] not in ('teacup-kate', 'teacup-empty')]
order = []
for nm in names:
    order.append(objs[nm])
    if nm == 'kate-at-table': order += [objs['teacup-kate'], objs['teacup-empty']]
sc['objects'] = order
json.dump(sc, open(sc_p, 'w'), indent=1)
