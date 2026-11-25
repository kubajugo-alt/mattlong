"""Prepare ElevenLabs sound effects for the engine.

python3 tools/process_sfx.py   (audio/sfx/raw/*.mp3 -> demo/office-walk/sfx/)
- beds (bed-*): loudness-normalised to -30 LUFS (the engine loops them with crossfades)
- footsteps (steps-*): cut into single steps at the onsets (energy peaks), each normalised, steps-<floor>-<n>.mp3
- one-shots: normalised to -24 LUFS
"""
import os, subprocess, json, glob
import numpy as np

SRC = 'audio/sfx/raw'; OUT = 'demo/office-walk/sfx'; os.makedirs(OUT, exist_ok=True)
SR = 44100

def decode(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

def encode(x, p, lufs):
    tmp = p + '.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', tmp], input=x.astype(np.float32).tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', f'loudnorm=I={lufs}:TP=-2:LRA=11', '-ar', '44100', '-b:a', '96k', p])
    os.remove(tmp)

info = {}
for p in sorted(glob.glob(SRC + '/*.mp3')):
    n = os.path.basename(p)[:-4]; x = decode(p)
    if n.startswith('bed-'):
        encode(x, f'{OUT}/{n}.mp3', -30); info[n] = round(len(x) / SR, 2)
    elif n.startswith('steps-'):
        # onsets: frames whose energy jumps well above the recent level, at least 0.3 s apart
        hop = 256; e = np.array([np.sqrt(np.mean(x[i:i + 1024] ** 2)) for i in range(0, len(x) - 1024, hop)])
        bg = np.convolve(e, np.ones(40) / 40, 'same'); thr = np.percentile(e, 70)
        on, last = [], -10**9
        for i in range(1, len(e)):
            if e[i] > thr and e[i] > bg[i] * 1.8 and e[i - 1] <= e[i] and (i - last) * hop > 0.30 * SR:
                on.append(i * hop); last = i
        k = 0
        for s in on[:10]:
            a = max(0, s - int(0.01 * SR)); seg = x[a:a + int(0.42 * SR)].copy()
            if len(seg) < 0.2 * SR: continue
            f = int(0.12 * SR); seg[-f:] *= np.linspace(1, 0, f); seg[:64] *= np.linspace(0, 1, 64)
            k += 1; encode(seg, f'{OUT}/{n}-{k}.mp3', -26)
        info[n] = k
    else:
        encode(x, f'{OUT}/{n}.mp3', -24); info[n] = round(len(x) / SR, 2)
json.dump(info, open(f'{OUT}/index.json', 'w'), indent=1); print(info)
