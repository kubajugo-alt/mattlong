const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2], out = process.argv[3];
const types = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.mp3': 'audio/mpeg' };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 2 });
  await ctx.route('http://review.local/**', (r) => {
    const u = new URL(r.request().url()); const f = path.join(root, decodeURIComponent(u.pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    let body = fs.readFileSync(f);
    if (f.endsWith('index.html')) body = '<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">' + body;
    r.fulfill({ status: 200, body, contentType: types[path.extname(f)] || 'application/octet-stream' });
  });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
  await p.goto('http://review.local/index.html#m0-rig-v2'); await p.waitForTimeout(2000);
  const box = p.locator('.stage > div').first();
  const shot = async (n) => box.screenshot({ path: out + '/' + n + '.png' });
  await p.click('.seg >> text=Rest'); await p.waitForTimeout(400); await shot('m_rest');
  await p.click('.seg >> text=Walk');
  for (let i = 0; i < 4; i++) { await p.waitForTimeout(400); await shot('m_walk' + i); }
  await p.click('.seg >> text=Gesture'); await p.waitForTimeout(2800); await shot('m_gesture');
  await p.check('#rig-mesh'); await p.click('.seg >> text=Walk'); await p.waitForTimeout(700); await shot('m_wire');
  console.log('errors', JSON.stringify(errs.slice(0, 5))); await b.close();
})();
