"""Voice an ink script with ElevenLabs, one mp3 per line, plus Rhubarb lip-sync cues for spoken lines.

python3 tools/voice_lines.py game/ink/prologue.ink voices/prologue [--only N] [--dry]

- Lines are `SPEAKER: text` (also inside {~a|b|c} shuffles). `VO` is Matt's voice-over.
- File name = speaker + hash of the exact text, so editing a line only re-voices that line; existing files are kept.
- Voices come from voices/cast.json (plus the newsboy); each speaker gets a short delivery direction (eleven_v4 tags).
- Writes voices/<out>/lines.json: {id: {speaker, text, voice_id, file, cues}}.
- The API key is injected by the network proxy (no key in code or env).
"""
import hashlib, json, os, re, subprocess, sys, urllib.request, concurrent.futures as cf

INK, OUT = sys.argv[1], sys.argv[2]
ONLY = int(sys.argv[sys.argv.index('--only') + 1]) if '--only' in sys.argv else None
DRY = '--dry' in sys.argv
RHUBARB = os.environ.get('RHUBARB', '/tmp/claude-0/-home-user/0f7a7501-1f63-5427-950d-2107e85f38a7/scratchpad/rhubarb/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb')

cast = json.load(open('voices/cast.json'))['voices']
VOICE = {'VO': 'matt', 'MATT': 'matt', 'PETE': 'pete', 'KATE': 'kate', 'INEZ': 'inez', 'LEE': 'lee', 'SOL': 'sol', 'JUNKIE': 'junkie'}
NEWSBOY = 'loY1uopAz31XyhAEhNSa'      # VALF, used for the street calls
DIRECTION = {                         # eleven_v4 audio tags: one or two words each (long directions made it repeat phrases)
    'VO': '[quietly]', 'MATT': '[dryly]', 'PETE': '[cheerfully]', 'KATE': '[crisply]', 'INEZ': '[softly]',
    'LEE': '[calmly]', 'SOL': '[wearily]', 'JUNKIE': '[nervously]', 'NEWSBOY': '[shouting]',
}


def lines_of(path):
    out = []
    for raw in open(path, encoding='utf-8'):
        s = raw.strip()
        if not s or s.startswith('//'):
            continue
        parts = s[2:-1].split('|') if s.startswith('{~') and s.endswith('}') else [s]
        for p in parts:
            m = re.match(r'([A-Z]+):\s*(.+)$', p.strip())
            if m and m.group(1) in DIRECTION:
                text = m.group(2).strip()
                if re.fullmatch(r'[.\s…]*', text):       # a silent beat ("KATE: ...") is not voiced
                    continue
                out.append((m.group(1), text))
    seen, uniq = set(), []
    for sp, t in out:
        if (sp, t) not in seen:
            seen.add((sp, t)); uniq.append((sp, t))
    return uniq


def line_id(sp, text):
    return f"{sp.lower()}-{hashlib.sha1((sp + '|' + text).encode()).hexdigest()[:10]}"


def voice_of(sp):
    return NEWSBOY if sp == 'NEWSBOY' else cast[VOICE[sp]]['voice_id']


def tts(sp, text, dst):
    body = json.dumps({'text': f"{DIRECTION[sp]} {text}", 'model_id': cast_model}).encode()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice_of(sp)}?output_format=mp3_44100_128', data=body,
                                 headers={'content-type': 'application/json', 'accept': 'audio/mpeg', 'xi-api-key': 'proxy-injected'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    open(dst, 'wb').write(data)
    return len(data)


def lipsync(sp, text, mp3, dst):
    wav = mp3[:-4] + '.wav'; txt = mp3[:-4] + '.txt'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '16000', wav], check=True)
    open(txt, 'w').write(text)
    subprocess.run([RHUBARB, '-q', '-f', 'json', '-d', txt, '--extendedShapes', 'GHX', '-o', dst, wav], check=True)
    os.remove(wav); os.remove(txt)


cast_model = json.load(open('voices/cast.json')).get('model', 'eleven_v4')
os.makedirs(OUT, exist_ok=True)
L = lines_of(INK)
if ONLY:
    L = L[:ONLY]
man_p = os.path.join(OUT, 'lines.json')
man = json.load(open(man_p)) if os.path.exists(man_p) else {}
todo = [(sp, t) for sp, t in L if not os.path.exists(os.path.join(OUT, line_id(sp, t) + '.mp3'))]
print(f'{len(L)} lines, {sum(len(t) for _, t in L)} chars; to voice now: {len(todo)} lines, {sum(len(t) for _, t in todo)} chars')
if DRY:
    sys.exit()


def work(item):
    sp, t = item; i = line_id(sp, t); mp3 = os.path.join(OUT, i + '.mp3')
    for attempt in range(3):
        try:
            tts(sp, t, mp3); break
        except Exception as e:
            err = e
    else:
        return i, f'FAILED {err}'
    if sp != 'VO':                    # voice-over is in Matt's head: no lip sync
        lipsync(sp, t, mp3, os.path.join(OUT, i + '.json'))
    return i, 'ok'


with cf.ThreadPoolExecutor(4) as ex:
    for i, res in ex.map(work, todo):
        if res != 'ok':
            print(i, res)
for sp, t in L:
    i = line_id(sp, t)
    if os.path.exists(os.path.join(OUT, i + '.mp3')):
        man[i] = {'speaker': sp, 'text': t, 'voice_id': voice_of(sp), 'file': i + '.mp3', 'cues': (i + '.json') if sp != 'VO' else None}
json.dump(man, open(man_p, 'w'), indent=1, ensure_ascii=False)
print('voiced', sum(1 for sp, t in L if os.path.exists(os.path.join(OUT, line_id(sp, t) + '.mp3'))), 'of', len(L))
