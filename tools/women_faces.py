"""Face rigs for the two women at the tea-house table (one sprite, two faces).

python3 tools/women_faces.py
Mouths come from tools/mouth_rig.py (each woman's own mouth, pulled open); the blinks are made here from the eyes'
own pixels: the lid is the skin just above the eye drawn down over it, with the lash line along its edge (Gemini,
which painted the other characters' blinks, isn't used). Writes art/faces/<mei|lan>/face.png + check-rig.png, and
installs demo/office-walk/tea-house/occ/tea-women-face-<who>.webp with `faces` on the scene object.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
import mouth_rig

SRC = 'art/scenes/tea-house/occ/tea-women.png'
FACES = {'mei': {'mouth': [128, 67, 16, 12], 'eyes': [127, 46, 15, 9]},     # left, braided bun, in profile facing right
         'lan': {'mouth': [388, 67, 19, 12], 'eyes': [393, 46, 16, 9]}}     # right, three-quarter, facing left


def blink(frame, rect, cover):
    """Lid over the eye: each eye pixel takes the skin colour interpolated between the skin above and below the eye
    in its column; the lid comes down `cover` of the way; a soft lash line runs along its edge. The patch covers only
    the eye's own dark pixels (feathered), never the whole rect."""
    x, y, w, h = rect; f = frame.astype(np.float32); reg = f[y:y + h, x:x + w].copy()
    lum = reg[..., :3].mean(2)
    above = f[y - 3:y - 1, x:x + w, :3].mean(0); below = f[y + h + 1:y + h + 3, x:x + w, :3].mean(0)
    skinl = np.median(np.r_[above.mean(1), below.mean(1)])
    dark = ndimage.binary_opening(lum < skinl - 22, iterations=0) if False else (lum < skinl - 22)
    lab, n = ndimage.label(dark)
    if n: dark = lab == (np.argmax(ndimage.sum(dark, lab, range(1, n + 1))) + 1)     # the eye: the biggest dark blob
    ys, xs = np.nonzero(dark)
    if not len(ys): return Image.new('RGBA', (w, h))
    top, bot = ys.min(), ys.max(); edge = top + (bot - top + 1) * cover
    # the lid's skin: inpaint the eye from the skin round it (in a margin around the rect, so it has skin to draw on)
    import cv2
    M = 6; big = f[y - M:y + h + M, x - M:x + w + M, :3].clip(0, 255).astype(np.uint8)
    hole = np.zeros(big.shape[:2], np.uint8); hole[M:M + h, M:M + w] = ndimage.binary_dilation(dark, iterations=1)
    skin = cv2.inpaint(big, hole, 4, cv2.INPAINT_TELEA).astype(np.float32)[M:M + h, M:M + w]
    out = reg.copy(); m = np.zeros((h, w), np.float32); eye = ndimage.binary_dilation(dark, iterations=1)
    for j in range(h):
        if j <= edge: out[j, eye[j], :3] = skin[j, eye[j]]; m[j, eye[j]] = 1
    # lash line along the lid's edge, darkest in the middle of the eye
    e = int(min(h - 1, round(edge))); c0, c1 = xs.min(), xs.max()
    for i in range(c0, c1 + 1):
        k = 1 - abs((i - c0) / max(1, c1 - c0) * 2 - 1) * 0.6
        out[e, i, :3] = out[e, i, :3] * (1 - 0.65 * k) + lum[dark].min() * 0.65 * k; m[e, i] = 1
    a = np.clip(ndimage.gaussian_filter(m, 0.9) * 1.4, 0, 1) * 255
    out[..., 3] = np.minimum(reg[..., 3], a)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')


frame_im = Image.open(SRC).convert('RGBA').crop((0, 0, 514, 520)); frame = np.asarray(frame_im)
for who, fc in FACES.items():
    mw, mh = fc['mouth'][2:]; ew, eh = fc['eyes'][2:]
    face = dict(mouth=fc['mouth'], eyes=fc['eyes'], shapes=list('ABCDEFGH'), blink=['half', 'closed'], rows=[0, mh])
    D = f'art/faces/{who}'; os.makedirs(D, exist_ok=True)
    sheet = Image.new('RGBA', (max(8 * mw, 2 * ew), mh + eh))
    for i, c in enumerate([0.55, 1.0]):
        sheet.paste(blink(frame, fc['eyes'], c), (i * ew, mh))
    sheet.save(f'{D}/face.png')
    mouth_rig.TEETH_MIN.setdefault(who, 0.0)
    mouth_rig.run(who, dict(frame=frame_im, face=face))
    json.dump(dict(face, who=who), open(f'{D}/face.json', 'w'))
# install
sc_paths = ['demo/office-walk/tea-house/scene.json', 'art/scenes/tea-house/scene.json']
for sc in sc_paths:
    j = json.load(open(sc)); o = next(o for o in j['objects'] if o['name'] == 'tea-women')
    o['faces'] = [json.load(open(f'art/faces/{w}/face.json')) for w in FACES]
    json.dump(j, open(sc, 'w'), indent=1)
for w in FACES:
    Image.open(f'art/faces/{w}/face.png').save(f'demo/office-walk/tea-house/occ/tea-women-face-{w}.webp', lossless=True)
print('installed', list(FACES))
