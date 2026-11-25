"""Copy face patches (mouth shapes, blinks) into the scene data and the demo.

python3 tools/install_faces.py
Props: art/scenes/<room>/occ/<name>-face.png + 'face' on the scene object (rects in the object's occ-frame pixels).
Matt: demo sprites/matt-<dir>-face.webp + 'face' in sprites/matt.json. A prop's tone (night) is applied here.
"""
import json, os
import numpy as np
from PIL import Image

def toned(im, t):
    if not t:
        return im
    a = np.asarray(im).astype(np.float32); a[..., :3] *= t
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')

PROPS = {'kate': [('pete-kate-flat', 'kate-at-table')], 'pete': [('pete-kate-flat', 'pete-seated')], 'lee': [('tea-house', 'lee-wing')],
         'sol': [('pawnshop', 'sol')], 'junkie': [('alley', 'junkie')], 'newsboy': [('doyers-street', 'newsboy')],
         'inez': [('office-night', 'inez-seated'), ('office-day', 'inez-seated')]}
for fid, places in PROPS.items():
    face = json.load(open(f'art/faces/{fid}/face.json')); sheet = Image.open(f'art/faces/{fid}/face.png').convert('RGBA')
    ref_room = json.load(open(f'art/faces/{fid}/map.json'))['target'].split('/')[0]
    ref = [o for o in json.load(open(f'art/scenes/{ref_room}/scene.json'))['objects'] if o['name'] == places[0][1]][0]['bbox']
    for room, name in places:
        L = json.load(open(f'art/rooms/labels/{room}.legend.json')); pr = [p for p in L['props'] if p['name'] == name][0]
        for base in [f'art/scenes/{room}', f'demo/office-walk/{room}']:
            sc = json.load(open(f'{base}/scene.json')); ob = [o for o in sc['objects'] if o['name'] == name][0]
            f = dict(face); dx, dy = ref[0] - ob['bbox'][0], ref[1] - ob['bbox'][1]          # same placement in both offices
            for k in ('mouth', 'eyes'):
                if f.get(k): f[k] = [f[k][0] + dx, f[k][1] + dy, f[k][2], f[k][3]]
            ob['face'] = f; json.dump(sc, open(f'{base}/scene.json', 'w'), indent=1)
            im = toned(sheet, pr.get('tone'))
            if base.startswith('art'):
                im.save(f'{base}/occ/{name}-face.png')
            else:
                im.save(f'{base}/occ/{name}-face.webp', lossless=True)
        print(fid, room, name, f.get('mouth'), f.get('eyes'))
sp = json.load(open('demo/office-walk/sprites/matt.json'))
for d in ['front', 'side']:
    sp[d]['face'] = json.load(open(f'art/faces/matt-{d}/face.json'))
    Image.open(f'art/faces/matt-{d}/face.png').save(f'demo/office-walk/sprites/matt-{d}-face.webp', lossless=True)
json.dump(sp, open('demo/office-walk/sprites/matt.json', 'w'))
print('matt', {d: sp[d]['face']['mouth'] for d in ['front', 'side']})
