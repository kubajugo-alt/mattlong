// Render Matt at the moments matching Muybridge's Plate 1 frames and stack them under the photos.
//   node compare.js <page dir with window.__dbg hooks> <muybridge frames dir> <out.png>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [root, mdir, outPng] = process.argv.slice(2);
const types = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png' };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl'] });
  const ctx = await b.newContext({ viewport: { width: 700, height: 760 } });
  await ctx.route('http://review.local/**', (r) => {
    const u = new URL(r.request().url()); const f = path.join(root, decodeURIComponent(u.pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    let body = fs.readFileSync(f); if (f.endsWith('index.html')) body = '<!doctype html><meta charset=utf-8>' + body;
    r.fulfill({ status: 200, body, contentType: types[path.extname(f)] || 'application/octet-stream' });
  });
  const p = await ctx.newPage();
  await p.goto('http://review.local/index.html#m0-rig-v2'); await p.waitForTimeout(2500);
  const box = p.locator('.stage > div').first();
  // Muybridge F3 = heel strike of the forward leg; frames are ~1/14 of a stride apart
  for (let k = 1; k <= 12; k++) {
    const ph = (((k - 3) / 14) % 1 + 1) % 1;
    await p.evaluate((ph) => { window.__dbg.pause(false); window.__dbg.setT(ph * window.__dbg.T()); }, ph);
    await p.waitForTimeout(40); await p.evaluate(() => window.__dbg.pause(true)); await p.waitForTimeout(120);
    await box.screenshot({ path: path.join(path.dirname(outPng), 'cmp_m' + k + '.png') });
  }
  await b.close();
  const { execSync } = require('child_process');
  execSync(`python3 - <<'PY'
from PIL import Image
import os
d='${path.dirname(outPng)}'; md='${mdir}'
tops=[Image.open(os.path.join(md,f'f{k}.png')).convert('RGB') for k in range(1,13)]
bots=[]
for k in range(1,13):
    im=Image.open(os.path.join(d,f'cmp_m{k}.png')).convert('RGB'); w,h=im.size
    c=im.crop((int(w*0.28),int(h*0.04),int(w*0.72),int(h*0.93)))
    bots.append(c)
H=560
tops=[t.resize((int(t.width*H/t.height),H)) for t in tops]
bots=[b.resize((int(b.width*H/b.height),H)) for b in bots]
W=max(sum(t.width for t in tops),sum(b.width for b in bots))
s=Image.new('RGB',(W,H*2+10),'white'); x=0
for t in tops: s.paste(t,(x,0)); x+=t.width
x=0
for b in bots: s.paste(b,(x,H+10)); x+=b.width
s.thumbnail((2600,2600)); s.save('${outPng}')
PY`);
})();
