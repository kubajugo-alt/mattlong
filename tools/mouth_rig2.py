"""Mouth shapes with a moving jaw (v2 of tools/mouth_rig.py, from the review board's notes).

python3 tools/mouth_rig2.py [id ...]      ids: pete kate inez lee sol junkie matt-front matt-side
Like mouth_rig, every shape is made from the character's own pixels, but the patch now takes in the chin:
  - the jaw drops: the lower lip AND the chin move down together as one block (full under the mouth, easing off
    toward the jaw's corners); only below the chin, where the neck starts, is the face stretched to meet the
    unmoved neck;
  - the upper lip lifts for the open vowels;
  - the opening shows the upper teeth under the lip (and a hint of the lower ones for the widest shapes), the
    mouth's dark inside between;
  - H (L, tongue up) is a small opening with the teeth showing and the tongue kept behind them;
  - the patch is kept only where it differs from the face, with a wide, soft edge.
Writes art/faces/<id>/face.png (row 1: mouths in the new, larger rect; row 2: the blinks, unchanged), face.json
(the new mouth rect and rows) and check-rig2.png (rest + every shape, enlarged); install with
tools/install_faces.py.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
import mouth_rig

# shape: (jaw open as a fraction of the mouth height, width factor, upper teeth, lower teeth, upper lip lift)
SHAPES = {
    'A': (0.00, 1.00, 0.0, 0.0, 0.00),   # M B P: closed
    'B': (0.18, 1.00, 0.9, 0.3, 0.10),   # most consonants: a little open, teeth together
    'C': (0.36, 1.00, 0.8, 0.2, 0.16),   # EH, AE: open
    'D': (0.66, 1.00, 0.7, 0.25, 0.20),  # AA: wide open, the jaw well down
    'E': (0.44, 0.80, 0.5, 0.0, 0.14),   # AO, ER: rounded
    'F': (0.24, 0.62, 0.0, 0.0, 0.08),   # UW, OW, W: puckered
    'G': (0.10, 1.00, 1.0, 0.0, 0.04),   # F, V: lower lip under the upper teeth
    'H': (0.30, 1.00, 0.9, 0.0, 0.12),   # L: small opening, teeth, tongue behind them
}
SS = 4
TEETH_MIN = {'inez': 0.85}               # near-black lipstick: an opening only reads by the teeth


def run(fid, T):
    face = T['face']; frame = np.asarray(T['frame']).astype(np.float32); H0, W0 = frame.shape[:2]
    x, y, w, h = face['mouth']
    g = mouth_rig.geometry(frame[..., :3].mean(2), frame[..., 3], face['mouth'])
    mouth_h = max(7.0, g['width'] * 0.42)                 # the opening's scale, as in v1
    # the patch: the mouth rect, wider for the jaw's corners and down past the chin
    px0 = max(0, int(x - w * 0.35)); px1 = min(W0, int(x + w * 1.35))
    py0 = max(0, int(y - h * 0.10)); py1 = min(H0, int(y + h + mouth_h * 2.6))
    pw, ph = px1 - px0, py1 - py0
    m = 8; X0, Y0 = px0 - m, py0 - m
    pad = np.zeros((ph + 2 * m, pw + 2 * m, 4), np.float32)
    ys0, xs0 = max(0, Y0), max(0, X0); ys1, xs1 = min(H0, py1 + m), min(W0, px1 + m)
    pad[ys0 - Y0:ys1 - Y0, xs0 - X0:xs1 - X0] = frame[ys0:ys1, xs0:xs1]
    big = np.stack([np.asarray(Image.fromarray(pad[..., c].clip(0, 255).astype(np.uint8)).resize(((pw + 2 * m) * SS, (ph + 2 * m) * SS), Image.BICUBIC)).astype(np.float32) for c in range(4)], -1)
    Hb, Wb = big.shape[:2]; yy, xx = np.mgrid[0:Hb, 0:Wb].astype(np.float32)
    ox, oy = (x - X0) * SS, (y - Y0) * SS                  # the mouth rect's origin in the padded, supersampled patch
    cx = ox + g['cx'] * SS; half = g['width'] * SS / 2; mh = mouth_h * SS
    seam = oy + np.interp((xx - ox) / SS, g['xs'], g['ys']) * SS
    chin = seam + mh * 1.55                               # where the chin ends and the neck begins (a fixed proportion)
    bottom = (py1 - Y0) * SS                              # the patch's lower edge: the neck, unmoved
    base_l = big[..., :3].mean(2)
    lip = big[..., :3][np.abs(yy - seam) < 2 * SS].reshape(-1, 3)
    dark_tone = (np.percentile(lip.mean(1), 5) if len(lip) else 40) * 0.45
    skin = big[..., :3][(big[..., 3] > 200) & (yy > seam + mh) & (yy < chin) & (np.abs(xx - cx) < half)]
    teeth_tone = np.percentile(base_l[big[..., 3] > 200], 92) * 0.95
    region = frame[py0:py1, px0:px1]
    cells = []
    for s in face['shapes']:
        open_f, width_f, t_up, t_lo, lift = SHAPES[s]
        open_px = open_f * mh
        u = (xx - cx) / (half * 1.0 * width_f); bell = np.clip(1 - u ** 2, 0, 1) ** 1.3           # the mouth across, corner to corner
        uj = (xx - cx) / (half * 2.1); jaw = np.clip(1 - uj ** 2, 0, 1) ** 0.8                      # the jaw across: wider
        # down: lips and chin move as one (jaw), fading only between the chin and the patch's bottom edge
        fall = np.where(yy < seam, 0, np.where(yy < chin, 1, np.clip((bottom - yy) / np.maximum(1, bottom - chin), 0, 1)))
        near = np.clip((yy - seam) / (mh * 0.9), 0, 1)                                   # 0 at the lip, 1 a lip's height below
        lower = bell ** 0.7 * (1 - near) + np.maximum(jaw, bell ** 0.7) * near
        up = np.where(yy < seam, np.clip(1 - (seam - yy) / (mh * 0.9), 0, 1), 0)
        dy = open_px * lower * fall - lift * mh * bell * up
        # rounded vowels pull the corners in
        dx = np.where((yy > seam - mh) & (yy < seam + mh), (1 - width_f) * (xx - cx) * 0.55 * np.clip(1 - np.abs(yy - seam) / mh, 0, 1) * np.clip(1 - np.abs(u) / 1.6, 0, 1), 0)
        pm = big.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0                         # premultiplied, so transparency carries no colour
        out = np.stack([ndimage.map_coordinates(pm[..., c], [yy - dy, xx + dx], order=1, mode='nearest') for c in range(4)], -1)
        out[..., :3] /= np.maximum(out[..., 3:4], 8.0) / 255.0
        gap_top = seam - lift * mh * bell; gap_bot = seam + open_px * bell ** 0.7
        gap = (yy > gap_top) & (yy < gap_bot) & (bell > 0.12) & (out[..., 3] > 128)
        if gap.any():
            t = np.clip((yy - gap_top) / np.maximum(1, gap_bot - gap_top), 0, 1)
            inside = dark_tone + 16 * np.sin(np.pi * t) * np.clip(1 - np.abs(u), 0, 1)        # deepest in the middle
            tu = max(t_up, TEETH_MIN.get(fid, 0) if open_f > 0.15 else 0)
            up_band = min(1.0, tu * 1.3) * np.clip(np.minimum(t / 0.04, (0.46 - t) / 0.1), 0, 1) * np.clip(1 - np.abs(u) / 0.8, 0, 1) ** 0.5   # under the lip, not at its edge
            lo_band = t_lo * np.clip((t - 0.82) / 0.18, 0, 1) * np.clip(1 - np.abs(u) / 0.6, 0, 1) ** 0.5
            val = inside * (1 - up_band - lo_band) + teeth_tone * up_band + teeth_tone * 0.85 * lo_band
            if s == 'H':                                   # the tongue, behind the teeth: a little lighter than the inside
                tongue = np.clip(1 - ((t - 0.55) / 0.3) ** 2, 0, 1) * np.clip(1 - np.abs(u) / 0.5, 0, 1)
                val = val * (1 - 0.5 * tongue) + (dark_tone * 2.6) * 0.5 * tongue
            soft = np.clip(np.minimum(yy - gap_top, gap_bot - yy) / (0.5 * SS), 0, 1) * np.clip(bell * 3, 0, 1)
            for c in range(3):
                out[..., c] = np.where(gap, out[..., c] * (1 - soft) + val * soft, out[..., c])
        o = out[m * SS:(m + ph) * SS, m * SS:(m + pw) * SS]
        im = Image.fromarray(o.clip(0, 255).astype(np.uint8), 'RGBA').resize((pw, ph), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        # over the original: where the moved jaw's edge is part-transparent, what was there (collar, neck) shows through
        wa = a[..., 3:4] / 255.0; a[..., :3] = a[..., :3] * wa + region[..., :3] * (1 - wa); a[..., 3] = np.maximum(a[..., 3], region[..., 3])
        diff = np.abs(a[..., :3] - region[..., :3]).mean(2)
        fm = ndimage.gaussian_filter(ndimage.binary_dilation(diff > 2.5, iterations=3).astype(np.float32), 1.6)
        a[..., 3] = np.minimum(region[..., 3], np.clip(fm * 1.25, 0, 1) * 255)
        cells.append(Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'))
    D = f'art/faces/{fid}'; old = Image.open(f'{D}/face.v1.png').convert('RGBA'); rows = face['rows']   # blinks from the v1 sheet
    ex, ey, ew, eh = face['eyes']
    blinks = old.crop((0, rows[1], len(face['blink']) * ew, rows[1] + eh)) if len(rows) > 1 else None
    sheet = Image.new('RGBA', (max(len(cells) * pw, len(face['blink']) * ew), ph + eh))
    for i, c in enumerate(cells):
        sheet.paste(c, (i * pw, 0))
    if blinks: sheet.paste(blinks, (0, ph))
    sheet.save(f'{D}/face.png')
    nf = dict(face, mouth=[px0, py0, pw, ph], rows=[0, ph]); json.dump(nf, open(f'{D}/face.json', 'w'), indent=1)
    # review: rest and every shape, enlarged around the mouth and chin
    tiles = []
    for s in ['rest'] + face['shapes']:
        im = T['frame'].copy()
        if s != 'rest': im.alpha_composite(cells[face['shapes'].index(s)], (px0, py0))
        bx = (px0 - pw * 0.25, py0 - ph * 0.6, px1 + pw * 0.25, py1 + ph * 0.1)
        bg = Image.new('RGBA', im.size, (40, 40, 40, 255)); bg.alpha_composite(im)
        tiles.append(bg.crop(tuple(int(v) for v in bx)).resize((240, int(240 * (bx[3] - bx[1]) / (bx[2] - bx[0]))), Image.LANCZOS))
    rv = Image.new('RGB', (240 * len(tiles), tiles[0].height), (40, 40, 40))
    for i, t in enumerate(tiles):
        rv.paste(t.convert('RGB'), (i * 240, 0))
    rv.save(f'{D}/check-rig2.png')
    print(fid, 'mouth', face['mouth'], '-> patch', nf['mouth'])


if __name__ == '__main__':
    T = mouth_rig.targets()
    for fid in (sys.argv[1:] or list(T)):
        # always start from the v1 face.json (mouth rect of the lips themselves) so a rerun doesn't grow the patch
        fj = f'art/faces/{fid}/face.json'; v1 = fj.replace('face.json', 'face.v1.json')
        if not os.path.exists(v1): os.system(f'cp {fj} {v1}'); os.system(f"cp art/faces/{fid}/face.png art/faces/{fid}/face.v1.png")
        T[fid]['face'] = json.load(open(v1))
        run(fid, T[fid])
