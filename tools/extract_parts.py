"""Split a generated parts sheet into transparent PNG pieces.

python3 tools/extract_parts.py sheet.png outdir [min_area]
Writes outdir/part_<n>.png (cropped, alpha) and outdir/parts.json with each
piece's box in sheet coordinates, its long-axis end points (local coords)
and its top/bottom attachment points.
"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
min_area = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
rgb = np.asarray(Image.open(src).convert('RGB')).astype(int)
g = rgb.mean(2)
bg = np.median(np.concatenate([g[:, :20], g[:, -20:]], 1), 1)[:, None]
fg = np.abs(g - bg) > 9
fg = ndimage.binary_opening(fg, iterations=2)
lab0, n0 = ndimage.label(fg)
sizes = ndimage.sum(fg, lab0, range(1, n0 + 1))
pieces = []
import os; os.makedirs(out, exist_ok=True)
k = 0
for i, s in enumerate(sizes):
    if s < min_area:
        continue
    m = lab0 == i + 1
    # close gaps where cloth matches the background, then fill holes.
    # Work on a padded crop so the large closing stays fast.
    ys, xs = np.nonzero(m); P = 40
    cy0, cx0 = max(ys.min() - P, 0), max(xs.min() - P, 0)
    sub = m[cy0:ys.max() + P, cx0:xs.max() + P]
    sub = ndimage.binary_closing(sub, structure=np.ones((3, 3)), iterations=22)
    sub = ndimage.binary_fill_holes(sub)
    sub = ndimage.binary_erosion(sub, iterations=2)
    m = np.zeros_like(m); m[cy0:cy0 + sub.shape[0], cx0:cx0 + sub.shape[1]] = sub
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alpha = ndimage.gaussian_filter(m.astype(float), 1.0)[y0:y1, x0:x1]
    rgba = np.dstack([rgb[y0:y1, x0:x1], (alpha * 255).astype(int)]).astype(np.uint8)
    name = f'part_{k}.png'
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, name), optimize=True)
    pts = np.stack([xs - x0, ys - y0], 1).astype(float)
    c = pts.mean(0); _, _, vt = np.linalg.svd(pts - c, full_matrices=False); d = vt[0]
    t = (pts - c) @ d
    a, b = c + d * np.percentile(t, 3), c + d * np.percentile(t, 97)
    if a[1] > b[1]: a, b = b, a
    top = pts[pts[:, 1] <= pts[:, 1].min() + 12].mean(0)
    bot = pts[pts[:, 1] >= pts[:, 1].max() - 12].mean(0)
    pieces.append(dict(file=name, box=[int(x0), int(y0), int(x1), int(y1)],
                       axisTop=a.round(1).tolist(), axisBottom=b.round(1).tolist(),
                       top=top.round(1).tolist(), bottom=bot.round(1).tolist()))
    k += 1
json.dump(dict(source=os.path.basename(src), pieces=pieces), open(os.path.join(out, 'parts.json'), 'w'), indent=1)
print(json.dumps(pieces, indent=1))
