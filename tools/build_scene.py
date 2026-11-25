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


def hull_fill(m):
    """Each separate part of an object filled to its convex outline, so the gaps between a table's
    legs and its chairs' legs count as part of it (for footprints and front lines)."""
    import cv2
    out = np.zeros(m.shape, np.uint8)
    lab_, n = ndimage.label(m)
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab_ == i)
        if len(xs) < 50:
            continue
        hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
        cv2.fillConvexPoly(out, hull, 1)
    return out > 0


def front_line(m):
    """Per column, the lowest y of the object's filled outline (where it meets the floor nearest the camera)."""
    hf = hull_fill(m)
    any_ = hf.any(0)
    low = np.where(any_, H - 1 - np.argmax(hf[::-1], 0), -1)
    return low, hf


# props: character sprites placed in the room (Kate at the table, Pete on his chair). They are not in the
# painting, so the engine always draws them; they block Matt (footprint) and hide him like furniture.
prop_m, prop_rgba = {}, {}
for pr in L.get('props', []):
    im = Image.open(pr['file']).convert('RGBA')
    im = im.resize((round(im.width * pr['scale']), round(im.height * pr['scale'])), Image.LANCZOS)
    full = Image.new('RGBA', (W, H)); full.paste(im, (pr['x'], pr['y']), im)
    a = np.asarray(full)
    prop_m[pr['name']] = a[..., 3] > 128
    prop_rgba[pr['name']] = a
    L.setdefault('islands', []).append(pr['name'])
    L.setdefault('depth_m', {})[pr['name']] = pr.get('depth_m', 0.5)
all_objs = list(L['objects'].items()) + [(pr['name'], None) for pr in L.get('props', [])]
# a prop sits among the painted furniture: wherever a piece of furniture stands nearer the camera than the
# prop (its front line lower, column by column), cut the furniture's pixels out of the prop so the painting
# shows in front (the table legs and edge in front of Kate)
for pname in prop_m:
    plow, _ = front_line(prop_m[pname])
    cut = np.zeros((H, W), bool)
    for oname, ocol in L['objects'].items():
        om = mask_of(ocol)
        if om.sum() < 400:
            continue
        olow, _ = front_line(om)
        nearer = (olow >= 0) & (plow >= 0) & (olow > plow + 6)
        cut |= om & nearer[None, :]
    a = prop_rgba[pname].copy()
    a[..., 3] = (a[..., 3] * (1 - ndimage.gaussian_filter(cut.astype(float), 1.0))).astype(np.uint8)
    prop_rgba[pname] = a
    prop_m[pname] = a[..., 3] > 128


def get_mask(name, color):
    return prop_m[name] if name in prop_m else mask_of(color)


objects = []
for name, color in all_objs:
    m = get_mask(name, color)
    if m.sum() < 400:
        continue
    lab_, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab_, range(1, n + 1))
    m = np.isin(lab_, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.05])
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alpha = ndimage.gaussian_filter(ndimage.binary_dilation(m, iterations=2).astype(float), 1.0)[y0:y1, x0:x1]
    rgba = np.dstack([P[y0:y1, x0:x1], (alpha * 255).astype(np.uint8)])
    if name in prop_rgba:
        rgba = prop_rgba[name][y0:y1, x0:x1].copy()
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, 'occ', name + '.png'), optimize=True)
    # front line per column (lowest y of the filled outline), so sloped counters and legged furniture work:
    # the engine hides Matt behind the object only in the columns where that line is below his feet
    low, _ = front_line(m)
    base = [int(low[x]) if low[x] >= 0 else None for x in range(x0, x1)]
    objects.append({'name': name, 'bbox': [int(x0), int(y0), int(x1), int(y1)], 'baseline': int(y1 - 1),
                    'baseline_cols': base[::8], 'baseline_step': 8, **({'prop': True} if name in prop_m else {})})
