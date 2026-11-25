"""Turn detected object masks into a curated hotspot list for a scene.

python3 tools/build_hotspots.py <segment dir> <scene dir> <labels.png> <legend.json> <curation.json>

- Furniture uses the exact shapes from the flat-colour label map (legend 'objects'), named
  through curation 'from_label_map' (hotspot id -> label-map object).
- Everything else uses the detected mask (or its box where the outline failed).
- curation: 'drop' (ids), 'rename' (old -> new id), 'names' (id -> display name), 'merge'
  (id -> [ids folded into it]).
Each hotspot gets polygons (simplified outlines, scene pixels), a bbox, an area and a 'z' so the
smallest hotspot under the cursor wins. Writes <scene dir>/hotspots.json and hotspots.md.
"""
import json, os, sys
import numpy as np
import cv2
from PIL import Image

seg, scene, labels_p, legend_p, cur_p = sys.argv[1:6]
objs = json.load(open(os.path.join(seg, 'objects.json')))
L = json.load(open(legend_p)); C = json.load(open(cur_p))
W, H = objs['size']
lab = np.asarray(Image.open(labels_p).convert('RGB').resize((W, H), Image.NEAREST)).astype(int)


def label_mask(name):
    h = L['objects'][name].lstrip('#'); c = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    m = (np.abs(lab - c).sum(2) < 70).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m > 0


masks = {}
for o in objs['objects']:
    masks[o['id']] = np.asarray(Image.open(os.path.join(seg, 'masks', o['id'] + '.png'))) > 0
for hid, src in C.get('merge', {}).items():
    for s in src:
        if s in masks:
            masks[hid] = masks.get(hid, np.zeros((H, W), bool)) | masks.pop(s)
for d in C.get('drop', []):
    masks.pop(d, None)
for old, new in C.get('rename', {}).items():
    if old in masks:
        masks[new] = masks.pop(old)
for hid, name in C.get('from_label_map', {}).items():
    m = label_mask(name)
    if m.sum() > 200:
        masks[hid] = m


def polygons(m):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) < max(40, 0.03 * m.sum()):
            continue
        p = cv2.approxPolyDP(c, 2.0, True)[:, 0, :]
        if len(p) >= 3:
            out.append(p.tolist())
    return out


hs = []
for hid, m in masks.items():
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        continue
    polys = polygons(m)
    if not polys:
        continue
    hs.append({'id': hid, 'name': C.get('names', {}).get(hid, hid.replace('-', ' ')),
               'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], 'area_px': int(m.sum()), 'polygons': polys})
hs.sort(key=lambda h: h['area_px'])
for i, h in enumerate(hs):
    h['z'] = len(hs) - i            # smaller objects sit on top for clicking
json.dump({'size': [W, H], 'note': 'No actions yet. Smallest hotspot under the cursor wins (highest z).', 'hotspots': sorted(hs, key=lambda h: h['bbox'][0])},
          open(os.path.join(scene, 'hotspots.json'), 'w'), indent=1)
with open(os.path.join(scene, 'hotspots.md'), 'w') as f:
    f.write(f'# Hotspots ({len(hs)})\n\nNo actions yet. Listed left to right; positions in scene pixels ({W}x{H}).\n\n| # | id | name | bbox (x0, y0, x1, y1) |\n|---|---|---|---|\n')
    for i, h in enumerate(sorted(hs, key=lambda h: h['bbox'][0])):
        f.write(f"| {i + 1} | `{h['id']}` | {h['name']} | {', '.join(map(str, h['bbox']))} |\n")
print(len(hs), 'hotspots')
