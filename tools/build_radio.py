"""Build the office radio: announcer voiced with ElevenLabs, the public-domain records, all through an old-radio chain.

python3 tools/build_radio.py <records dir>        (records downloaded from the Commons pages in game/radio/broadcast.json)
- game/radio/broadcast.json: the program (announcer lines in order; a line's `then` names the record that follows it)
- voices the announcer into game/radio/voice/ (file = hash of the line, so editing a line re-voices only that one)
- writes demo/office-walk/radio/: one mono mp3 per segment, and radio.json (the playlist the game loops)
Old-radio chain: mono, 1930 receiver band (about 200 Hz to 3.6 kHz), a little valve saturation and compression,
a quiet bed of hiss and hum mixed under each segment.
"""
import hashlib, json, os, subprocess, sys, time, urllib.request, urllib.error

REC = sys.argv[1]
B = json.load(open('game/radio/broadcast.json'))
VOICE = B['announcer']['voice_id']
os.makedirs('game/radio/voice', exist_ok=True)
OUT = 'demo/office-walk/radio'; os.makedirs(OUT, exist_ok=True)


def tts(text, dst):
    body = json.dumps({'text': text, 'model_id': 'eleven_v4'}).encode()
    for a in range(6):
        try:
            data = urllib.request.urlopen(urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128', data=body,
                                          headers={'content-type': 'application/json', 'xi-api-key': 'proxy-injected'}), timeout=120).read()
            open(dst, 'wb').write(data); return
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 503): time.sleep(3 + 4 * a); continue
            raise
    raise RuntimeError('tts failed')


def radio(src, dst, music=False):
    """the receiver: band-limit, warm it up, squash it a little, and lay hiss and mains hum underneath"""
    chain = ('highpass=f=200,highpass=f=200,lowpass=f=3600,lowpass=f=3600,'
             'acompressor=threshold=-20dB:ratio=3:attack=10:release=200,'
             'asoftclip=type=tanh:param=1.4,volume=-2dB,equalizer=f=1200:t=q:w=1:g=3')
    if music:
        chain = 'loudnorm=I=-20:TP=-3,' + chain
    else:
        chain = 'loudnorm=I=-15:TP=-2,' + chain
    if not music:
        chain += ',volume=2.5dB,alimiter=limit=0.9'      # the announcer sits level with the records
    flt = (f'[0:a]aformat=channel_layouts=mono,{chain}[s];'
           'anoisesrc=color=pink:amplitude=0.012:sample_rate=44100[n];'
           'sine=f=60:sample_rate=44100,volume=0.004[h];'
           '[n][h]amix=inputs=2:duration=shortest,highpass=f=150,lowpass=f=5000[bed];'
           '[s][bed]amix=inputs=2:duration=first:normalize=0,afade=t=in:d=0.15[o]')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-filter_complex', flt, '-map', '[o]', '-ac', '1', '-ar', '22050', '-b:a', '48k', dst], check=True)


playlist = []
for i, seg in enumerate(B['program']):
    h = hashlib.sha1(seg['say'].encode()).hexdigest()[:10]
    raw = f'game/radio/voice/{h}.mp3'
    if not os.path.exists(raw):
        tts(f"{seg.get('tag', '')} {seg['say']}".strip(), raw); print('voiced', h, seg['say'][:50])
    radio(raw, f'{OUT}/say-{h}.mp3')
    playlist.append({'kind': 'say', 'file': f'say-{h}.mp3', 'text': seg['say']})
    if seg.get('then'):
        r = B['records'][seg['then']]
        dst = f"{OUT}/rec-{seg['then']}.mp3"
        if not os.path.exists(os.path.join(REC, r['file'])):
            print('MISSING record', r['file']); continue
        radio(os.path.join(REC, r['file']), dst, music=True)
        playlist.append({'kind': 'record', 'file': f"rec-{seg['then']}.mp3", 'title': r['title'], 'artist': r['artist'], 'year': r['year']})
keep = {p['file'] for p in playlist} | {'radio.json'}
for f in sorted(os.listdir(OUT)):
    if f not in keep: print('stale (not in the program):', f)
json.dump({'station': B['station'], 'playlist': playlist}, open(f'{OUT}/radio.json', 'w'), indent=1, ensure_ascii=False)
print(len(playlist), 'segments,', round(sum(os.path.getsize(f'{OUT}/{p["file"]}') for p in playlist) / 1e6, 1), 'MB')
