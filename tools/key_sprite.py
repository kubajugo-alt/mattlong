"""Key a chroma-green character image into a greyscale cut-out (same treatment as the cast).

python3 tools/key_sprite.py <in.png> <out.png>
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
alpha = np.clip(1 - (g - np.maximum(r, b) - 25) / 70, 0, 1)
fg = alpha > 0.5
lab, n = ndimage.label(fg)
if n:
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > sizes.max() * 0.02])
    alpha = alpha * ndimage.binary_dilation(keep, iterations=3)
g2 = np.minimum(g, np.maximum(r, b))
lum = 0.299 * r + 0.587 * g2 + 0.114 * b
rgba = np.dstack([lum, lum, lum, alpha * 255]).clip(0, 255).astype(np.uint8)
ys, xs = np.nonzero(alpha > 0.05)
im = Image.fromarray(rgba, 'RGBA').crop((xs.min() - 8, ys.min() - 8, xs.max() + 9, ys.max() + 9))
im.save(sys.argv[2], optimize=True)
print(im.size)
