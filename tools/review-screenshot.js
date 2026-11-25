const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2], out = process.argv[3];
const types = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.mp3': 'audio/mpeg' };
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1400, height: 950 } });
  await ctx.route('http://review.local/**', (r) => {
    const u = new URL(r.request().url()); const f = path.join(root, decodeURIComponent(u.pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    let body = fs.readFileSync(f);
    if (f.endsWith('index.html')) body = '<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">' + body;
    r.fulfill({ status: 200, body, contentType: types[path.extname(f)] || 'application/octet-stream' });
  });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('http://review.local/index.html#m0-rig'); await p.waitForTimeout(1500);
  await p.check('#rig-joints'); await p.waitForTimeout(300); await p.screenshot({ path: out + '/rig.png' });
  await p.click('.seg >> text=Gesture'); await p.waitForTimeout(1700); await p.screenshot({ path: out + '/gesture.png' });
  await p.goto('http://review.local/index.html#m0-voice'); await p.waitForTimeout(600); await p.screenshot({ path: out + '/voice.png' });
  await p.setViewportSize({ width: 400, height: 900 }); await p.goto('http://review.local/index.html#m0-poses'); await p.waitForTimeout(800);
  await p.screenshot({ path: out + '/phone.png' });
  console.log('phone scrollWidth', await p.evaluate(() => document.documentElement.scrollWidth));
  console.log('errors', JSON.stringify(errs)); await b.close();
})();
