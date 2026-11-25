const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2], out = process.argv[3];
const types = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.mp3': 'audio/mpeg' };
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 2 });
  await ctx.route('http://review.local/**', (r) => {
    const u = new URL(r.request().url()); const f = path.join(root, decodeURIComponent(u.pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    let body = fs.readFileSync(f);
    if (f.endsWith('index.html')) body = '<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">' + body;
    r.fulfill({ status: 200, body, contentType: types[path.extname(f)] || 'application/octet-stream' });
  });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://review.local/index.html#m0-rig-v2'); await p.waitForTimeout(1200);
  const canvas = p.locator('canvas');
  await p.click('.seg >> text=Rest'); await p.waitForTimeout(300); await canvas.screenshot({ path: out + '/r_rest.png' });
  await p.click('.seg >> text=Walk');
  for (let i = 0; i < 4; i++) { await p.waitForTimeout(420); await canvas.screenshot({ path: out + '/r_walk' + i + '.png' }); }
  await p.click('.seg >> text=Gesture'); await p.waitForTimeout(2600); await canvas.screenshot({ path: out + '/r_gesture.png' });
  await p.check('#rig-joints'); await p.click('.seg >> text=Exploded'); await p.waitForTimeout(2000); await canvas.screenshot({ path: out + '/r_exploded.png' });
  console.log('errors', JSON.stringify(errs)); await b.close();
})();
