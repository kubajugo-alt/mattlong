"""Turn a Ludo animateSprite sheet into the demo's sprite strip.

python3 tools/pack_sprite.py <sheet.webp> <cols> <rows> <out strip.webp> [figure_h=520]

Cuts the grid into frames, crops every frame to the union box of the figure across all
frames (so the figure never jumps), scales so the tallest frame is figure_h px, and lays
the frames out in one row. Prints a JSON entry for sprites/matt.json: frame size, the feet
point (x from the bottom rows, y = lowest opaque row) and the feet row of every frame,
which the engine uses to keep the planted foot (and the shadow) fixed to the floor.
"""
import json, sys
import numpy as np
from PIL import Image

src, cols, rows, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
figure_h = int(sys.argv[5]) if len(sys.argv) > 5 else 520
sheet = Image.open(src).convert('RGBA')
fw0, fh0 = sheet.width // cols, sheet.height // rows
frames = [sheet.crop((c * fw0, r * fh0, (c + 1) * fw0, (r + 1) * fh0)) for r in range(rows) for c in range(cols)]
A = [np.asarray(f)[:, :, 3] > 40 for f in frames]
union = np.any(A, axis=0)
ys, xs = np.nonzero(union)
x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
tallest = max(np.ptp(np.nonzero(a.any(1))[0]) + 1 for a in A)
s = figure_h / tallest
fw, fh = round((x1 - x0) * s), round((y1 - y0) * s)
strip = Image.new('RGBA', (fw * len(frames), fh))
feet = []
for i, f in enumerate(frames):
    g = f.crop((x0, y0, x1, y1)).resize((fw, fh), Image.LANCZOS)
    strip.paste(g, (i * fw, 0))
    a = np.asarray(g)[:, :, 3] > 40
    feet.append(int(np.nonzero(a.any(1))[0].max()))
strip.save(out, quality=88, method=6)
a0 = np.asarray(strip.crop((0, 0, fw, fh)))[:, :, 3] > 40
bottom = a0[feet[0] - 12:feet[0] + 1]
feet_x = float(np.nonzero(bottom.any(0))[0].mean())
print(json.dumps({'frames': len(frames), 'fw': fw, 'fh': fh, 'feet_x': round(feet_x, 1),
                  'feet_y': float(max(feet)), 'figure_h': figure_h, 'feet_per_frame': feet}))
