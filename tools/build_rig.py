"""Cut a character into cut-out rig pieces from aligned Gemini edits.

Inputs (same framing, chroma-green background):
  master.png   full figure, strict side profile
  noarm.png    same image with the near arm removed (torso painted in)
  oneleg.png   same image with the far leg removed
and a joints JSON with image-space points (shoulder, elbow, wrist, finger,
neck, hip, knee, ankle) plus a few cut lines.

Every piece keeps its position from the master image, so the rest pose
rebuilds the original picture exactly; pivots sit on the real joints.

python3 tools/build_rig.py <dir with the three images> <joints.json> <out dir>
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, joints_path, out = sys.argv[1:4]
J = json.load(open(joints_path))
os.makedirs(out, exist_ok=True)


def load(n):
    return np.asarray(Image.open(os.path.join(src, n)).convert('RGB')).astype(int)


def figure_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = ~((g > 140) & (g - r > 60) & (g - b > 60))
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    s = ndimage.sum(m, lab, range(1, n + 1))
    return ndimage.binary_fill_holes(lab == (np.argmax(s) + 1))


M, N, L = load('master.png'), load('noarm.png'), load('oneleg.png')
fM, fN, fL = figure_mask(M), figure_mask(N), figure_mask(L)
H, W = fM.shape
yy, xx = np.mgrid[0:H, 0:W]


def capsule(a, b, r):
    a, b = np.array(a, float), np.array(b, float)
    ab = b - a
    t = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / (ab @ ab), 0, 1)
    return (xx - a[0] - t * ab[0]) ** 2 + (yy - a[1] - t * ab[1]) ** 2 <= r * r


def disk(c, r):
    return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r


def side_of(p, axis_a, axis_b):
    """Signed distance along the bone axis from point p (positive = towards b)."""
    a, b = np.array(axis_a, float), np.array(axis_b, float)
    d = (b - a) / np.linalg.norm(b - a)
    return (xx - p[0]) * d[0] + (yy - p[1]) * d[1]


def largest(m):
    lab, n = ndimage.label(m)
    if n == 0:
        return m
    s = ndimage.sum(m, lab, range(1, n + 1))
    return lab == (np.argmax(s) + 1)


# ---- arm: what changed between master and noarm, inside capsules around the bones
A = J['arm']
cap = (capsule((A['shoulder'][0], A['shoulder'][1] - 90), A['elbow'], A['r_upper'])
       | capsule(A['elbow'], A['wrist'], A['r_fore'])
       | capsule(A['wrist'], A['finger'], A['r_hand']))
diff = np.abs(M - N).mean(2) > 14
arm = fM & cap & (diff | ~fN) & (yy <= A['max_y'])
arm = ndimage.binary_fill_holes(ndimage.binary_closing(arm, iterations=5))
arm = largest(ndimage.binary_opening(arm, iterations=3))

el = A['elbow']; rj = A['r_joint']
upper = arm & ((side_of(el, A['shoulder'], el) <= 0) | disk(el, rj))
# round the top of the upper arm off around the shoulder joint so it never pokes out when raised
upper &= (yy >= A['shoulder'][1]) | disk(A['shoulder'], A['r_cap'])
fore = arm & ((side_of(el, el, A['wrist']) >= 0) | disk(el, rj))

# ---- leg: the one-leg edit, with the hand area taken from the no-arm edit
G = J['leg']
leg_img = L.copy()
leg_img[arm] = N[arm]
leg_mask = (fL & ~arm) | (fN & arm & fL)
leg = leg_mask & (yy >= G['hem_y'] - 10)
leg = largest(leg)
# extend the thigh up under the jacket to the hip so it never shows a gap
top = np.nonzero(leg.any(1))[0].min()
row = leg[top + 4]
xs = np.nonzero(row)[0]
for y in range(G['hip'][1] - 40, top + 4):
    leg[y, xs.min():xs.max() + 1] = True
    leg_img[y, xs.min():xs.max() + 1] = leg_img[top + 4, xs.min():xs.max() + 1]
kn = G['knee']; rk = G['r_joint']
thigh = leg & ((yy <= kn[1]) | disk(kn, rk))
shin = leg & ((yy >= kn[1]) | disk(kn, rk))

# ---- torso and head from the no-arm edit
T = J['torso']
# cut along the collar: a line from the back of the collar to the throat
(cx0, cy0), (cx1, cy1) = T['collar_line']
slope = (cy1 - cy0) / (cx1 - cx0)
collar_y = cy0 + np.clip(xx - cx0, 0, None) * slope
torso = fN & (yy >= collar_y) & (yy < G['hem_y'] + T['hem_extra'])
torso = largest(torso)
head = fN & (yy < collar_y + T['neck_tuck'])
head = largest(head)


def save(name, mask, img, feather=1.2):
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(mask, iterations=1).astype(float), feather)[y0:y1, x0:x1]
    rgb = img[y0:y1, x0:x1]
    # strip green spill from edge pixels and force greyscale
    grey = rgb.mean(2, keepdims=True)
    rgba = np.dstack([np.repeat(grey, 3, 2), alpha * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, name + '.png'), optimize=True)
    return [int(x0), int(y0)]


off = {
    'torso': save('torso', torso, N),
    'head': save('head', head, N),
    'upperArm': save('upperArm', upper, M),
    'foreArm': save('foreArm', fore, M),
    'thigh': save('thigh', thigh, leg_img),
    'shin': save('shin', shin, leg_img),
}


def local(p, part):
    return [round(p[0] - off[part][0], 1), round(p[1] - off[part][1], 1)]


S, E, Wr = A['shoulder'], A['elbow'], A['wrist']
hip, knee, ankle, neck = G['hip'], G['knee'], G['ankle'], T['neck']
rig = {
    'name': J.get('name', 'character'),
    'height': J['height'],
    'groundY': J['ground_y'] - hip[1],
    'root': 'torso',
    'parts': [
        {'id': 'thighBack', 'file': 'thigh.png', 'parent': 'torso', 'at': local(hip, 'torso'), 'pivot': local(hip, 'thigh'), 'z': 0, 'shade': 0.72},
        {'id': 'shinBack', 'file': 'shin.png', 'parent': 'thighBack', 'at': local(knee, 'thigh'), 'pivot': local(knee, 'shin'), 'z': 1, 'shade': 0.72},
        {'id': 'upperArmBack', 'file': 'upperArm.png', 'parent': 'torso', 'at': local(S, 'torso'), 'pivot': local(S, 'upperArm'), 'z': 2, 'shade': 0.68},
        {'id': 'foreArmBack', 'file': 'foreArm.png', 'parent': 'upperArmBack', 'at': local(E, 'upperArm'), 'pivot': local(E, 'foreArm'), 'z': 3, 'shade': 0.68},
        {'id': 'thigh', 'file': 'thigh.png', 'parent': 'torso', 'at': local(hip, 'torso'), 'pivot': local(hip, 'thigh'), 'z': 4},
        {'id': 'shin', 'file': 'shin.png', 'parent': 'thigh', 'at': local(knee, 'thigh'), 'pivot': local(knee, 'shin'), 'z': 5},
        {'id': 'head', 'file': 'head.png', 'parent': 'torso', 'at': local(neck, 'torso'), 'pivot': local(neck, 'head'), 'z': 6},
        {'id': 'torso', 'file': 'torso.png', 'parent': None, 'at': [0, 0], 'pivot': local(hip, 'torso'), 'z': 7},
        {'id': 'upperArm', 'file': 'upperArm.png', 'parent': 'torso', 'at': local(S, 'torso'), 'pivot': local(S, 'upperArm'), 'z': 8},
        {'id': 'foreArm', 'file': 'foreArm.png', 'parent': 'upperArm', 'at': local(E, 'upperArm'), 'pivot': local(E, 'foreArm'), 'z': 9},
    ],
    'joints': {k: v for k, v in [('shoulder', S), ('elbow', E), ('wrist', Wr), ('neck', neck), ('hip', hip), ('knee', knee), ('ankle', ankle)]},
}
json.dump(rig, open(os.path.join(out, 'rig.json'), 'w'), indent=1)
print(json.dumps({k: off[k] for k in off}))
