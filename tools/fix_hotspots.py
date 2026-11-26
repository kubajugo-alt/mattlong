"""Apply the hand-drawn outlines in game/hotspots/outlines.json to the rooms' hotspots.json
(art/scenes/<room>/ and demo/office-walk/<room>/). The detected shape is kept as 'mapped_polygons',
so the mapping survives; re-running is safe.

python3 tools/fix_hotspots.py
"""
import json, os

FIX = json.load(open('game/hotspots/outlines.json'))
for room, fixes in FIX.items():
    if room == 'note':
        continue
    if isinstance(fixes, str):
        fixes = FIX[fixes]
    for d in (f'art/scenes/{room}', f'demo/office-walk/{room}'):
        p = f'{d}/hotspots.json'
        if not os.path.exists(p):
            continue
        hj = json.load(open(p))
        H = {h['id']: h for h in hj['hotspots']}
        for hid, f in fixes.items():
            h = H[hid]
            if 'polygons' in f:
                h.setdefault('mapped_polygons', h['polygons'])
                h['polygons'] = f['polygons']
                xs = [x for pl in f['polygons'] for x, _ in pl]; ys = [y for pl in f['polygons'] for _, y in pl]
                h['bbox'] = [min(xs), min(ys), max(xs), max(ys)]
            if 'z' in f:
                h['z'] = f['z']
        json.dump(hj, open(p, 'w'), indent=1)
        print(p, len(fixes), 'outlines')
