"""Measure body proportions of every cast figure with a pose model, relative to eye height.

python3 tools/measure_cast.py art/cast <pose_landmarker.task>
All values are fractions of eye height above the floor (soles), so hats don't matter:
  head  = eye-to-mouth distance x 3.2 (approximate head height)
  shoulder, hip, knee = height of the joint above the floor
Prints a table and flags figures more than 6% away from Matt.
"""
import json, os, sys
import numpy as np
from PIL import Image
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

root, model = sys.argv[1:3]
cast = json.load(open(os.path.join(root, 'cast.json')))
det = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model), num_poses=1, min_pose_detection_confidence=0.2))
rows = {}
for c in cast['characters']:
    im = Image.open(os.path.join(root, 'final', c['id'] + '.png'))
    bg = Image.new('RGBA', (im.width + 200, im.height + 100), (128, 128, 128, 255)); bg.alpha_composite(im, (100, 50))
    a = np.asarray(im)[..., 3]
    ys = np.nonzero(a.max(1) > 128)[0]; floor = ys.max() + 50
    rgb = bg.convert('RGB')
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(rgb)))
    if not r.pose_landmarks:
        rows[c['id']] = None; continue
    L = r.pose_landmarks[0]; W, H = rgb.size
    y = lambda i: L[i].y * H
    eye = (y(2) + y(5)) / 2; mouth = (y(9) + y(10)) / 2
    E = floor - eye
    rows[c['id']] = dict(head=3.2 * (mouth - eye) / E, shoulder=(floor - (y(11) + y(12)) / 2) / E,
                         hip=(floor - (y(23) + y(24)) / 2) / E, knee=(floor - (y(25) + y(26)) / 2) / E)
ref = rows['matt']
print(f"{'id':16s} {'head':>6s} {'shoulder':>8s} {'hip':>6s} {'knee':>6s}   off by (vs Matt)")
flag = []
for k, v in rows.items():
    if v is None: print(f'{k:16s} not detected'); continue
    d = {m: (v[m] - ref[m]) / ref[m] for m in v}
    worst = max(d, key=lambda m: abs(d[m]))
    mark = '  <-- ' + worst + f' {d[worst]:+.0%}' if abs(d[worst]) > 0.06 else ''
    if mark: flag.append(k)
    print(f"{k:16s} {v['head']:6.3f} {v['shoulder']:8.3f} {v['hip']:6.3f} {v['knee']:6.3f}{mark}")
json.dump({'rows': rows, 'flagged': flag}, open(os.path.join(root, 'proportions.json'), 'w'), indent=1)
print('flagged:', flag)
