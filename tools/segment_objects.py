"""Find every object in a room painting and cut a precise outline for each.

GEMINI_API_KEY=... python3 tools/segment_objects.py <room.png> <out dir> [model]

1. Gemini (vision) lists every object with a label and a bounding box, on the whole image and
   on overlapping zoomed tiles so small items (an ashtray, a light switch) are found too.
2. Boxes from different tiles that are the same object are merged.
3. OpenCV GrabCut cuts each object's exact outline from inside its box.
Writes <out dir>/masks/<id>.png (full-size, white = object) and <out dir>/objects.json.
"""
import base64, io, json, os, sys, urllib.request
import numpy as np
import cv2
from PIL import Image

src, out = sys.argv[1:3]
model = sys.argv[3] if len(sys.argv) > 3 else 'gemini-3.5-flash'
key = os.environ['GEMINI_API_KEY']
os.makedirs(os.path.join(out, 'masks'), exist_ok=True)
img = Image.open(src).convert('RGB'); W, H = img.size
rgb = np.asarray(img)

PROMPT = ("You are mapping a point-and-click adventure game background so that every object can become a hotspot. "
          "Detect EVERY distinct physical object visible, large and small: each piece of furniture, each item on any "
          "surface (telephone, ashtray, bottle, glass, lamp, papers, typewriter...), each picture, certificate, notice "
          "or photo on the walls, the cork board and the pinned items on it as one group, the door, its handle and the "
          "window above it, windows and blinds, ceiling lamp, light switch, radiator, coat stand and each garment or hat "
          "on it or on hooks, the hat on the wall hook, the radio, books and boxes on each shelf as one group per shelf, "
          "each stack of papers or newspapers, the envelope on the floor, the drawers. Do not list walls, floor or ceiling. "
          "Return a JSON list; each entry has \"box_2d\" as [ymin, xmin, ymax, xmax] normalised to 0-1000 and \"label\", "
          "a short specific lowercase name (e.g. \"whiskey bottle\", \"framed police commendation\"). Give distinct "
          "objects distinct labels; number repeats (\"newspaper stack 1\").")


def ask(tile):
    buf = io.BytesIO(); tile.save(buf, 'PNG')
    body = {'contents': [{'parts': [{'inline_data': {'mime_type': 'image/png', 'data': base64.b64encode(buf.getvalue()).decode()}},
                                    {'text': PROMPT}]}],
            'generationConfig': {'temperature': 0.2, 'response_mime_type': 'application/json', 'maxOutputTokens': 32768}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                 data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'x-goog-api-key': key})
    r = json.load(urllib.request.urlopen(req, timeout=280))
    return json.loads(r['candidates'][0]['content']['parts'][0]['text'])


tiles = [(0, 0, W, H)]
for j in range(2):
    for i in range(3):
        tw, th = int(W * 0.45), int(H * 0.6)
        tiles.append((int(i * (W - tw) / 2), int(j * (H - th)), tw, th))
boxes = []
for (ox, oy, tw, th) in tiles:
    tile = img.crop((ox, oy, ox + tw, oy + th))
    s = 1536 / max(tw, th)
    try:
        res = ask(tile.resize((int(tw * s), int(th * s)), Image.LANCZOS))
    except Exception as e:
        print('tile failed', (ox, oy), str(e)[:80]); continue
    n = 0
    for e in res:
        try:
            b = e['box_2d']
            if isinstance(b, str): b = json.loads(b)
            y0, x0, y1, x1 = [float(v) for v in b]
        except Exception:
            continue
        bx = [ox + x0 / 1000 * tw, oy + y0 / 1000 * th, ox + x1 / 1000 * tw, oy + y1 / 1000 * th]
        # ignore boxes cut by the tile edge (the whole-image pass or another tile has them whole)
        edge = (x0 < 3 and ox > 0) or (y0 < 3 and oy > 0) or (x1 > 997 and ox + tw < W) or (y1 > 997 and oy + th < H)
        if bx[2] - bx[0] > 6 and bx[3] - bx[1] > 6 and not edge:
            boxes.append({'label': str(e.get('label', 'object')).strip().lower(), 'box': bx, 'whole': (ox, oy, tw, th) == (0, 0, W, H)}); n += 1
    print('tile', (ox, oy), n, 'boxes', flush=True)


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy; u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u else 0


# merge: same object found twice (high overlap); prefer the tile box (finer) over the whole-image one
merged = []
for b in sorted(boxes, key=lambda b: b['whole']):
    for m in merged:
        if iou(m['box'], b['box']) > 0.5:
            m['labels'].add(b['label']); break
    else:
        merged.append({'label': b['label'], 'labels': {b['label']}, 'box': b['box']})

bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
objs, used = [], {}
for m in sorted(merged, key=lambda m: (m['box'][0], m['box'][1])):
    x0, y0, x1, y1 = [int(round(v)) for v in m['box']]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    pad = max(6, int(0.08 * max(x1 - x0, y1 - y0)))
    cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    crop = bgr[cy0:cy1, cx0:cx1]
    gm = np.zeros(crop.shape[:2], np.uint8)
    rect = (x0 - cx0, y0 - cy0, max(2, x1 - x0), max(2, y1 - y0))
    try:
        cv2.grabCut(crop, gm, rect, np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64), 5, cv2.GC_INIT_WITH_RECT)
        mk = (gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)
    except cv2.error:
        mk = np.zeros(crop.shape[:2], bool)
    if mk.sum() < 0.15 * (x1 - x0) * (y1 - y0):          # GrabCut gave up: fall back to the box itself
        mk = np.zeros(crop.shape[:2], bool); mk[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = True
    full = np.zeros((H, W), np.uint8); full[cy0:cy1, cx0:cx1] = mk * 255
    base = m['label'].replace(' ', '-').replace('/', '-')
    used[base] = used.get(base, 0) + 1
    oid = base if used[base] == 1 else f'{base}-{used[base]}'
    Image.fromarray(full).save(os.path.join(out, 'masks', oid + '.png'), optimize=True)
    ys, xs = np.nonzero(full)
    objs.append({'id': oid, 'label': m['label'], 'also_seen_as': sorted(m['labels'] - {m['label']}),
                 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], 'area_px': int((full > 0).sum())})
json.dump({'image': os.path.basename(src), 'size': [W, H], 'model': model, 'objects': objs}, open(os.path.join(out, 'objects.json'), 'w'), indent=1)
print(len(objs), 'objects:', ', '.join(o['id'] for o in objs))
