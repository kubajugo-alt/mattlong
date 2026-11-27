"""Soften Matt's face in every frame of his sheets (tools/soften_face.py, strength 1.0).

Run from a directory holding orig/<sheet>.webp, the unsoftened sheets (git history before this change):
  python3 /path/to/tools/soften_matt_sheets.py
The face is tracked per frame (brows and mouth separately, template match against the standing frame); where it
cannot be found (head bowed, a hand or the flask in front) the change fades out with the match score.
"""
# where Matt's face is in each frame, relative to the standing frame of the same view (translation + match score)
import json, cv2, numpy as np
from PIL import Image
O = 'orig/'; M = json.load(open('/home/user/mattlong/demo/office-walk/sprites/matt.json')); A = json.load(open('/home/user/mattlong/demo/office-walk/sprites/acts.json'))
BOX = {'front': (150, 70, 235, 165), 'side': (282, 68, 352, 150)}     # brows to chin
def frames(name):
    im = np.asarray(Image.open(O + name + '.webp').convert('RGBA')).astype(np.float32); m = A.get(name[4:]) or M[name]
    fw, fh, c = m['fw'], m['fh'], m.get('cols', 6)
    return [im[(f // c) * fh:(f // c + 1) * fh, (f % c) * fw:(f % c + 1) * fw] for f in range(m['frames'])], m
def lum(a): return (a[..., :3].mean(2) * (a[..., 3] / 255) + 128 * (1 - a[..., 3] / 255)).astype(np.float32)
ref = {d: frames(d)[0][0] for d in ['front', 'side']}

REG = {'front': {'brow': (158, 74, 230, 102), 'mouth': (162, 128, 226, 158)}, 'side': {'brow': (296, 72, 345, 100), 'mouth': (305, 120, 346, 150)}}
out = {}
for name in ['front', 'side'] + ['act-' + k for k in A]:
    d = A[name[4:]]['dir'] if name.startswith('act-') else name
    F, m = frames(name); P = 45; out[name] = {'dir': d}
    for part, (x0, y0, x1, y1) in REG[d].items():
        T = lum(ref[d])[y0:y1, x0:x1]; res = []
        for a in F:
            S = lum(a)[y0 - P:y1 + P, x0 - P:x1 + P]
            r = cv2.matchTemplate(S, T, cv2.TM_CCOEFF_NORMED); _, sc, _, loc = cv2.minMaxLoc(r)
            res.append([loc[0] - P, loc[1] - P, round(float(sc), 3)])
        out[name][part] = res
        print(f'{name:14s} {part:5s}', ' '.join(f'{r[2]:.2f}' for r in res))


import json, os, numpy as np, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from soften_face import soften
T = out; D = '/home/user/mattlong/demo/office-walk/sprites/'
M = json.load(open(D + 'matt.json')); A = json.load(open(D + 'acts.json'))
ramp = lambda sc: float(np.clip((sc - 0.6) / 0.25, 0, 1))
log = {}
for name, t in T.items():
    m = A.get(name[4:]) if name.startswith('act-') else M[name]; fw, fh, c = m['fw'], m['fh'], m.get('cols', 6)
    im = np.asarray(Image.open('orig/' + name + '.webp').convert('RGBA')).astype(np.float32); out = im.copy(); ks = []
    for f in range(m['frames']):
        y, x = (f // c) * fh, (f % c) * fw; a = im[y:y + fh, x:x + fw]
        (bx, by, bs), (mx, my, ms) = t['brow'][f], t['mouth'][f]; kb, km = ramp(bs), ramp(ms)
        if kb > 0: a = soften(a, t['dir'], kb, bx, by, ('brow',))
        if km > 0: a = soften(a, t['dir'], km, mx, my, ('mouth',))
        out[y:y + fh, x:x + fw] = a; ks.append((round(kb, 2), round(km, 2)))
    Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(D + name + '.webp', quality=90, method=6)
    log[name] = ks; print(name, 'full:', sum(1 for k in ks if min(k) >= 1), 'partial:', sum(1 for k in ks if 0 < min(k) < 1 or (min(k) == 0 and max(k) > 0)), 'none:', sum(1 for k in ks if max(k) == 0))
json.dump(log, open('applied.json', 'w'))
