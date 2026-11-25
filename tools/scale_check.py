"""Drop Matt (1.85 m) into a room at several floor points using the scale rule, to check a horizon.

python3 tools/scale_check.py <room.png> <horizon> <out.jpg> x,y [x,y ...]   (fractions of the image)
height_px = (feet_y - horizon) * H * 1.85 / 1.6
"""
import sys
from PIL import Image, ImageDraw
room, hor, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
bg = Image.open(room).convert('RGB'); W, H = bg.size
m = Image.open('art/cast/final/matt.png').convert('RGBA'); m = m.crop(m.getbbox())
d = ImageDraw.Draw(bg)
d.line([(0, hor * H), (W, hor * H)], fill=(255, 0, 0), width=3)
for p in sys.argv[4:]:
    x, y = [float(v) * s for v, s in zip(p.split(','), (W, H))]
    h = (y - hor * H) * 1.85 / 1.6
    if h < 10: continue
    f = m.resize((max(1, int(m.width * h / m.height)), int(h)), Image.LANCZOS)
    bg.paste(f, (int(x - f.width / 2), int(y - f.height)), f)
bg.resize((1100, int(1100 * H / W))).save(out, quality=82)
