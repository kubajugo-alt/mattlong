"""Fit a cleanly drawn, free-floating limb back onto the same limb in the master picture.

Gemini redraws an isolated limb well but not in place (it rescales and moves
it). This finds the scale, rotation and offset that best overlay the clean
limb's outline on the limb's outline in the master, then warps the clean
limb (and any companion drawn in the same frame, like the far arm) into the
master's pixel frame.

python3 tools/register_part.py <source dir> <joints.json> arm
  reads  master.png, noarm.png, arm_free.png [, fararm_free.png]
  writes arm.png [, fararm.png]
python3 tools/register_part.py <source dir> <joints.json> leg
  reads  oneleg.png, leg_free.png; matches only the leg below the jacket hem
  writes leg.png
Output images are in the master frame on a green background.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage, optimize

src, jp = sys.argv[1:3]
mode = sys.argv[3] if len(sys.argv) > 3 else 'arm'
J = json.load(open(jp))
A = J['arm']
GREEN = (0, 255, 0)


def load(n):
    return np.asarray(Image.open(os.path.join(src, n)).convert('RGB')).astype(int)


def fmask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = ~((g > 140) & (g - r > 60) & (g - b > 60))
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    s = ndimage.sum(m, lab, range(1, n + 1))
    return ndimage.binary_fill_holes(lab == (np.argmax(s) + 1))


M, N = load('master.png'), load('noarm.png')
F = load(mode + '_free.png')
fM, fN, fF = fmask(M), fmask(N), fmask(F)
H, W = fM.shape
yy, xx = np.mgrid[0:H, 0:W]


def capsule(a, b, r):
    a, b = np.array(a, float), np.array(b, float)
    ab = b - a
    t = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / (ab @ ab), 0, 1)
    return (xx - a[0] - t * ab[0]) ** 2 + (yy - a[1] - t * ab[1]) ** 2 <= r * r


cap = (capsule((A['shoulder'][0], A['shoulder'][1] - 90), A['elbow'], A['r_upper'])
       | capsule(A['elbow'], A['wrist'], A['r_fore']) | capsule(A['wrist'], A['finger'], A['r_hand']))
target = fM & cap & ((np.abs(M - N).mean(2) > 14) | ~fN) & (yy <= A['max_y'])
target = ndimage.binary_fill_holes(ndimage.binary_closing(target, iterations=5))
region = np.ones_like(target)
if mode == 'leg':
    # the leg is only visible below the jacket: compare outlines there
    hem = J['leg']['hem_y'] + 25
    target = fmask(load('oneleg.png')) & (yy >= hem)
    region = yy >= hem

# work at quarter resolution
k = 4
T = target[::k, ::k].astype(float)
Rg = region[::k, ::k].astype(float)
S = fF[::k, ::k].astype(float)
ty, tx = np.array(np.nonzero(T)).mean(1)
sy, sx = np.array(np.nonzero(S)).mean(1)
th = np.ptp(np.nonzero(T)[0]); sh = np.ptp(np.nonzero(S)[0])
s0 = th / sh
if mode == 'leg':
    # the free leg also has its hidden top: scale by width instead, and match bottoms
    tw = T.sum(1).max(); sw = S.sum(1).max(); s0 = tw / sw
    ty = np.nonzero(T)[0].max() - (np.nonzero(S)[0].max() - sy) * s0


def warp(img, s, ang, dx, dy, order=1, cval=0.0):
    # output (target frame) -> input (free frame): p_in = R(-ang)/s (p_out - c_t - d) + c_s
    c, si = np.cos(ang), np.sin(ang)
    Minv = np.array([[c, si], [-si, c]]) / s
    off = np.array([sy, sx]) - Minv @ (np.array([ty, tx]) + np.array([dy, dx]))
    return ndimage.affine_transform(img, Minv, offset=off, output_shape=T.shape, order=order, cval=cval)


def cost(p):
    s, ang, dx, dy = p
    w = warp(S, s, ang, dx, dy) * Rg
    inter = (w * T).sum(); uni = w.sum() + T.sum() - inter
    return 1 - inter / uni


best = None
for s in s0 * np.array([0.92, 0.96, 1.0, 1.04, 1.08]):
    for ang in np.radians([-6, -3, 0, 3, 6]):
        x0 = np.array([s, ang, 0.0, 0.0])
        simplex = np.array([x0, x0 + [0.02 * s, 0, 0, 0], x0 + [0, 0.03, 0, 0], x0 + [0, 0, 4, 0], x0 + [0, 0, 0, 4]])
        r = optimize.minimize(cost, x0, method='Nelder-Mead',
                              options=dict(xatol=1e-3, fatol=1e-5, maxiter=600, initial_simplex=simplex))
        if best is None or r.fun < best.fun:
            best = r
s, ang, dx, dy = best.x
print(f'IoU {1 - best.fun:.3f}  scale {s:.4f}  rotation {np.degrees(ang):.2f} deg  offset {dx * k:.1f},{dy * k:.1f} px')

# apply at full resolution
c, si = np.cos(ang), np.sin(ang)
Minv = np.array([[c, si], [-si, c]]) / s
off = np.array([sy, sx]) * k - Minv @ (np.array([ty, tx]) * k + np.array([dy, dx]) * k)


def warp_rgb(name, out):
    a = load(name)
    chans = [ndimage.affine_transform(a[..., i].astype(float), Minv, offset=off, output_shape=(H, W), order=1, cval=GREEN[i]) for i in range(3)]
    Image.fromarray(np.dstack(chans).clip(0, 255).astype(np.uint8)).save(os.path.join(src, out))


warp_rgb(mode + '_free.png', mode + '.png')
if mode == 'arm' and os.path.exists(os.path.join(src, 'fararm_free.png')):
    warp_rgb('fararm_free.png', 'fararm.png')
json.dump(dict(iou=round(1 - best.fun, 4), scale=s, rotation_deg=float(np.degrees(ang)), offset=[dx * k, dy * k]),
          open(os.path.join(src, mode + '_registration.json'), 'w'), indent=1)