exits = {}
for name, e in L.get('exits', {}).items():
    if 'box' in e:      # an exit at the edge of the screen (end of a street): a box in fractions of the image
        bx0, by0, bx1, by1 = e['box']
        bb = [int(bx0 * W), int(by0 * H), int(bx1 * W), int(by1 * H)]
        st = e.get('stand', [(bx0 + bx1) / 2, by1])
        exits[name] = {'to': e.get('to'), 'bbox': bb, 'stand': [int(st[0] * W), int(st[1] * H)], 'edge': True}
        continue
    m = mask_of(e['color'])
    lab_, n = ndimage.label(m)
    if n > 1:           # stray specks of the same colour elsewhere (washing on a line): keep the doorway itself
        sizes = ndimage.sum(m, lab_, range(1, n + 1))
        m = lab_ == (np.argmax(sizes) + 1)
    ys, xs = np.nonzero(m)
    st = [int(np.median(xs)), int(ys.max())]
    if 'stand' in e:
        st = [int(e['stand'][0] * W), int(e['stand'][1] * H)]
    exits[name] = {'to': e.get('to'), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                   'stand': st}
# walkable: the visible floor, shrunk so feet keep clear of furniture and walls
walk = ndimage.binary_erosion(floor, iterations=L.get('clearance_px', 10))
# a little floor in front of each exit is walkable even if the label map clipped it
for e in exits.values():
    if e.get('edge'):
        continue
    x0, _, x1, y1 = e['bbox']
    walk[max(0, y1 - 8):min(H, y1 + 30), x0 + 20:x1 - 20] |= floor[max(0, y1 - 8):min(H, y1 + 30), x0 + 20:x1 - 20] | True
# floor that lies behind a piece of furniture's front line (under a desk, between its legs) is not walkable
for name, color in all_objs:
    m = get_mask(name, color)
    if m.sum() < 400:
        continue
    ys, xs = np.nonzero(m)
    if name in L.get('islands', []):
        # stands out in the room (a table with chairs round it): Matt walks round it, so only its
        # floor-plan footprint blocks him. The floor its picture hides is still floor: in each
        # column, island pixels below the furthest visible floor count as walkable.
        top = np.where(floor.any(0), floor.argmax(0), H)
        hidden = m & (np.arange(H)[:, None] >= top[None, :])
        walk |= ndimage.binary_erosion(floor | hidden, iterations=L.get('clearance_px', 10)) & hidden
        continue
    if name in L.get('column_cut', []):
        # set at an angle (a counter running back into the room): per column, only the floor
        # above the object's lowest painted pixel is behind it
        for x in range(xs.min(), xs.max() + 1):
            col = np.nonzero(m[:, x])[0]
            if len(col):
                walk[:col.max() + 1, x] = False
    else:
        walk[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = False
# hand-marked floor the label map hid (behind a chair's legs), as fractions of the image; footprints still apply
for x0, y0, x1, y1 in L.get('include', []):
    walk[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = True
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
radius = L.get('body_radius_m', 0.25)
pts = []
for name, color in all_objs:
    if name not in depths:
        continue
    m = get_mask(name, color)
    if m.sum() < 400:
        continue
    lab_, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab_, range(1, n + 1))
    m = np.isin(lab_, [i + 1 for i, sz in enumerate(sizes) if sz > sizes.max() * 0.05])
    low, _ = front_line(m)
    # footprint: every column's front point on the floor plan, extended straight back by depth_m
    fp = []
    for x in range(0, W, 4):
        if low[x] < 0 or low[x] <= hor + 2:
            continue
        X, Zf = to_floor(float(x), float(low[x]))
        for z in np.arange(Zf, Zf + depths[name] + 1e-6, 0.04):
            pts.append((X, z))
        fp.append([round(float(X), 3), round(float(Zf), 3)])
    footprints.append({'name': name, 'front': fp, 'depth_m': depths[name]})
from scipy.spatial import cKDTree
blocked = np.zeros((H, W), bool)
if pts:
    tree = cKDTree(np.array(pts))
    g = 2                                   # test every 2nd pixel, then fill in
    yy_, xx_ = np.mgrid[0:H:g, 0:W:g]
    below = yy_ > hor + 2
    FX, FZ = to_floor(xx_.astype(float), yy_.astype(float))
    d, _ = tree.query(np.stack([FX[below], FZ[below]], 1), distance_upper_bound=radius)
    bsmall = np.zeros(yy_.shape, bool); bsmall[below] = np.isfinite(d)
    blocked = np.repeat(np.repeat(bsmall, g, 0), g, 1)[:H, :W]
walk &= ~blocked
# hand-marked areas that are not floor (things the label map missed), as fractions of the image
for x0, y0, x1, y1 in L.get('exclude', []):
    walk[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = False
walk[int(L.get('max_feet_y', 0.96) * H):, :] = False
walk[:int(L.get('min_feet_y', 0.0) * H), :] = False
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
