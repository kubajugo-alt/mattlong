"""Build engine scene data for a room from its painting and an aligned flat-colour label map.

python3 tools/build_scene.py <room.png> <labels.png> <legend.json> <out dir>

legend.json: {"horizon": 0.40, "floor": "#00FF00", "objects": {"couch": "#FF0000", ...},
              "exits": {"door": {"color": "#FFFFFF", "to": "doyers-street"}}}

Writes:
  bg.png                       the painting (greyscale)
  occ/<name>.png               each object cut out of the painting (transparent elsewhere)
  walk.png                     walkable floor mask (white = walkable), at 1/4 resolution
  scene.json                   size, horizon, scale rule, objects with bbox and baseline, exits

Depth: a character of height h metres with feet at y is (y - horizon) * h / 1.6 pixels tall
(eye line 1.6 m above the floor). Occlusion: an object is drawn in front of a character when
its baseline (the lowest y where it stands on the floor) is below the character's feet.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

room, labels, legend_p, out = sys.argv[1:5]
L = json.load(open(legend_p))
os.makedirs(os.path.join(out, 'occ'), exist_ok=True)
img = Image.open(room).convert('L').convert('RGB')
lab = Image.open(labels).convert('RGB').resize(img.size, Image.NEAREST)
W, H = img.size
A = np.asarray(lab).astype(int)
P = np.asarray(img)


def hexrgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])


def mask_of(color, tol=70):
    m = np.abs(A - hexrgb(color)).sum(2) < tol
    m = ndimage.binary_opening(m, iterations=2)
    return ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3))


img.save(os.path.join(out, 'bg.png'), optimize=True)
floor = mask_of(L['floor'])
objects = []
for name, color in L['objects'].items():
    m = mask_of(color)
    if m.sum() < 400:
        continue
    lab_, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab_, range(1, n + 1))
    m = np.isin(lab_, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.05])
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alpha = ndimage.gaussian_filter(ndimage.binary_dilation(m, iterations=2).astype(float), 1.0)[y0:y1, x0:x1]
    rgba = np.dstack([P[y0:y1, x0:x1], (alpha * 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, 'occ', name + '.png'), optimize=True)
    # baseline per column: lowest painted pixel of the object in that column, so sloped bases work
    cols = m[:, x0:x1]
    base = [int(np.nonzero(cols[:, i])[0].max()) if cols[:, i].any() else None for i in range(x1 - x0)]
    objects.append({'name': name, 'bbox': [int(x0), int(y0), int(x1), int(y1)], 'baseline': int(y1 - 1),
                    'baseline_cols': base[::8], 'baseline_step': 8})
exits = {}
for name, e in L.get('exits', {}).items():
    m = mask_of(e['color'])
    ys, xs = np.nonzero(m)
    exits[name] = {'to': e.get('to'), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                   'stand': [int(np.median(xs)), int(ys.max())]}
# walkable: the visible floor, shrunk so feet keep clear of furniture and walls
walk = ndimage.binary_erosion(floor, iterations=L.get('clearance_px', 10))
# a little floor in front of each exit is walkable even if the label map clipped it
for e in exits.values():
    x0, _, x1, y1 = e['bbox']
    walk[max(0, y1 - 8):min(H, y1 + 30), x0 + 20:x1 - 20] |= floor[max(0, y1 - 8):min(H, y1 + 30), x0 + 20:x1 - 20] | True
# floor that lies behind a piece of furniture's front line (under a desk, between its legs) is not walkable
for name, color in L['objects'].items():
    m = mask_of(color)
    if m.sum() < 400:
        continue
    ys, xs = np.nonzero(m)
    walk[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = False
# ---- FLOOR PLAN: solid furniture footprints in metres, and Matt's body radius
# Camera: eye 1.6 m above the floor, horizon at L['horizon'], focal length f px (from an assumed
# horizontal field of view). A floor pixel (x, y) is at depth Z = f*1.6/(y - hor) and X = (x - W/2)*Z/f.
fov = L.get('fov_deg', 60.0)
f_px = (W / 2) / np.tan(np.radians(fov / 2))
hor = L['horizon'] * H
def to_floor(x, y):
    Z = f_px * 1.6 / np.maximum(y - hor, 1e-3)
    return (x - W / 2) * Z / f_px, Z
footprints = []
depths = L.get('depth_m', {})
for name, color in L['objects'].items():
    if name not in depths:
        continue
    m = mask_of(color)
    if m.sum() < 400:
        continue
    ys, xs = np.nonzero(m)
    base = ys.max()
    X0, Zf = to_floor(xs.min(), base); X1, _ = to_floor(xs.max(), base)
    footprints.append({'name': name, 'x0': float(X0), 'x1': float(X1), 'z0': float(Zf), 'z1': float(Zf + depths[name])})
radius = L.get('body_radius_m', 0.25)
yy_, xx_ = np.mgrid[0:H, 0:W]
FX, FZ = to_floor(xx_.astype(float), yy_.astype(float))
blocked = np.zeros((H, W), bool)
for fp in footprints:
    dx = np.maximum(np.maximum(fp['x0'] - FX, FX - fp['x1']), 0)
    dz = np.maximum(np.maximum(fp['z0'] - FZ, FZ - fp['z1']), 0)
    blocked |= np.hypot(dx, dz) < radius
walk &= ~blocked
# hand-marked areas that are not floor (things the label map missed), as fractions of the image
for x0, y0, x1, y1 in L.get('exclude', []):
    walk[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = False
walk[int(L.get('max_feet_y', 0.96) * H):, :] = False
walk = ndimage.binary_opening(walk, iterations=2)
lab_, n = ndimage.label(walk)
sizes = ndimage.sum(walk, lab_, range(1, n + 1))
walk = lab_ == (np.argmax(sizes) + 1)        # one connected floor
small = Image.fromarray((walk * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.NEAREST)
small.save(os.path.join(out, 'walk.png'))
# the whole visible floor (not shrunk): shadows may fall anywhere on it, never on furniture or walls
Image.fromarray((floor * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.NEAREST).save(os.path.join(out, 'floor.png'))
scene = {'size': [W, H], 'horizon': L['horizon'], 'eye_m': 1.6,
         'scale_rule': 'height_px = (feet_y - horizon*H) * height_m / eye_m',
         'walk': {'file': 'walk.png', 'scale': 4}, 'camera': {'f_px': float(f_px), 'eye_m': 1.6}, 'footprints': footprints, 'body_radius_m': radius, 'floor': {'file': 'floor.png', 'scale': 4}, 'lights': L.get('lights', []), 'spots': L.get('spots', {}), 'objects': sorted(objects, key=lambda o: o['baseline']), 'exits': exits}
json.dump(scene, open(os.path.join(out, 'scene.json'), 'w'), indent=1)
print(json.dumps({o['name']: o['baseline'] for o in objects}), 'walkable px', int(walk.sum()), 'exits', list(exits))
