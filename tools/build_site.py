"""Assemble the playable Prologue into site/ (deployed to Netlify).

python3 tools/build_site.py
- the room engine and all room/sprite/sound/UI assets from demo/office-walk/
- game/web/game.js + game.css (the game layer), the ink runtime (inkjs), the compiled script prologue.json
  and paths.json (every knot.stitch, so the game knows which interactions the script covers)
- the voice track from voices/prologue/ (mp3 + Rhubarb cues + lines.json) as site/voice/
Needs inkjs (npm i inkjs@2.2.3) for the compiler: INKJS=<node_modules dir>.
"""
import json, os, re, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
NM = os.environ.get('INKJS', '/tmp/claude-0/-home-user/0f7a7501-1f63-5427-950d-2107e85f38a7/scratchpad/inkc/node_modules')
if os.path.exists(SITE):
    shutil.rmtree(SITE)
shutil.copytree(os.path.join(ROOT, 'demo/office-walk'), SITE, ignore=shutil.ignore_patterns('audio'))
for f in ['game.js', 'game.css']:
    shutil.copy(os.path.join(ROOT, 'game/web', f), SITE)
shutil.copy(os.path.join(NM, 'inkjs/dist/ink.js'), os.path.join(SITE, 'ink.js'))
# footsteps: each floor's ten steps packed into one file, one second apiece (the engine slices them; keeps the
# page under its file limit)
for floor in ('wood', 'tile', 'cobble'):
    parts = [os.path.join(SITE, 'sfx', f'steps-{floor}-{k}.mp3') for k in range(1, 11)]
    if all(os.path.exists(p) for p in parts):
        inputs = sum((['-i', p] for p in parts), [])
        pads = ''.join(f'[{k}:a]aformat=sample_rates=44100:channel_layouts=mono,apad=whole_dur=1,atrim=0:1[a{k}];' for k in range(10))
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *inputs, '-filter_complex', pads + ''.join(f'[a{k}]' for k in range(10)) + 'concat=n=10:v=0:a=1[o]',
                        '-map', '[o]', '-ar', '44100', '-ac', '1', '-c:a', 'pcm_s16le', os.path.join(SITE, 'sfx', f'steps-{floor}.wav')], check=True)
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', os.path.join(SITE, 'sfx', f'steps-{floor}.wav'), '-b:a', '96k', os.path.join(SITE, 'sfx', f'steps-{floor}.mp3')], check=True)
        os.remove(os.path.join(SITE, 'sfx', f'steps-{floor}.wav'))
        for p in parts: os.remove(p)
# voice track
os.makedirs(os.path.join(SITE, 'voice'))
cues = {}
for f in os.listdir(os.path.join(ROOT, 'voices/prologue')):
    src = os.path.join(ROOT, 'voices/prologue', f)
    if f.endswith('.mp3') or f == 'lines.json':
        shutil.copy(src, os.path.join(SITE, 'voice', f))
    elif f.endswith('.json') and not f.startswith('qa'):
        cues[f[:-5]] = json.load(open(src))['mouthCues']          # every line's mouth cues in one file
json.dump(cues, open(os.path.join(SITE, 'voice', 'cues.json'), 'w'), separators=(',', ':'))
# compile the script
ink = os.path.join(ROOT, 'game/ink/prologue.ink')
js = """const { Compiler } = require('inkjs/compiler/Compiler'); const fs = require('fs'); const errs = [];
const s = new Compiler(fs.readFileSync(process.argv[1], 'utf8'), { errorHandler: m => errs.push(m) }).Compile();
if (errs.length) { console.error(errs.join('\\n')); process.exit(1); } fs.writeFileSync(process.argv[2], s.ToJson());"""
subprocess.run(['node', '-e', js, ink, os.path.join(SITE, 'prologue.json')], check=True, env={**os.environ, 'NODE_PATH': NM})
paths, knot = [], None
for line in open(ink, encoding='utf-8'):
    m = re.match(r'\s*===\s*(?:function\s+)?(\w+)', line)
    if m: knot = m.group(1); paths.append(knot); continue
    m = re.match(r'\s*=\s*(\w+)\s*$', line)
    if m and knot: paths.append(knot + '.' + m.group(1))
json.dump(paths, open(os.path.join(SITE, 'paths.json'), 'w'))
# the page: a proper document, the game's title, styles and scripts
html = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
html = re.sub(r'<title>.*?</title>', '<title>Matt Long: The Bloody Angle</title>', html, count=1)
html = re.sub(r'<meta charset="utf-8">\s*', '', html, count=1)
html = html.replace('family=Jost:wght@400;500;600&family=Special+Elite', 'family=Jost:wght@400;500;600&family=Caveat:wght@400;600&family=Special+Elite')
head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="A noir point-and-click adventure. New York, winter 1930. Prologue: Rent Day.">\n')
html = head + html.replace('</style>', '</style>\n<link rel="stylesheet" href="game.css">', 1)
html = html.replace('<div class="wrap">', '</head>\n<body>\n<div class="rotate">Turn your phone sideways to play.</div>\n<div class="wrap">', 1)
html += '\n<script src="ink.js"></script>\n<script src="game.js"></script>\n</body>\n</html>\n'
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
open(os.path.join(SITE, '_headers'), 'w').write('/*\n  Cache-Control: public, max-age=3600\n/index.html\n  Cache-Control: no-cache\n')
open(os.path.join(SITE, 'netlify.toml'), 'w').write('[build]\n  publish = "."\n  command = ""\n')
size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(SITE) for f in fs)
print('site/ built:', len(paths), 'script entry points,', round(size / 1e6, 1), 'MB')

# a variant for a claude.ai page: the page gets its document wrapper from the host, and no Netlify files
ART = os.path.join(ROOT, 'site-artifact')
if os.path.exists(ART):
    shutil.rmtree(ART)
shutil.copytree(SITE, ART, ignore=shutil.ignore_patterns('netlify.toml', '_headers'))
page = open(os.path.join(ART, 'index.html'), encoding='utf-8').read()
for tag in ['<!doctype html>\n', '<html lang="en">\n', '<head>\n', '<meta charset="utf-8">\n', '</head>\n', '<body>\n', '</body>\n', '</html>\n']:
    page = page.replace(tag, '', 1)
page = re.sub(r'<meta name="viewport"[^>]*>\n', '', page, count=1)
open(os.path.join(ART, 'index.html'), 'w', encoding='utf-8').write(page)
print('site-artifact/:', sum(len(fs) for _, _, fs in os.walk(ART)), 'files')
