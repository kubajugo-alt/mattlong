"""Mouth shapes and blinks as small patches at engine resolution, from Gemini edits of each face close-up.

python3 tools/face_patches.py [id ...]
Reads art/faces/<id>/{base,A..H,half,closed}.png and map.json (from tools/face_crops.py). For each edit:
  1. register it to base (OpenCV ECC, affine) so a slight shift or scale in the edit does not move the face;
  2. the mouth region = where the mouth edits differ from base (union over A..H, near the lower middle of the
     face), the eye region = where the closed-eyes edit differs (upper half); one feathered mask per region,
     shared by all shapes so every shape covers the same pixels;
  3. scale the patch to the engine frame (target = source * k + off) and write a sheet + json.
Output: art/faces/<id>/face.png (row 1: mouth A..H, row 2: eyes half, closed), face.json (rects in target px),
and check.png (each shape composited on base, for review).
"""
import json, os, sys
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage

MOUTH = list('ABCDEFGH'); EYES = ['half', 'closed']


def load(p):
    return np.asarray(Image.open(p).convert('RGB').resize((1024, 1024), Image.LANCZOS)).astype(np.float32)


def register(img, base):
    g1 = cv2.cvtColor(base.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g2 = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    s = 0.5; a = cv2.resize(g1, None, fx=s, fy=s); b = cv2.resize(g2, None, fx=s, fy=s)
    M = np.eye(2, 3, dtype=np.float32)
    try:
        _, M = cv2.findTransformECC(a, b, M, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
    except cv2.error:
        pass
    M[:, 2] /= s
    return cv2.warpAffine(img, M, (1024, 1024), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


def region(diffs, lower):
    d = np.max(diffs, axis=0)
    d = ndimage.gaussian_filter(d, 3) > 18
    yy = np.arange(1024)[:, None] * np.ones((1, 1024))
    d &= (yy > 420) if lower else (yy < 620)
    d = ndimage.binary_opening(d, iterations=3)
    lab, n = ndimage.label(d)
    if not n:
        return None
    sizes = ndimage.sum(d, lab, range(1, n + 1))
    keep = [i + 1 for i in np.argsort(-sizes)[:(1 if lower else 2)] if sizes[i] > 150]
    m = np.isin(lab, keep)
    if lower:
        # mouth: a tight ellipse around where the mouth shapes change most (Gemini sometimes repaints the
        # cheeks too; those changes are ignored), from the lips down over the jaw drop
        dd = np.max(diffs, axis=0) * (yy > 420) * m
        thr = np.percentile(dd[dd > 0], 80) if (dd > 0).any() else 0
        ys, xs = np.nonzero(dd >= thr)
        cy, cx = np.average(ys, weights=dd[ys, xs]), np.average(xs, weights=dd[ys, xs])
        e = np.zeros((1024, 1024), np.uint8)
        cv2.ellipse(e, (int(cx), int(cy + 12)), (95, 80), 0, 0, 360, 1, -1)
        return ndimage.gaussian_filter(e.astype(np.float32), 10).clip(0, 1)
    m = ndimage.binary_dilation(m, iterations=10)
    return ndimage.gaussian_filter(m.astype(np.float32), 6).clip(0, 1)


def face_alpha(base):
    """The face close-ups sit on flat mid-grey: everything not connected to that border grey is the character."""
    g = (np.abs(base - 128).max(2) <= 2)
    lab, n = ndimage.label(g)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    return ~bg


def align_local(img, base, ring):
    """Second, local alignment on the area around the mouth (nose, cheeks, chin), translation + scale only."""
    g1 = cv2.cvtColor(base.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g2 = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    M = np.eye(2, 3, dtype=np.float32)
    try:
        _, M = cv2.findTransformECC(g1, g2, M, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 150, 1e-6), ring.astype(np.uint8), 5)
    except cv2.error:
        return img
    return cv2.warpAffine(img, M, (1024, 1024), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


def tone_match(img, base, band):
    """Bring the painted mouth's brightness and contrast to the skin around it."""
    out = img.copy()
    for c in range(3):
        a, b = img[..., c][band], base[..., c][band]
        if a.size > 50 and a.std() > 1:
            out[..., c] = (img[..., c] - a.mean()) * (b.std() / a.std()) + b.mean()
    return out.clip(0, 255)


def mouth_mask(diffs, inside):
    """An ellipse around where the open shapes differ most (the lips and jaw drop), kept off the face outline."""
    d = np.max(diffs, axis=0) * inside
    yy = np.arange(1024)[:, None] * np.ones((1, 1024))
    d = ndimage.gaussian_filter(d, 3) * (yy > 380)
    thr = np.percentile(d[d > 0], 92) if (d > 0).any() else 0
    ys, xs = np.nonzero(d >= thr)
    wts = d[ys, xs]
    cy, cx = np.average(ys, weights=wts), np.average(xs, weights=wts)
    sy = np.sqrt(np.average((ys - cy) ** 2, weights=wts)); sx = np.sqrt(np.average((xs - cx) ** 2, weights=wts))
    ax, ay = int(np.clip(sx * 2.3, 45, 120)), int(np.clip(sy * 1.8, 32, 80))       # lips and jaw drop, not the chin highlight
    e = np.zeros((1024, 1024), np.uint8); cv2.ellipse(e, (int(cx), int(cy)), (ax, ay), 0, 0, 360, 1, -1)
    e = e.astype(bool) & ndimage.binary_erosion(inside, iterations=10)       # never touch the outline
    return e, ndimage.gaussian_filter(e.astype(np.float32), 7).clip(0, 1)


def blend_mouth(img, base, hard, soft):
    """Gradient-domain clone of the painted mouth into the face, then a feathered edge."""
    ys, xs = np.nonzero(hard)
    if not len(ys):
        return base
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    center = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
    m8 = (hard * 255).astype(np.uint8)
    try:
        cl = cv2.seamlessClone(img.clip(0, 255).astype(np.uint8), base.clip(0, 255).astype(np.uint8), m8, center, cv2.NORMAL_CLONE).astype(np.float32)
    except cv2.error:
        cl = img
    out = base * (1 - soft[..., None]) + cl * soft[..., None]
    # below the lips the painted version must not be lit brighter than the original (it may be darker: jaw shadow)
    cy = (ys.min() + ys.max()) / 2; ay = (ys.max() - ys.min()) / 2
    w = np.clip(((np.arange(1024)[:, None] - (cy + 0.2 * ay)) / (0.3 * ay)), 0, 1)[..., None]
    return out * (1 - w) + np.minimum(out, base + 8) * w


def grey_keep_red(rgb, keep_red):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    out = np.dstack([lum, lum, lum])
    if keep_red:
        red = (r > 70) & (r > g * 1.5) & (r > b * 1.5)
        out[red] = rgb[red]
    return out


def run(fid):
    D = f'art/faces/{fid}'; mp = json.load(open(f'{D}/map.json'))
    base = load(f'{D}/base.png')
    have = {k: f'{D}/{k}.png' for k in MOUTH + EYES if os.path.exists(f'{D}/{k}.png')}
    reg = {k: register(load(p), base) for k, p in have.items()}
    diff = {k: np.abs(reg[k] - base).mean(2) for k in reg}
    mouth_keys = [k for k in MOUTH if k in reg]
    mm = None
    if mouth_keys:
        inside = face_alpha(base)
        hard, mm = mouth_mask([diff[k] for k in mouth_keys if k in 'CDE'] or [diff[k] for k in mouth_keys], inside)
        ring = ndimage.binary_dilation(hard, iterations=70) & ~ndimage.binary_dilation(hard, iterations=8) & inside
        band = ndimage.binary_dilation(hard, iterations=18) & ~hard & inside
        for k in mouth_keys:
            r = align_local(reg[k], base, ring)
            r = tone_match(r, base, band)
            reg[k] = blend_mouth(r, base, hard, mm)
        mm = ndimage.gaussian_filter((ndimage.binary_dilation(hard, iterations=6)).astype(np.float32), 4).clip(0, 1)
    em = region([diff[k] for k in EYES if k in reg], False) if any(k in reg for k in EYES) else None
    keep_red = False      # Inez's sprite lips are near-black; red only in some shapes would flash
    # source px per 1024-crop px, and crop -> target
    bx0, by0, bx1, by1 = mp['box_src']; f = (bx1 - bx0) / 1024 * mp['k']
    tx0 = bx0 * mp['k'] + mp['off'][0]; ty0 = by0 * mp['k'] + mp['off'][1]
    out = {'mouth': None, 'eyes': None, 'shapes': mouth_keys, 'blink': [k for k in EYES if k in reg]}
    cells = []
    for name, m, keys in [('mouth', mm, mouth_keys), ('eyes', em, [k for k in EYES if k in reg])]:
        if m is None or not keys:
            continue
        ys, xs = np.nonzero(m > 0.02); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        # target rect (integer, enclosing)
        X0 = int(np.floor(tx0 + x0 * f)); Y0 = int(np.floor(ty0 + y0 * f)); X1 = int(np.ceil(tx0 + x1 * f)); Y1 = int(np.ceil(ty0 + y1 * f))
        w, h = max(1, X1 - X0), max(1, Y1 - Y0)
        # the crop region that maps exactly onto that target rect
        cx0 = (X0 - tx0) / f; cy0 = (Y0 - ty0) / f; cx1 = (X1 - tx0) / f; cy1 = (Y1 - ty0) / f
        row = []
        for k in keys:
            rgb = grey_keep_red(reg[k], keep_red); a = m * 255
            rgba = np.dstack([rgb, a]).clip(0, 255).astype(np.uint8)
            im = Image.fromarray(rgba, 'RGBA').transform((w * 4, h * 4), Image.EXTENT, (cx0, cy0, cx1, cy1), Image.BICUBIC)
            im = im.resize((w, h), Image.LANCZOS)
            row.append(im)
        out[name] = [X0, Y0, w, h]; cells.append(row)
    if cells:
        W = max(len(r) * r[0].width for r in cells); H = sum(r[0].height for r in cells)
        sheet = Image.new('RGBA', (W, H)); y = 0; rows = []
        for r in cells:
            for i, im in enumerate(r):
                sheet.paste(im, (i * im.width, y))
            rows.append(y); y += r[0].height
        sheet.save(f'{D}/face.png')          # untoned; the installer darkens it for a night room
        out['rows'] = rows
    json.dump(out, open(f'{D}/face.json', 'w'), indent=1)
    # review sheet: every shape composited onto the base close-up (mask outline drawn faintly)
    tiles = []
    for k in ['base'] + list(reg):
        if k == 'base':
            t = base.copy()
        else:
            m = mm if k in MOUTH else em
            t = base * (1 - m[..., None]) + reg[k] * m[..., None]
        tiles.append(Image.fromarray(t.clip(0, 255).astype(np.uint8)).crop((150, 150, 874, 874)).resize((240, 240)))
    rv = Image.new('RGB', (240 * len(tiles), 240)); [rv.paste(t, (i * 240, 0)) for i, t in enumerate(tiles)]
    rv.save(f'{D}/check.png')
    print(fid, 'mouth', out['mouth'], 'eyes', out['eyes'], 'shapes', ''.join(mouth_keys))


if __name__ == '__main__':
    ids = sys.argv[1:] or sorted(d for d in os.listdir('art/faces') if os.path.exists(f'art/faces/{d}/map.json'))
    for i in ids:
        run(i)
