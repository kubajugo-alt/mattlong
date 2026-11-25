"""Crop each talking character's head from the highest-resolution art that matches what the engine shows still.

python3 tools/face_crops.py  -> art/faces/<id>/base.png (1024 px square, on mid-grey) + map.json
map.json gives the crop box in source pixels and how source pixels map into the engine frame (target):
target = source * k + off ; the engine frame is the prop's occ frame (scene object bbox) or Matt's sprite frame.
"""
import json, os, re
import numpy as np
from PIL import Image

idx = open('demo/office-walk/index.html').read()
RIGS = {}
for m in re.finditer(r"'([a-z-]+)':\s*\{ head: \[([^\]]+)\], neck", idx):
    RIGS[m.group(1)] = [float(v) for v in m.group(2).split(',')]

def sheet_frame0(path, cols, rows):
    sh = Image.open(path).convert('RGBA'); fw, fh = sh.width // cols, sh.height // rows
    return sh.crop((0, 0, fw, fh)), [sh.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for r in range(rows) for c in range(cols)]

jobs = []
# props: source image -> room (x, y, scale) -> occ frame (minus bbox origin); animated props use the Ludo frame 0
for room, name, fid in [('pete-kate-flat', 'kate-at-table', 'kate'), ('pete-kate-flat', 'pete-seated', 'pete'), ('tea-house', 'lee-wing', 'lee'),
                        ('pawnshop', 'sol', 'sol'), ('alley', 'junkie', 'junkie'), ('office-night', 'inez-seated', 'inez'), ('doyers-street', 'newsboy', 'newsboy')]:
    L = json.load(open(f'art/rooms/labels/{room}.legend.json')); pr = [p for p in L['props'] if p['name'] == name][0]
    sc = json.load(open(f'art/scenes/{room}/scene.json')); ob = [o for o in sc['objects'] if o['name'] == name][0]
    an = pr['anim']; f0, frames = sheet_frame0(an['sheet'], an['sheet_cols'], an['sheet_rows'])
    src = Image.open(pr['file']).convert('RGBA'); sb = src.getbbox(); fb = f0.getbbox()
    k = (sb[3] - sb[1]) * pr['scale'] / (fb[3] - fb[1])
    ox = pr['x'] + sb[0] * pr['scale'] - fb[0] * k - ob['bbox'][0]; oy = pr['y'] + sb[1] * pr['scale'] - fb[1] * k - ob['bbox'][1]
    fw_, fh_ = ob['bbox'][2] - ob['bbox'][0], ob['bbox'][3] - ob['bbox'][1]
    jobs.append(dict(id=fid, target=f'{room}/{name}', src_img=f0, k=k, off=[ox, oy], frame=[fw_, fh_], rig=RIGS[name], tone=pr.get('tone')))
# Matt: Ludo walk sheet frame 0, packed by tools/pack_sprite.py (union crop of all frames, scaled to figure_h 520)
sp = json.load(open('demo/office-walk/sprites/matt.json'))
for d in ['front', 'side']:
    f0, frames = sheet_frame0(f'art/animations/matt-coat/coat-walk-{d}.webp', 6, 6)
    A = [np.asarray(f)[:, :, 3] > 40 for f in frames]; U = np.any(A, axis=0); ys, xs = np.nonzero(U)
    tallest = max(np.ptp(np.nonzero(a.any(1))[0]) + 1 for a in A); s = 520 / tallest
    jobs.append(dict(id='matt-' + d, target='sprites/' + d, src_img=f0, k=s, off=[-xs.min() * s, -ys.min() * s], frame=[sp[d]['fw'], sp[d]['fh']], rig=RIGS['matt-' + d], tone=None))

for j in jobs:
    hu, hv, hr = j['rig']; fw, fh = j['frame']
    cx, cy, side = hu * fw, hv * fh, 3.6 * hr * fh              # head box in target pixels
    # back to source pixels
    sx0 = (cx - side / 2 - j['off'][0]) / j['k']; sy0 = (cy - side / 2 - j['off'][1]) / j['k']; ss = side / j['k']
    box = [round(sx0), round(sy0), round(sx0 + ss), round(sy0 + ss)]
    crop = j['src_img'].crop(box)
    bg = Image.new('RGBA', crop.size, (128, 128, 128, 255)); bg.alpha_composite(crop)
    os.makedirs(f"art/faces/{j['id']}", exist_ok=True)
    bg.convert('RGB').resize((1024, 1024), Image.LANCZOS).save(f"art/faces/{j['id']}/base.png")
    json.dump({'target': j['target'], 'box_src': box, 'k': j['k'], 'off': j['off'], 'frame': j['frame'], 'tone': j['tone'],
               'note': 'target = source * k + off'}, open(f"art/faces/{j['id']}/map.json", 'w'), indent=1)
    print(j['id'], box, 'source head px', round(ss), 'target head px', round(side))
