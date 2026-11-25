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

arm_old = arm            # the arm as painted in the master: used to clean the hand off the leg
arm_img = M
if os.path.exists(os.path.join(src, 'arm.png')):
    # a cleanly drawn arm fitted into the master frame (tools/register_arm.py): crisp outline
    arm_img = load('arm.png')
    arm = largest(figure_mask(arm_img))
far_img, far = None, None
if os.path.exists(os.path.join(src, 'fararm.png')):
    far_img = load('fararm.png')
    far = largest(figure_mask(far_img))

el = A['elbow']; rj = A['r_joint']


def split_arm(m):
    up = m & ((side_of(el, A['shoulder'], el) <= 0) | disk(el, rj))
    # round the top off around the shoulder joint so it never pokes out when raised
    up &= (yy >= A['shoulder'][1]) | disk(A['shoulder'], A['r_cap'])
    fo = m & ((side_of(el, el, A['wrist']) >= 0) | disk(el, rj))
    return up, fo


upper, fore = split_arm(arm)
if far is not None:
    upper_far, fore_far = split_arm(far)

# ---- leg: the one-leg edit, with the hand area taken from the no-arm edit
G = J['leg']
leg_img = L.copy()
leg_img[arm_old] = N[arm_old]
leg_mask = (fL & ~arm_old) | (fN & arm_old & fL)
leg = leg_mask & (yy >= G['hem_y'] - 10)
leg = largest(leg)
if os.path.exists(os.path.join(src, 'leg.png')):
    # a cleanly drawn whole leg (hip to sole) fitted into the master frame (tools/register_part.py)
    leg_img = load('leg.png')
    leg = largest(figure_mask(leg_img))
else:
    # fallback: extend the visible thigh up under the jacket to the hip
    top = np.nonzero(leg.any(1))[0].min()
    xs = np.nonzero(leg[top + 4])[0]
    for y in range(G['hip'][1] - 40, top + 4):
        leg[y, xs.min():xs.max() + 1] = True
        leg_img[y, xs.min():xs.max() + 1] = leg_img[top + 4, xs.min():xs.max() + 1]
kn = G['knee']; rk = G['r_joint']
thigh = leg & ((yy <= kn[1]) | disk(kn, rk))
shin = leg & ((yy >= kn[1]) | disk(kn, rk))

# ---- torso and head from the no-arm edit
T = J['torso']
# Cut along the traced top edge of the collar (a polyline in image pixels).
# The head keeps only what is above it (hat, face, neck skin); the torso keeps the collar and below.
px, py = zip(*T['neck_cut'])
cut_y = np.interp(np.arange(W), px, py)[None, :]
if os.path.exists(os.path.join(src, 'torso_only.png')):
    # the jacket with the legs removed: keeps its natural hem, front corner and vent
    torso_img = load('torso_only.png')
    torso = largest(figure_mask(torso_img) & (yy >= cut_y))
else:
    torso_img = N
    torso = largest(fN & (yy >= cut_y) & (yy < G['hem_y'] + T['hem_extra']))
head = largest(fN & (yy < cut_y))
# Hidden neck stub: repeat the skin just above the cut downwards so the neck tucks under the
# collar when the head turns. Only columns across the neck, and only skin, never fabric.
head_img = N.copy()
n0, n1 = T['neck_span']
skin_row = np.array([N[int(cut_y[0, x]) - T['skin_above'], x] for x in range(W)], float)
skin_row = ndimage.gaussian_filter1d(skin_row, 6, axis=0)   # soften outline streaks
for x in range(n0, n1 + 1):
    y = int(cut_y[0, x])
    if not head[y - 3, x]:
        continue
    skin = skin_row[x]
    if not (T['skin_range'][0] <= skin.mean() <= T['skin_range'][1]):
        continue
    head[y - 2:y + T['neck_tuck'], x] = True
    head_img[y - T['skin_above']:y + T['neck_tuck'], x] = skin

def save(name, mask, img, feather=1.2, extra=None):
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(mask, iterations=1).astype(float), feather)
    if extra is not None:
        alpha = alpha * extra
    alpha = alpha[y0:y1, x0:x1]
    rgb = img[y0:y1, x0:x1]
    # strip green spill from edge pixels and force greyscale
    grey = rgb.mean(2, keepdims=True)
    rgba = np.dstack([np.repeat(grey, 3, 2), alpha * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, name + '.png'), optimize=True)
    return [int(x0), int(y0)]


def ramp_from(joint, toward, width, start):
    """0 at `start` px before the joint (measured along joint->toward), rising to 1 over `width` px."""
    d = side_of(joint, joint, toward)
    return np.clip((d + start) / width, 0, 1)


