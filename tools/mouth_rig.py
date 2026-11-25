"""Mouth shapes made from the character's own mouth, the way cut-out animation does it (replaces pasting
separately painted mouths, which never matched the face's tone or outline).

python3 tools/mouth_rig.py [id ...]     (ids as in art/faces: pete, kate, inez, lee, sol, junkie, matt-front, matt-side)
For each Rhubarb shape the lower lip and jaw are pulled down by an amount (with a smooth falloff towards the chin
and the corners), the corners are drawn in for rounded vowels, and the opening shows a dark mouth interior, with a
pale upper-teeth band for the shapes that show teeth. Everything comes from the base frame's own pixels, so tone,
line work and the face outline stay exactly as painted. The result replaces row 1 (mouths) of the engine face
sheet; row 2 (blinks) is kept.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

# shape: (jaw open as a fraction of the mouth height, mouth width factor, teeth band 0..1, upper lip lift)
SHAPES = {
    'A': (0.00, 1.00, 0.0, 0.00),   # M B P: closed
    'B': (0.20, 1.00, 0.9, 0.05),   # most consonants: slightly open, teeth
    'C': (0.42, 1.00, 0.6, 0.10),   # EH, AE: open
    'D': (0.75, 1.02, 0.4, 0.15),   # AA: wide open
    'E': (0.50, 0.78, 0.2, 0.10),   # AO, ER: rounded
    'F': (0.22, 0.62, 0.0, 0.06),   # UW, OW, W: puckered
    'G': (0.12, 1.00, 1.0, 0.00),   # F, V: lower lip under the teeth
    'H': (0.36, 1.00, 0.3, 0.08),   # L: tongue up
}
SS = 4      # supersampling
TEETH_MIN = {'inez': 0.85}     # near-black lipstick: an opening only reads by the teeth


def targets():
    out = {}
    for room, name, fid in [('pete-kate-flat', 'pete-seated', 'pete'), ('pete-kate-flat', 'kate-at-table', 'kate'), ('office-day', 'inez-seated', 'inez'),
                            ('tea-house', 'lee-wing', 'lee'), ('pawnshop', 'sol', 'sol'), ('alley', 'junkie', 'junkie')]:
        sc = json.load(open(f'art/scenes/{room}/scene.json')); o = [o for o in sc['objects'] if o['name'] == name][0]
        w, h = o['bbox'][2] - o['bbox'][0], o['bbox'][3] - o['bbox'][1]
        out[fid] = dict(frame=Image.open(f'art/scenes/{room}/occ/{name}.png').convert('RGBA').crop((0, 0, w, h)), face=o['face'])
    sp = json.load(open('demo/office-walk/sprites/matt.json'))
    for d in ('front', 'side'):
        v = sp[d]; out['matt-' + d] = dict(frame=Image.open(f'demo/office-walk/sprites/{d}.webp').convert('RGBA').crop((0, 0, v['fw'], v['fh'])), face=v['face'])
    return out


def geometry(lum, alpha, rect):
    """Find the lip seam (a thin dark line: the black top-hat picks thin lines out of broad shading) and the mouth's
    corners, in the upper part of the mouth rect, where the lips sit."""
    x, y, w, h = rect
    reg = ndimage.gaussian_filter(lum[y:y + h, x:x + w], 0.8)
    a = alpha[y:y + h, x:x + w] > 200
    th = ndimage.grey_closing(reg, size=(7, 1)) - reg                  # thin dark horizontal lines
    th *= ndimage.gaussian_filter(a.astype(float), 1) > 0.95
    y0, y1 = int(h * 0.12), int(h * 0.62)
    band = th[y0:y1]
    cols = [c for c in range(int(w * 0.08), int(w * 0.92)) if a[y0:y1, c].mean() > 0.9]
    seam = {c: y0 + int(np.argmax(band[:, c])) for c in cols}
    strength = {c: band[seam[c] - y0, c] for c in cols}
    top = max(strength.values()) if strength else 0
    strong = [c for c in cols if strength[c] > top * 0.35]
    if len(strong) < 4:
        strong = cols
    # the mouth is the longest run of strong columns
    runs, cur = [], [strong[0]]
    for c in strong[1:]:
        if c - cur[-1] <= 2: cur.append(c)
        else: runs.append(cur); cur = [c]
    runs.append(cur); run = max(runs, key=len)
    xs = np.array(run); ys = np.array([seam[c] for c in run])
    k, b0 = np.polyfit(xs, ys, 1) if len(xs) > 3 else (0.0, float(np.median(ys)))
    k = float(np.clip(k, -0.35, 0.35)); b0 = float(np.median(ys - k * xs))
    # follow the lip line out from the middle of that run, a column at a time, while it stays a line
    curve = {}
    mid = run[len(run) // 2]
    for direction in (1, -1):
        c, yprev = mid, k * mid + b0
        while 0 <= c < w and a[:, c].mean() > 0.3:
            lo, hi = int(max(0, yprev - 2)), int(min(h - 1, yprev + 3))
            j = lo + int(np.argmax(th[lo:hi, c])); v = th[j, c]
            if v < top * 0.22: break
            curve[c] = j; yprev = j; c += direction
    cs = sorted(curve)
    c0, c1 = cs[0], cs[-1]
    yv = ndimage.uniform_filter1d(np.array([curve[c] for c in cs], float), 5)
    return dict(c0=c0, c1=c1, k=k, b=b0, cx=(c0 + c1) / 2, width=max(6, c1 - c0), xs=np.array(cs, float), ys=yv)


def make_shape(base, rect, g, open_f, width_f, teeth, lift, teeth_min=0.0):
    """Warp the mouth region of `base` (RGBA float array of the rect, supersampled) into one shape."""
    H, W = base.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = g['cx'] * SS; half = g['width'] * SS / 2
    seam = np.interp(xx / SS, g['xs'], g['ys']) * SS          # the traced lip line (flat beyond the corners)
    mouth_h = max(7.0, g['width'] * 0.42) * SS
    open_px = open_f * mouth_h
    # across the mouth: full in the middle, nothing past the corners
    u = (xx - cx) / (half * 1.15 * width_f)             # rounded vowels: a narrower, rounder opening
    bell = np.clip(1 - u ** 2, 0, 1) ** 1.3
    # below the seam: full at the lip, easing out towards the chin
    v = (yy - seam) / (mouth_h * 2.2)
    down = np.where(yy >= seam, np.clip(1 - v, 0, 1) ** 0.6, 0)
    up = np.where(yy < seam, np.clip(1 - (seam - yy) / (mouth_h * 0.9), 0, 1), 0)
    dy = open_px * bell * down - lift * mouth_h * bell * up
    sx = xx
    sy = yy - dy
    out = np.stack([ndimage.map_coordinates(base[..., c], [sy, sx], order=1, mode='nearest') for c in range(4)], -1)
    # the opening: between the lifted upper lip and the dropped lower lip
    gap_top = seam - lift * mouth_h * bell
    gap_bot = seam + open_px * bell
    gap = (yy > gap_top) & (yy < gap_bot) & (bell > 0.15) & (out[..., 3] > 128)
    if gap.any():
        lip = out[..., :3][np.abs(yy - seam) < 2 * SS].reshape(-1, 3)
        dark = (np.percentile(lip.mean(1), 5) if len(lip) else 40) * 0.35
        t = np.clip((yy - gap_top) / np.maximum(1, gap_bot - gap_top), 0, 1)
        interior = dark + 10 * np.sin(np.pi * t)                                    # a little depth in the middle
        band = max(teeth, teeth_min if open_f > 0.15 else 0) * np.clip(1 - t / 0.35, 0, 1) * (np.abs(u) < 0.75)   # upper teeth just under the lip
        teeth_tone = np.percentile(base[..., :3].mean(2)[base[..., 3] > 200], 85) * 0.92
        val = interior * (1 - band) + teeth_tone * band
        soft = np.clip(np.minimum(yy - gap_top, gap_bot - yy) / (0.8 * SS), 0, 1) * np.clip(bell * 3, 0, 1)
        for c in range(3):
            out[..., c] = np.where(gap, out[..., c] * (1 - soft) + val * soft, out[..., c])
    return out


def run(fid, T):
    face = T['face']; frame = np.asarray(T['frame']).astype(np.float32)
    x, y, w, h = face['mouth']
    lum = frame[..., :3].mean(2); alpha = frame[..., 3]
    g = geometry(lum, alpha, face['mouth'])
    region = frame[y:y + h, x:x + w]
    # warp a margin around the mouth rect too, so pulled-in pixels come from the real face, then cut the rect out
    m = 10; H0, W0 = frame.shape[:2]
    pad = np.zeros((h + 2 * m, w + 2 * m, 4), np.float32)
    ys0, xs0 = max(0, y - m), max(0, x - m); ys1, xs1 = min(H0, y + h + m), min(W0, x + w + m)
    pad[ys0 - (y - m):ys1 - (y - m), xs0 - (x - m):xs1 - (x - m)] = frame[ys0:ys1, xs0:xs1]
    big = np.stack([np.asarray(Image.fromarray(pad[..., c].clip(0, 255).astype(np.uint8)).resize(((w + 2 * m) * SS, (h + 2 * m) * SS), Image.BICUBIC)).astype(np.float32) for c in range(4)], -1)
    gm = dict(g, xs=g['xs'] + m, ys=g['ys'] + m, cx=g['cx'] + m)
    cells = []
    for s in face['shapes']:
        o = make_shape(big, face['mouth'], gm, *SHAPES[s], teeth_min=TEETH_MIN.get(fid, 0.0))[m * SS:(m + h) * SS, m * SS:(m + w) * SS]
        im = Image.fromarray(o.clip(0, 255).astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
        # keep the patch only where it differs from the face, feathered, so its edge can't show
        a = np.asarray(im).astype(np.float32); diff = np.abs(a[..., :3] - region[..., :3]).mean(2)
        fm = ndimage.gaussian_filter((ndimage.binary_dilation(diff > 3, iterations=2)).astype(np.float32), 1.2)
        a[..., 3] = np.minimum(region[..., 3], fm * 255)
        cells.append(Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'))
    # engine sheet: row 1 mouths (replaced), row 2 blinks (kept)
    D = f'art/faces/{fid}'; old = Image.open(f'{D}/face.png').convert('RGBA'); rows = face['rows']
    sheet = old.copy(); sheet.paste(Image.new('RGBA', (len(cells) * w, h), (0, 0, 0, 0)), (0, rows[0]))
    for i, c in enumerate(cells):
        sheet.paste(c, (i * w, rows[0]))
    sheet.save(f'{D}/face.png')
    # review: rest + every shape, enlarged
    tiles = []
    pad = int(max(w, h) * 0.9); cxp, cyp = x + w // 2, y + h // 2; box = (cxp - pad, cyp - pad, cxp + pad, cyp + pad)
    for s in ['rest'] + face['shapes']:
        im = T['frame'].copy()
        if s != 'rest':
            im.alpha_composite(cells[face['shapes'].index(s)], (x, y))
        tiles.append(im.crop(box).resize((200, 200), Image.LANCZOS))
    rv = Image.new('RGBA', (200 * len(tiles), 200), (40, 40, 40, 255))
    for i, t in enumerate(tiles):
        rv.alpha_composite(t, (i * 200, 0))
    rv.convert('RGB').save(f'{D}/check-rig.png')
    print(fid, 'seam', round(g['k'], 2), round(g['b'], 1), 'mouth x', g['c0'], '-', g['c1'])


if __name__ == '__main__':
    T = targets()
    for fid in (sys.argv[1:] or list(T)):
        run(fid, T[fid])
