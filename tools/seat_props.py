"""Seated characters as props cut from AI edits of a room, so the furniture is the room's own.

python3 tools/seat_props.py <room.png> <plate.png> <out dir> name:edit.png:x0,y0,x1,y1 [...]

- The plate is an edit of the room with the props' furniture painted out. It is pasted back into the
  original only where it differs inside the given boxes (the furniture and its shadows), so the rest of
  the painting stays untouched -> <out dir>/<room>-plate.png
- Each prop is the part of its edit (character + chair + shadow) that differs from the plate inside its
  box, as a full-size RGBA image with a soft edge -> <out dir>/<name>.png
Boxes are fractions of the image.
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

room, plate_p, out = sys.argv[1:4]
props = [a.split(':') for a in sys.argv[4:]]
R = np.asarray(Image.open(room).convert('L')).astype(float)
P = np.asarray(Image.open(plate_p).convert('L').resize(R.shape[::-1], Image.LANCZOS)).astype(float)
H, W = R.shape
os.makedirs(out, exist_ok=True)


def region(a, b, box, thr=22):
    x0, y0, x1, y1 = [float(v) for v in box.split(',')]
    X0, Y0, X1, Y1 = int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)
    d = np.abs(ndimage.gaussian_filter(a, 2) - ndimage.gaussian_filter(b, 2))
    m = np.zeros((H, W), bool); m[Y0:Y1, X0:X1] = d[Y0:Y1, X0:X1] > thr
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=6)
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.08])
    return ndimage.binary_fill_holes(m)


# 1) plate: original + plate pixels where the furniture was
mask = np.zeros((H, W), bool)
for name, edit, box in props:
    mask |= region(R, P, box)
for extra in os.environ.get('PLATE_EXTRA', '').split(';'):
    if extra:
        mask |= region(R, P, extra)
alpha = ndimage.gaussian_filter(ndimage.binary_dilation(mask, iterations=6).astype(float), 3)
plate = R * (1 - alpha) + P * alpha
base = os.path.splitext(os.path.basename(room))[0]
Image.fromarray(plate.clip(0, 255).astype(np.uint8)).convert('RGB').save(os.path.join(out, base + '-plate.png'))
# 2) props: edit pixels that differ from the plate
for name, edit, box in props:
    E = np.asarray(Image.open(edit).convert('L').resize((W, H), Image.LANCZOS)).astype(float)
    m = region(E, plate, box)
    a = ndimage.gaussian_filter(ndimage.binary_dilation(m, iterations=2).astype(float), 1.2)
    rgba = np.dstack([E, E, E, a * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(out, name + '.png'))
    ys, xs = np.nonzero(m); print(name, 'bbox', xs.min() / W, ys.min() / H, xs.max() / W, ys.max() / H)
