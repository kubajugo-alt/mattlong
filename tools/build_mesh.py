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
SP, FT = J['spine'], J['foot']
M = J.get('mesh', {})
STEP = M.get('grid', 28)

S, E, Wr = A['shoulder'], A['elbow'], A['wrist']
hip, knee, ankle, neck = G['hip'], G['knee'], G['ankle'], T['neck']
waist, ball = SP['waist'], FT['ball']

# torso = pelvis (root, turns about the hip joint); chest bends above the waist and carries head and arms
bones = [
    {'id': 'torso', 'parent': None, 'joint': hip},
    {'id': 'chest', 'parent': 'torso', 'joint': waist},
    {'id': 'head', 'parent': 'chest', 'joint': neck},
    {'id': 'thighBack', 'parent': 'torso', 'joint': hip},
    {'id': 'shinBack', 'parent': 'thighBack', 'joint': knee},
    {'id': 'footBack', 'parent': 'shinBack', 'joint': ankle},
    {'id': 'toeBack', 'parent': 'footBack', 'joint': ball},
    {'id': 'upperArmBack', 'parent': 'chest', 'joint': S},
    {'id': 'foreArmBack', 'parent': 'upperArmBack', 'joint': E},
    {'id': 'thigh', 'parent': 'torso', 'joint': hip},
    {'id': 'shin', 'parent': 'thigh', 'joint': knee},
    {'id': 'foot', 'parent': 'shin', 'joint': ankle},
    {'id': 'toe', 'parent': 'foot', 'joint': ball},
    {'id': 'upperArm', 'parent': 'chest', 'joint': S},
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


def limb(name, png, top, bot, j0, j1, j2, blend, root_blend, shade=None, root='torso'):
    """Weights for a whole limb: the part above the first joint stays with the torso
    (so a raised arm stretches the shoulder instead of poking out), the middle follows
    the upper bone, and past the middle joint the lower bone takes over."""
    ox, oy = off[png.replace('.png', '')]
    P, uv, tris = grid_mesh(png, ox, oy)
    lower = smooth(-blend, blend, along(P, j1, j2))
    upper_in = smooth(root_blend[0], root_blend[1], along(P, j0, j1))   # 0 above the root joint
    w = pack([(root, (1 - upper_in) * (1 - lower)), (top, upper_in * (1 - lower)), (bot, lower)])
    m = {'id': name, 'file': png, 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(), 'triangles': tris, 'weights': w}
    if shade:
        m['shade'] = shade
    meshes.append(m)


def leg_chain(name, sfx, shade=None):
    """Thigh, shin, foot and toe on one continuous drawing of the leg and shoe."""
    ox, oy = off['legFull']
    P, uv, tris = grid_mesh('legFull.png', ox, oy)
    r = smooth(-120, 40, along(P, hip, knee))                          # 0 above the hip: stays with the pelvis
    k = smooth(-M.get('knee_blend', 75), M.get('knee_blend', 75), along(P, knee, ankle))
    f = smooth(-FT['ankle_blend'], FT['ankle_blend'], along(P, ankle, [ankle[0] + (ankle[0] - knee[0]), ankle[1] + (ankle[1] - knee[1])]))
    t = smooth(-FT['toe_blend'], FT['toe_blend'], P[:, 0] - ball[0]) * f
    w = pack([('torso', (1 - r) * (1 - k)), ('thigh' + sfx, r * (1 - k)), ('shin' + sfx, k * (1 - f)),
              ('foot' + sfx, k * f * (1 - t / np.maximum(f, 1e-6))), ('toe' + sfx, k * t)])
    hem = smooth(2110, 2190, P[:, 1]) * (1 - smooth(2270, 2300, P[:, 1])) * M.get('hem_jiggle', 0.35)
    m = {'id': name, 'file': 'legFull.png', 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(),
         'triangles': tris, 'weights': w, 'jiggle': np.round(hem, 3).tolist()}
    if shade:
        m['shade'] = shade
    meshes.append(m)


leg_chain('legBack', 'Back', shade=0.72)
farfile = 'farArmFull.png' if 'farArmFull' in off else 'armFull.png'
limb('armBack', farfile, 'upperArmBack', 'foreArmBack', S, E, Wr, M.get('elbow_blend', 60), (-90, 50), shade=0.8, root='chest')
leg_chain('leg', '')

# head: rigid
ox, oy = off['head']
P, uv, tris = grid_mesh('head.png', ox, oy)
meshes.append({'id': 'head', 'file': 'head.png', 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(),
               'triangles': tris, 'weights': pack([('head', np.ones(len(P)))])})

# torso: the jacket skirt below the waist is pulled partly by the thighs and jiggles
ox, oy = off['torso']
P, uv, tris = grid_mesh('torso.png', ox, oy)
skirt_top, hem = M.get('waist_y', 1180), G['hem_y'] + 40
low = smooth(skirt_top, hem, P[:, 1])
front = smooth(hip[0] - 120, hip[0] + 120, P[:, 0])          # front half follows the front leg
pull = M.get('skirt_pull', 0.35) * low
up = 1 - smooth(waist[1] - SP['waist_blend'], waist[1] + SP['waist_blend'], P[:, 1])   # 1 above the waist
w = pack([('chest', up * (1 - pull)), ('torso', (1 - up) * (1 - pull)), ('thigh', pull * front), ('thighBack', pull * (1 - front))])
meshes.append({'id': 'torso', 'file': 'torso.png', 'vertices': P.round(1).tolist(), 'uvs': np.round(uv, 5).tolist(),
               'triangles': tris, 'weights': w, 'jiggle': np.round(low * M.get('jiggle', 1.0), 3).tolist()})

limb('arm', 'armFull.png', 'upperArm', 'foreArm', S, E, Wr, M.get('elbow_blend', 60), (-90, 50), root='chest')

# draw order: back leg, back arm, front leg, head, torso, front arm
order = ['legBack', 'armBack', 'leg', 'head', 'torso', 'arm']
meshes.sort(key=lambda m: order.index(m['id']))
import math


def rot_about(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return [c[0] + ca * x - sa * y, c[1] + sa * x + ca * y]


# angle about the ankle that brings heel and ball contacts level (the drawn shoe stands on its toes a little)
foot_neutral = 0.0
for _ in range(60):
    hc, bc = rot_about(FT['heel_contact'], ankle, foot_neutral), rot_about(FT['ball_contact'], ankle, foot_neutral)
    foot_neutral -= (bc[1] - hc[1]) / 400.0
joints = dict(rig['joints'])
joints.update({'waist': waist, 'ball': ball, 'hand': [round((Wr[0] + A['finger'][0]) / 2), round((Wr[1] + A['finger'][1]) / 2)]})
out = {'height': rig['height'], 'joints': joints, 'groundY': rig['groundY'], 'floorY': J['ground_y'], 'bones': bones, 'meshes': meshes,
       'contacts': {'heel': FT['heel_contact'], 'ball': FT['ball_contact'], 'toe': FT['toe_contact']},
       'footNeutral': round(foot_neutral, 4)}
json.dump(out, open(os.path.join(parts, 'mesh.json'), 'w'), separators=(',', ':'))
print({m['id']: (len(m['vertices']), len(m['triangles']) // 3) for m in meshes}, 'footNeutral deg', round(math.degrees(foot_neutral), 2))
