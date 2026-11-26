"""Trace the torch outlines: the exact silhouette of each live hotspot's object, for drawing (clicks keep the
simpler 'polygons').

python3 tools/trace_outlines.py [room ...]
- people: the edge of their cut-out sprite (occ alpha, first frame), kept inside their hotspot area
- things: GrabCut on the painting (background plus the visible sprites), seeded with the hotspot polygon as
  "probably the object" and everything else as background
Writes 'outline' (list of polygons, scene px) into art/scenes/<room>/hotspots.json and demo/office-walk/<room>/hotspots.json.
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image

PFX = {'office-day': 'office', 'office-night': 'office', 'corridor': 'corridor', 'pete-kate-flat': 'flat', 'doyers-street': 'doyers',
       'tea-house': 'tea', 'pawnshop': 'pawn', 'alley': 'alley'}
OCC_OF = {'pete': 'pete-seated', 'kate': 'kate-at-table', 'lee-wing': 'lee-wing', 'sol': 'sol', 'junkie': 'junkie', 'newsboy': 'newsboy'}
paths = set(json.load(open('site/paths.json')))
rooms = sys.argv[1:] or list(PFX)
for room in rooms:
    D = f'demo/office-walk/{room}'; sc = json.load(open(f'{D}/scene.json'))
    img = Image.open(f'{D}/bg.webp').convert('RGBA'); W, H = img.size
    occ = {}
    for o in sc['objects']:
        try:
            oc = Image.open(f'{D}/occ/{o["name"]}.webp').convert('RGBA'); w, h = o['bbox'][2] - o['bbox'][0], o['bbox'][3] - o['bbox'][1]
            fr = oc.crop((0, 0, w, h)); occ[o['name']] = (o, np.asarray(fr)[..., 3])
            if not o.get('hidden'): img.alpha_composite(fr, tuple(o['bbox'][:2]))
        except Exception: pass
    rgb = np.ascontiguousarray(np.asarray(img.convert('RGB'))[..., ::-1])
    hj = json.load(open(f'{D}/hotspots.json'))
    for hs in hj['hotspots']:
        if not any(q.startswith(PFX[room] + '__' + hs['id'].replace('-', '_') + '.') for q in paths): continue
        poly = np.zeros((H, W), np.uint8)
        for pl in hs['polygons']: cv2.fillPoly(poly, [np.array(pl, np.int32)], 1)
        x0, y0, x1, y1 = hs['bbox']; pad = 24
        X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
        if hs['id'] not in OCC_OF and ('mapped_polygons' not in hs or any(k in hs['id'] for k in ('door', 'window', 'cabinet', 'bookcase', 'ledgers'))):
            hs['outline'] = hs['polygons']; continue      # traced from the painting already, or a true rectangle (doors, windows, cabinets)
        if hs['id'] in OCC_OF and OCC_OF[hs['id']] in occ:
            o, a = occ[OCC_OF[hs['id']]]; m = np.zeros((H, W), np.uint8)
            m[o['bbox'][1]:o['bbox'][1] + a.shape[0], o['bbox'][0]:o['bbox'][0] + a.shape[1]] = (a > 128)
            m &= cv2.dilate(poly, np.ones((15, 15), np.uint8))
        else:
            gm = np.full((Y1 - Y0, X1 - X0), cv2.GC_BGD, np.uint8)
            pc = poly[Y0:Y1, X0:X1]
            gm[cv2.dilate(pc, np.ones((9, 9), np.uint8)) > 0] = cv2.GC_PR_BGD
            gm[pc > 0] = cv2.GC_PR_FGD
            gm[cv2.erode(pc, np.ones((25, 25), np.uint8)) > 0] = cv2.GC_PR_FGD
            bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
            try:
                cv2.grabCut(rgb[Y0:Y1, X0:X1].copy(), gm, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
                sub = ((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)).astype(np.uint8)
            except cv2.error:
                sub = pc.copy()
            # GrabCut can lose a thin or low-contrast object: then keep the polygon
            if sub.sum() < 0.15 * max(1, pc.sum()):          # lost it: try once more from the box alone
                gm2 = np.zeros(pc.shape, np.uint8); bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
                r = (x0 - X0 + 2, y0 - Y0 + 2, max(4, x1 - x0 - 4), max(4, y1 - y0 - 4))
                try: cv2.grabCut(rgb[Y0:Y1, X0:X1].copy(), gm2, r, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT); sub = ((gm2 == 1) | (gm2 == 3)).astype(np.uint8) & cv2.dilate(pc, np.ones((9, 9), np.uint8))
                except cv2.error: pass
            if sub.sum() < 0.15 * max(1, pc.sum()): sub = pc.copy()
            m = np.zeros((H, W), np.uint8); m[Y0:Y1, X0:X1] = sub
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > max(60, 0.06 * st[1:, cv2.CC_STAT_AREA].max())] if n > 1 else []
        cs = []
        for i in keep:
            c, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cc in c:
                cc = cv2.approxPolyDP(cc, 1.6, True)
                if len(cc) >= 3: cs.append(cc[:, 0, :].tolist())
        hs['outline'] = cs or hs['polygons']
    for out in (f'{D}/hotspots.json', f'art/scenes/{room}/hotspots.json'):
        if os.path.exists(os.path.dirname(out)): json.dump(hj, open(out, 'w'), indent=1)
    print(room, 'traced')
