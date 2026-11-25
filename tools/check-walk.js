// Walk check: samples Matt's walk for 2.3 s and reports whether the body ever moves backwards,
// how far a planted foot slides, and whether feet sink below or float above the floor.
//   node tools/check-walk.js review
// Expect backwardsSteps 0, maxSlidePx under ~6 (heel-to-toe roll), sink and float 0.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2];
const ok = (r) => r.backwardsSteps === 0 && +r.maxSlidePx < 6 && +r.maxSinkPx < 0.5 && +r.maxFloatPx < 0.5;
const types = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png' };
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl'] });
  const ctx = await b.newContext({ viewport: { width: 600, height: 600 } });
  await ctx.route('http://review.local/**', (r) => {
    const u = new URL(r.request().url()); const f = path.join(root, decodeURIComponent(u.pathname));
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: '' });
    let body = fs.readFileSync(f); if (f.endsWith('index.html')) body = '<!doctype html><meta charset=utf-8>' + body;
    r.fulfill({ status: 200, body, contentType: types[path.extname(f)] || 'application/octet-stream' });
  });
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://review.local/index.html#m0-rig-v2'); await p.waitForTimeout(2000);
  const res = await p.evaluate(() => {
    const { pose, boneMatrices, mesh, apply } = window.__rigDebug, ix = mesh.boneIndex, J = mesh.joints;
    const rows = []; let prevHx = null, back = 0, maxSlide = 0, maxSink = 0, maxFloat = 0;
    const planted = { '': null, 'Back': null };
    for (let i = 0; i <= 230; i++) {
      const tt = i * 0.01, P = pose('Walk', tt); P.headRel = 0;
      const W = boneMatrices(P), ry = P.hy - J.hip[1];
      if (prevHx !== null && P.hx < prevHx - 1e-6) back++;
      prevHx = P.hx;
      for (const s of ['', 'Back']) {
        const heel = apply(W[ix['foot' + s]], mesh.contacts.heel), ball = apply(W[ix['foot' + s]], mesh.contacts.ball);
        const hw = [heel[0] + P.hx, heel[1] + ry], bw = [ball[0] + P.hx, ball[1] + ry];
        const low = Math.max(hw[1], bw[1]);
        maxSink = Math.max(maxSink, low - mesh.floorY);
        // a foot on the floor (within 2 px) should not move sideways between samples
        const onFloor = Math.abs(low - mesh.floorY) < 2;
        const key = hw[1] >= bw[1] ? hw[0] : bw[0];
        if (onFloor && planted[s] && planted[s].on && Math.abs(planted[s].pt - (hw[1] >= bw[1] ? 'h' : 'b').length) === 0) {}
        if (onFloor && planted[s] && planted[s].on) {
          const prev = hw[1] >= bw[1] ? planted[s].h : planted[s].b, now = hw[1] >= bw[1] ? hw[0] : bw[0];
          if (planted[s].which === (hw[1] >= bw[1] ? 'h' : 'b')) maxSlide = Math.max(maxSlide, Math.abs(now - prev));
        }
        planted[s] = { on: onFloor, h: hw[0], b: bw[0], which: hw[1] >= bw[1] ? 'h' : 'b' };
      }
      // the lowest point of both feet should be on the floor (no floating)
      const lows = ['', 'Back'].map(s => { const W2 = W; const h = apply(W2[ix['foot' + s]], mesh.contacts.heel)[1] + ry, b2 = apply(W2[ix['foot' + s]], mesh.contacts.ball)[1] + ry, t2 = apply(W2[ix['toe' + s]], mesh.contacts.toe)[1] + ry; return Math.max(h, b2, t2); });
      maxFloat = Math.max(maxFloat, mesh.floorY - Math.max(...lows));
      if (i % 23 === 0) rows.push({ t: tt.toFixed(2), hx: Math.round(P.hx), hy: Math.round(P.hy), lowestAboveFloor: Math.round(mesh.floorY - Math.max(...lows)), kneeFlex: Math.round(P.shin * 57.3), kneeFlexBack: Math.round(P.shinBack * 57.3) });
    }
    return { rows, backwardsSteps: back, maxSlidePx: maxSlide.toFixed(2), maxSinkPx: maxSink.toFixed(2), maxFloatPx: maxFloat.toFixed(2) };
  });
  console.table(res.rows); console.log({ backwardsSteps: res.backwardsSteps, maxSlidePx: res.maxSlidePx, maxSinkBelowFloorPx: res.maxSinkPx, maxFloatAboveFloorPx: res.maxFloatPx, errors: errs });
  if (!ok(res)) { console.error('WALK CHECK FAILED'); process.exitCode = 1; } else console.log('walk check passed');
  await b.close();
})();
