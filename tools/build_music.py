"""Room music: trim, level and encode the tracks chosen in game/music/rooms.json into demo/office-walk/music/.

python3 tools/build_music.py
Masters: art/music/suno/<title>.mp3. Leading and trailing silence is cut (so the loop has no gap), loudness set to
-20 LUFS, stereo 96 kb/s. Writes music/music.json {room: file} plus the volume for the engine.
"""
import json, os, re, subprocess

C = json.load(open('game/music/rooms.json'))
OUT = 'demo/office-walk/music'; os.makedirs(OUT, exist_ok=True)
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
files = {}
for room, title in C['rooms'].items():
    dst = f'{OUT}/{slug(title)}.mp3'
    if not os.path.exists(dst):      # two passes (trim, then level): one long filter chain runs very slowly
        tmp = dst[:-4] + '.tmp.wav'
        trim = 'silenceremove=start_periods=1:start_threshold=-55dB,areverse,silenceremove=start_periods=1:start_threshold=-55dB,areverse'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', f'art/music/suno/{title}.mp3', '-af', trim, tmp], check=True)
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-20:TP=-2', '-ar', '44100', '-b:a', '96k', dst], check=True)
        os.remove(tmp)
    files[room] = os.path.basename(dst)
keep = set(files.values()) | {'music.json'}
for f in os.listdir(OUT):
    if f not in keep: print('stale:', f)
json.dump({'volume': C['volume'], 'rooms': files}, open(f'{OUT}/music.json', 'w'), indent=1)
print(len(files), 'rooms,', round(sum(os.path.getsize(f'{OUT}/{f}') for f in set(files.values())) / 1e6, 1), 'MB')
