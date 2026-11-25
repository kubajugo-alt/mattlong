"""Check voiced lines against the script: transcribe each take (ElevenLabs Scribe) and compare the words.

python3 tools/voice_qa.py voices/prologue            -> voices/prologue/qa.json, prints the takes that don't match
A take fails when its words differ from the script line (repeats, stumbles, added or missing words).
"""
import json, os, re, subprocess, sys, difflib, concurrent.futures as cf

D = sys.argv[1]
man = json.load(open(f'{D}/lines.json'))
qa_p = f'{D}/qa.json'
qa = json.load(open(qa_p)) if os.path.exists(qa_p) else {}
words = lambda s: re.findall(r"[a-z0-9']+", s.lower().replace('’', "'"))


def check(i):
    v = man[i]
    r = subprocess.run(['curl', '-s', '-X', 'POST', 'https://api.elevenlabs.io/v1/speech-to-text', '-H', 'xi-api-key: proxy-injected',
                        '-F', 'model_id=scribe_v1', '-F', f'file=@{D}/{v["file"]}'], capture_output=True, text=True)
    try:
        heard = json.loads(r.stdout)['text']
    except Exception:
        return i, None
    a, b = words(v['text']), words(heard)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return i, {'file': v['file'], 'mtime': os.path.getmtime(f'{D}/{v["file"]}'), 'heard': heard, 'ratio': round(ratio, 3), 'extra_words': len(b) - len(a)}


todo = [i for i in man if qa.get(i, {}).get('mtime') != os.path.getmtime(f'{D}/{man[i]["file"]}')]   # re-check any take that was re-voiced
with cf.ThreadPoolExecutor(6) as ex:
    for i, res in ex.map(check, todo):
        if res:
            qa[i] = res
json.dump(qa, open(qa_p, 'w'), indent=1, ensure_ascii=False)
bad = {i: q for i, q in qa.items() if i in man and (q['ratio'] < 0.9 or abs(q['extra_words']) >= 2)}
for i, q in sorted(bad.items(), key=lambda x: x[1]['ratio']):
    print(f"{q['ratio']:.2f} {man[i]['speaker']:7} {man[i]['text'][:60]!r} -> {q['heard'][:70]!r}")
print(len(qa), 'checked,', len(bad), 'to redo')
json.dump(sorted(bad), open(f'{D}/qa_bad.json', 'w'))
