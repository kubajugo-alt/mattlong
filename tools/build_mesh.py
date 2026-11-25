"""Turn rig pieces into skinned triangle meshes.

Each drawing (head, torso, whole arm, whole leg) gets a grid of triangles over
its visible pixels. Every vertex is tied to one or more bones with weights, so
limbs bend smoothly through elbows and knees, the jacket skirt is pulled a
little by the thighs, and the lower jacket carries a "jiggle" factor the player
uses for spring-like follow-through.

python3 tools/build_mesh.py <parts dir with rig.json> <joints.json>
Writes <parts dir>/mesh.json. All coordinates are source-image pixels.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

parts, jp = sys.argv[1:3]
rig = json.load(open(os.path.join(parts, 'rig.json')))
J = json.load(open(jp))
off = rig['offsets']
A, G, T = J['arm'], J['leg'], J['torso']
M = J.get('mesh', {})
STEP = M.get('grid', 28)

S, E, Wr = A['shoulder'], A['elbow'], A['wrist']
hip, knee, ankle, neck = G['hip'], G['knee'], G['ankle'], T['neck']

bones = [
    {'id': 'torso', 'parent': None, 'joint': hip},
    {'id': 'head', 'parent': 'torso', 'joint': neck},
    {'id': 'thighBack', 'parent': 'torso', 'joint': hip},
    {'id': 'shinBack', 'parent': 'thighBack', 'joint': knee},
    {'id': 'upperArmBack', 'parent': 'torso', 'joint': S},
    {'id': 'foreArmBack', 'parent': 'upperArmBack', 'joint': E},
    {'id': 'thigh', 'parent': 'torso', 'joint': hip},
    {'id': 'shin', 'parent': 'thigh', 'joint': knee},
    {'id': 'upperArm', 'parent': 'torso', 'joint': S},
    {'id': 'foreArm', 'parent': 'upperArm', 'joint': E},
]
B = {b['id']: i for i, b in enumerate(bones)}


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def along(p, a, b):
    """Signed distance of points p (N,2) past point a, measured along a->b."""
    d = np.array(b, float) - np.array(a, float)
    d /= np.linalg.norm(d)
    return (p - np.array(a, float)) @ d


def grid_mesh(png, ox, oy):
    im = np.asarray(Image.open(os.path.join(parts, png)))
    a = im[..., 3] > 6
    a = ndimage.binary_dilation(a, iterations=3)
    h, w = a.shape
    nx, ny = int(np.ceil(w / STEP)), int(np.ceil(h / STEP))
    vid, verts, uvs, tris = {}, [], [], []

    def v(i, j):
        if (i, j) not in vid:
            x, y = min(i * STEP, w), min(j * STEP, h)
            vid[(i, j)] = len(verts)
            verts.append((x + ox, y + oy))
            uvs.append((x / w, y / h))
        return vid[(i, j)]

    for j in range(ny):
        for i in range(nx):
            if a[j * STEP:(j + 1) * STEP, i * STEP:(i + 1) * STEP].any():
                p00, p10, p01, p11 = v(i, j), v(i + 1, j), v(i, j + 1), v(i + 1, j + 1)
                tris += [p00, p10, p11, p00, p11, p01]
    return np.array(verts, float), uvs, tris


def pack(weights):
    """weights: list of (bone, array) -> per-vertex [[bone, w], ...] normalised."""
    W = np.stack([w for _, w in weights], 1)
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-6)
    out = []
    for row in W:
        out.append([[B[weights[k][0]], round(float(row[k]), 3)] for k in range(len(weights)) if row[k] > 0.004])
    return out


meshes = []


def limb(name, png, top, bot, j0, j1, j2, blend, root_blend, shade=None):
    """Weights for a whole limb: the part above the first joint stays with the torso
    (so a raised arm stretches the shoulder instead of poking out), the middle follows
    the upper bone, and past the middle joint the lower bone takes over."""
    ox, oy = off[png.replace('.png', '')]
    P, uv, tris = grid_mesh(png, ox, oy)
    lower = smooth(-blend, blend, along(P, j1, j2))
    upper_in = smooth(root_blend[0], root_blend[1], along(P, j0, j1))   # 0 above the root joint
    w = pack([('torso', (1 - upper_in) * (1 - lower)), (top, upper_in * (1 - lower)), (bot, lower)])
    m = {'id': name, 'file': png, 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(), 'triangles': tris, 'weights': w}
    if shade:
        m['shade'] = shade
    meshes.append(m)


limb('legBack', 'legFull.png', 'thighBack', 'shinBack', hip, knee, ankle, M.get('knee_blend', 75), (-120, 40), shade=0.72)
farfile = 'farArmFull.png' if 'farArmFull' in off else 'armFull.png'
limb('armBack', farfile, 'upperArmBack', 'foreArmBack', S, E, Wr, M.get('elbow_blend', 60), (-90, 50), shade=0.8)
limb('leg', 'legFull.png', 'thigh', 'shin', hip, knee, ankle, M.get('knee_blend', 75), (-120, 40))

# head: rigid
ox, oy = off['head']
P, uv, tris = grid_mesh('head.png', ox, oy)
meshes.append({'id': 'head', 'file': 'head.png', 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(),
               'triangles': tris, 'weights': pack([('head', np.ones(len(P)))])})

# torso: the jacket skirt below the waist is pulled partly by the thighs and jiggles
ox, oy = off['torso']
P, uv, tris = grid_mesh('torso.png', ox, oy)
waist, hem = M.get('waist_y', 1180), G['hem_y'] + 40
low = smooth(waist, hem, P[:, 1])
front = smooth(hip[0] - 120, hip[0] + 120, P[:, 0])          # front half follows the front leg
pull = M.get('skirt_pull', 0.35) * low
w = pack([('torso', 1 - pull), ('thigh', pull * front), ('thighBack', pull * (1 - front))])
meshes.append({'id': 'torso', 'file': 'torso.png', 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(),
               'triangles': tris, 'weights': w, 'jiggle': np.round(low * M.get('jiggle', 1.0), 3).tolist()})

limb('arm', 'armFull.png', 'upperArm', 'foreArm', S, E, Wr, M.get('elbow_blend', 60), (-90, 50))

# draw order: back leg, back arm, front leg, head, torso, front arm
order = ['legBack', 'armBack', 'leg', 'head', 'torso', 'arm']
meshes.sort(key=lambda m: order.index(m['id']))
out = {'height': rig['height'], 'joints': rig['joints'], 'groundY': rig['groundY'], 'bones': bones, 'meshes': meshes}
json.dump(out, open(os.path.join(parts, 'mesh.json'), 'w'), separators=(',', ':'))
print({m['id']: (len(m['vertices']), len(m['triangles']) // 3) for m in meshes})