B = J.get('blend', {})
cap_w = B.get('cap_feather', 40)
fore_fade = ramp_from(el, A['wrist'], cap_w, rj)            # forearm cap fades in over the upper arm
shin_fade = ramp_from(G['knee'], G['ankle'], cap_w, G['r_joint'])


def patch(name, mask, img, c, r):
    """A soft disc of the rest-pose drawing around a joint, drawn over both pieces to hide the seam."""
    rr = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2)
    radial = np.clip((r - rr) / (r * B.get('patch_soft', 0.45)), 0, 1)
    radial = radial * radial * (3 - 2 * radial)               # smoothstep
    m = mask & (rr <= r)
    return save(name, m, img, extra=radial)


off = {
    'torso': save('torso', torso, torso_img),
    'head': save('head', head, head_img),
    'upperArm': save('upperArm', upper, arm_img),
    'foreArm': save('foreArm', fore, arm_img, extra=fore_fade),
    'elbowPatch': patch('elbowPatch', arm, arm_img, el, B.get('elbow_patch_r', 85)),
    'thigh': save('thigh', thigh, leg_img),
    'shin': save('shin', shin, leg_img, extra=shin_fade),
    'kneePatch': patch('kneePatch', leg, leg_img, G['knee'], B.get('knee_patch_r', 120)),
}
if far is not None:
    off['upperArmFar'] = save('upperArmFar', upper_far, far_img)
    off['foreArmFar'] = save('foreArmFar', fore_far, far_img, extra=fore_fade)
    off['elbowPatchFar'] = patch('elbowPatchFar', far, far_img, el, B.get('elbow_patch_r', 85))
far_u = 'upperArmFar' if far is not None else 'upperArm'
far_f = 'foreArmFar' if far is not None else 'foreArm'
far_p = 'elbowPatchFar' if far is not None else 'elbowPatch'


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
        {'id': 'kneeBack', 'file': 'kneePatch.png', 'parent': 'thighBack', 'at': local(knee, 'thigh'), 'pivot': local(knee, 'kneePatch'), 'z': 1.5, 'shade': 0.72, 'follow': {'of': 'shinBack', 'k': 0.5}},
        {'id': 'upperArmBack', 'file': far_u + '.png', 'parent': 'torso', 'at': local(S, 'torso'), 'pivot': local(S, far_u), 'z': 2, 'shade': 0.8},
        {'id': 'foreArmBack', 'file': far_f + '.png', 'parent': 'upperArmBack', 'at': local(E, far_u), 'pivot': local(E, far_f), 'z': 3, 'shade': 0.8},
        {'id': 'elbowBack', 'file': far_p + '.png', 'parent': 'upperArmBack', 'at': local(E, far_u), 'pivot': local(E, far_p), 'z': 3.5, 'shade': 0.8, 'follow': {'of': 'foreArmBack', 'k': 0.5}},
        {'id': 'thigh', 'file': 'thigh.png', 'parent': 'torso', 'at': local(hip, 'torso'), 'pivot': local(hip, 'thigh'), 'z': 4},
        {'id': 'shin', 'file': 'shin.png', 'parent': 'thigh', 'at': local(knee, 'thigh'), 'pivot': local(knee, 'shin'), 'z': 5},
        {'id': 'knee', 'file': 'kneePatch.png', 'parent': 'thigh', 'at': local(knee, 'thigh'), 'pivot': local(knee, 'kneePatch'), 'z': 5.5, 'follow': {'of': 'shin', 'k': 0.5}},
        {'id': 'head', 'file': 'head.png', 'parent': 'torso', 'at': local(neck, 'torso'), 'pivot': local(neck, 'head'), 'z': 6},
        {'id': 'torso', 'file': 'torso.png', 'parent': None, 'at': [0, 0], 'pivot': local(hip, 'torso'), 'z': 7},
        {'id': 'upperArm', 'file': 'upperArm.png', 'parent': 'torso', 'at': local(S, 'torso'), 'pivot': local(S, 'upperArm'), 'z': 8},
        {'id': 'foreArm', 'file': 'foreArm.png', 'parent': 'upperArm', 'at': local(E, 'upperArm'), 'pivot': local(E, 'foreArm'), 'z': 9},
        {'id': 'elbow', 'file': 'elbowPatch.png', 'parent': 'upperArm', 'at': local(E, 'upperArm'), 'pivot': local(E, 'elbowPatch'), 'z': 9.5, 'follow': {'of': 'foreArm', 'k': 0.5}},
    ],
    'joints': {k: v for k, v in [('shoulder', S), ('elbow', E), ('wrist', Wr), ('neck', neck), ('hip', hip), ('knee', knee), ('ankle', ankle)]},
}
json.dump(rig, open(os.path.join(out, 'rig.json'), 'w'), indent=1)
print(json.dumps({k: off[k] for k in off}))
