"""Soften Matt's frown by warping his own pixels: lift and part the inner brows, ease the crease between them,
and lift the mouth corners a touch. soften(img RGBA float array, kind 'front'|'side', strength, dx0, dy0)"""
import numpy as np
from scipy import ndimage

# (cx, cy, radius, lift px, outward px) at strength 1, in standing-frame sprite pixels; eye_y: below it nothing moves up
FEAT = {
 'front': {'brows': [(184, 89, 12, 2.2, -1.0), (196, 88, 12, 2.2, 1.0), (166, 86, 14, 1.4, 0), (216, 84, 16, 1.4, 0)], 'eye_y': 96,
           'crease': (182, 84, 196, 99), 'mouth': [], 'lip_y': 141, 'corners': [(174, 143, 5, 6, 3.2, -0.4), (212, 142, 5, 6, 3.2, 0.4)],
           'bags': [(160, 107, 184, 117), (198, 106, 226, 116)]},
 'side':  {'brows': [(326, 84, 11, 2.2, 0.6), (311, 83, 12, 1.3, 0)], 'eye_y': 91,
           'crease': None, 'mouth': [], 'lip_y': 136, 'corners': [(320, 138, 5.5, 7, 4.5, -0.3)], 'bags': [(312, 99, 334, 107)]},
}

def soften(a, kind, k, ox=0, oy=0, parts=('brow', 'mouth')):
    F = FEAT[kind]; H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.zeros((H, W), np.float32); dy = np.zeros((H, W), np.float32)
    def bump(cx, cy, r, lift, out, below):
        g = np.exp(-(((xx - cx - ox) ** 2 + (yy - cy - oy) ** 2) / (2 * r * r)))
        g *= np.clip((below + oy - yy) / 4.0, 0, 1)            # nothing below the line moves (the eye, the lower lip)
        dy[...] -= lift * k * g; dx[...] += out * k * g
    for b in (F['brows'] if 'brow' in parts else []): bump(*b, F['eye_y'] - 3)
    for m in (F['mouth'] if 'mouth' in parts else []): bump(*m, F['lip_y'] + 3)
    for (cx, cy, rx, ry, lift, out) in (F.get('corners', []) if 'mouth' in parts else []):     # a mouth corner: lip, crease and the skin under it rise together
        g = np.exp(-(((xx - cx - ox) / rx) ** 2 + ((yy - cy - oy) / ry) ** 2) / 2)
        dy[...] -= lift * k * g; dx[...] += out * k * g
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
    out = np.stack([ndimage.map_coordinates(pm[..., c], [yy - dy, xx - dx], order=3, mode='nearest') for c in range(4)], -1)
    out[..., 3] = np.clip(out[..., 3], 0, 255); out[..., :3] = np.clip(out[..., :3] / np.maximum(out[..., 3:4], 8.0) * 255.0, 0, 255)
    moved = (np.hypot(dx, dy) > 0.02)[..., None] & (a[..., 3:4] > 250) & (out[..., 3:4] > 250)   # only solid skin moves: the
    out = np.where(moved, out, a)                                                                # silhouette's edge stays as drawn
    for (x0, y0, x1, y1) in (F.get('bags', []) if 'brow' in parts else []):                 # the dark bags under the eyes: eased the same way, lighter touch
        x0 += ox; x1 += ox; y0 += oy; y1 += oy
        reg = out[y0:y1, x0:x1, :3].mean(2); sm = ndimage.gaussian_filter(reg, 3.0); h, w = reg.shape; cyy, cxx = np.mgrid[0:h, 0:w]
        m = np.exp(-(((cxx - w / 2) / (w * 0.4)) ** 2 + ((cyy - h / 2) / (h * 0.5)) ** 2))
        lift = np.clip(sm - reg, 0, None) * min(1, 0.35 * k) + 6 * k * m * (reg < 140)
        for c in range(3): out[y0:y1, x0:x1, c] += lift * m
    if F['crease'] and 'brow' in parts:                                            # the vertical frown line: lift its darkest values toward its surroundings
        x0, y0, x1, y1 = F['crease']; x0 += ox; x1 += ox; y0 += oy; y1 += oy
        reg = out[y0:y1, x0:x1, :3].mean(2); sm = ndimage.gaussian_filter(reg, 2.2)
        lift = np.clip(sm - reg, 0, None) * min(1, 0.55 * k)   # only darker-than-surroundings pixels, so the brows' edges stay
        m = np.zeros_like(reg); h, w = m.shape; cyy, cxx = np.mgrid[0:h, 0:w]
        m = np.exp(-(((cxx - w / 2) / (w * 0.3)) ** 2 + ((cyy - h / 2) / (h * 0.45)) ** 2))
        for c in range(3): out[y0:y1, x0:x1, c] += lift * m
    return out
