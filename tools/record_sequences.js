// Records scripted sequences from the built game, one frame per 1/12 s on a frozen clock, for the frame boards.
// node tools/record_sequences.js <out dir>     (serves nothing itself: run a server on site-artifact/ at :8765)
// Each sequence replays what game.js does for that moment, through the same ENGINE calls.
const { chromium } = require('playwright'); const fs = require('fs');
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true }); const ONLY = process.argv[3];
const SEQ = [
  { key: 'kate', label: 'Kate wychodzi', room: 'pete-kate-flat', from: 'corridor', matt: [560, 1420], clip: { x: 240, y: 110, width: 680, height: 600 },
    run: `window.__ph='kate'; await GAME.kateLeaves(); ENGINE.STORY.kateGone=true; window.__ph='door'; await new Promise(r=>setTimeout(r,800)); window.__ph='gone';` },
  { key: 'inez-in', label: 'Inez wchodzi i siada', room: 'office-night', from: 'corridor', matt: [1480, 1330], clip: { x: 130, y: 90, width: 620, height: 620 },
    run: `ENGINE.STORY.hidden.add('inez-seated'); window.__ph='walkin'; await GAME.inez('walk_in'); await GAME.inez('sit'); window.__ph='seated'; await new Promise(r=>setTimeout(r,600)); window.__ph='gone';` },
  { key: 'inez-out', label: 'Inez wstaje i wychodzi', room: 'office-night', from: 'corridor', matt: [1480, 1330], clip: { x: 130, y: 90, width: 620, height: 620 },
    run: `ENGINE.STORY.hidden.delete('inez-seated'); window.__ph='seated'; await new Promise(r=>setTimeout(r,500));
      window.__ph='stand'; await GAME.inez('stand'); window.__ph='walkout'; await GAME.inez('walk_out'); window.__ph='gone';` },
  { key: 'matt-in', label: 'Matt wchodzi do mieszkania', room: 'corridor', from: 'doyers-street', matt: [900, 1350], clip: { x: 520, y: 60, width: 700, height: 640 },
    run: `window.__ph='enter'; await ENGINE.enter('pete-kate-flat','corridor'); window.__ph='door'; await new Promise(r=>setTimeout(r,1800)); window.__ph='gone';` },
];
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] }); const all = [];
  const prev = ONLY && fs.existsSync(OUT + '/seqs.json') ? JSON.parse(fs.readFileSync(OUT + '/seqs.json')) : [];
  for (const q of SEQ) { if (ONLY && q.key !== ONLY) { const o = prev.find(x => x.key === q.key); if (o) all.push(o); continue; }
    const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
    await p.addInitScript(() => { const rn = performance.now.bind(performance), rr = window.requestAnimationFrame.bind(window); let virt = false, vt = 0, qq = [];
      const st = window.setTimeout.bind(window); window.__realST = st;
      performance.now = () => virt ? vt : rn(); window.requestAnimationFrame = (cb) => { if (virt) { qq.push(cb); return 0; } return rr((t) => cb(virt ? vt : t)); };
      window.setTimeout = (f, ms, ...a) => virt ? (window.__timers.push({ at: vt + (ms || 0), f, a }), 0) : st(f, ms, ...a); window.__timers = [];
      window.__virt = () => { vt = rn(); virt = true; };
      window.__adv = (ms) => { vt += ms; const c = qq; qq = []; c.forEach(f => f(vt)); const due = window.__timers.filter(t => t.at <= vt); window.__timers = window.__timers.filter(t => t.at > vt); due.forEach(t => t.f(...t.a)); }; });
    await p.goto('http://localhost:8765/');
    await p.waitForSelector('.gcard.open .cardbtn'); await p.click('.gcard.open .cardbtn'); await p.waitForSelector('.gcard.open .cardbtn'); await p.click('.gcard.open .cardbtn'); await p.waitForTimeout(800);
    const S = async () => { for (let i = 0; i < 80; i++) { if (!await p.evaluate(() => GAME.busy)) return; await p.evaluate(() => ENGINE.hooks.click(0, 0)); await p.waitForTimeout(200); } }; await S();
    await p.evaluate(([r, f]) => ENGINE.enter(r, f), [q.room, q.from]); await p.waitForTimeout(3500); await S();
    await p.evaluate(([x, y]) => { ENGINE.M.x = x; ENGINE.M.y = y; ENGINE.M.dir = 'front'; }, q.matt); await p.waitForTimeout(1500);
    await p.evaluate((code) => { window.__virt(); for (let i = 0; i < 3; i++) window.__adv(16); (new Function('return (async()=>{' + code + '})()'))(); }, q.run);
    const frames = []; let gone = 0;
    for (let k = 0; k < 260 && gone < 6; k++) {
      await p.evaluate(() => window.__adv(1000 / 12)); await p.evaluate(() => new Promise(r => window.__realST(r, 0)));
      const ph = await p.evaluate(() => window.__ph); const f = q.key + '-' + String(k).padStart(3, '0') + '.jpg';
      await p.screenshot({ path: OUT + '/' + f, type: 'jpeg', quality: 72, clip: q.clip }); frames.push({ f, ph }); if (ph === 'gone') gone++;
    }
    all.push({ key: q.key, label: q.label, frames }); console.log(q.key, frames.length, frames.map(x => x.ph[0]).join('')); await p.close();
  }
  fs.writeFileSync(OUT + '/seqs.json', JSON.stringify(all)); await b.close();
})();
