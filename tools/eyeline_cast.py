"""Proportion check for the cast: every figure scaled to the same eye height above the floor.

python3 tools/eyeline_cast.py art/cast <pose_landmarker.task> <out.jpg>
With equal eye heights, differences in head size, torso and leg length are directly visible.
Also prints a face ratio (eye-to-mouth / eye-to-floor) per figure; Matt is the reference.
Joints under clothing are unreliable for the pose model, but eyes and mouth are found reliably.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

root, model, out = sys.argv[1:4]
cast = json.load(open(os.path.join(root, 'cast.json')))
det = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model), num_poses=1, min_pose_detection_confidence=0.1, min_pose_presence_confidence=0.1))
T = 700; base = T + 140; ims = []; ratios = {}
for c in cast['characters']:
    im = Image.open(os.path.join(root, 'final', c['id'] + '.png'))
    floor = np.nonzero(np.asarray(im)[..., 3].max(1) > 128)[0].max()
    eye = mouth = None
    for pad in (100, 300):
        bg = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (128, 128, 128, 255)); bg.alpha_composite(im, (pad, pad))
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(bg.convert('RGB'))))
        if r.pose_landmarks:
            L = r.pose_landmarks[0]; H = bg.height
            eye = (L[2].y + L[5].y) / 2 * H - pad; mouth = (L[9].y + L[10].y) / 2 * H - pad; break
    if eye is None or mouth - eye < 5:
        eye = im.height * 0.09; ratios[c['id']] = None
    else:
        ratios[c['id']] = (mouth - eye) / (floor - eye)
    s = T / (floor - eye)
    ims.append((c, im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS), int(floor * s)))
W = sum(i.width for _, i, _ in ims) + 30 * len(ims) + 40
sheet = Image.new('RGBA', (W, base + 60), (34, 33, 38, 255)); d = ImageDraw.Draw(sheet)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
x = 30
for c, im, fl in ims:
    sheet.alpha_composite(im, (x, base - fl)); d.text((x, base + 14), c['name'].split(' (')[0].replace('Salvatore "Sal" ', 'Sal '), fill=(220, 220, 220, 255), font=f); x += im.width + 30
d.line((0, base - T, W, base - T), fill=(255, 220, 0, 200), width=2)
d.text((30, base - T - 28), 'eye level', fill=(255, 220, 0, 255), font=f)
sheet.convert('RGB').save(out, quality=88)
ref = ratios['matt']
for k, v in ratios.items():
    print(f'{k:16s}', 'n/a' if v is None else f'{v:.4f}  {(v - ref) / ref:+.0%}')
