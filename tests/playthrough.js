// Plays the whole Prologue in a headless browser through the game's own input hooks.
// node tests/playthrough.js [url]   (default: http://localhost:8765/ serving site/)
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://localhost:8765/';
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const log = (...a) => console.log(...a);
  await p.goto(URL); await p.waitForSelector('.gcard.open .cardbtn', { timeout: 30000 });
  await p.click('.gcard.open .cardbtn');                              // title: Begin
  await p.waitForSelector('.gcard.open .cardbtn', { timeout: 15000 }); await p.click('.gcard.open .cardbtn');   // Prologue card
  const state = () => p.evaluate(() => ({ room: ENGINE.room(), busy: document.body.classList.contains('busy'), moving: ENGINE.M.moving || ENGINE.M.path.length > 0 || ENGINE.busyRoom(),
    choices: [...document.querySelectorAll('.dlg.open li button')].map(x => x.textContent), cap: document.querySelector('.cap.on')?.textContent || '',
    inv: [...document.querySelectorAll('#inv .slot')].map(x => x.getAttribute('aria-label')), card: !!document.querySelector('.gcard.open') }));
  // wait until the game is idle, skipping lines and answering choices from `picks` (prefix match)
  async function settle(picks = []) {
    for (let n = 0; n < 600; n++) {
      await p.waitForTimeout(120); const s = await state();
      if (s.card) return s;
      if (s.choices.length) { const want = picks.shift(); const i = want ? s.choices.findIndex(c => c.startsWith(want)) : -1;
        if (i < 0) throw new Error('no choice ' + want + ' in ' + JSON.stringify(s.choices));
        log('    > ' + s.choices[i]); await p.click(`.dlg.open li:nth-child(${i + 1}) button`); continue; }
      if (s.busy) { await p.evaluate(() => ENGINE.hooks.click(0, 0)); continue; }       // skip the line
      if (!s.moving) { await p.waitForTimeout(300); const s2 = await state(); if (!s2.busy && !s2.moving && !s2.choices.length) return s2; }
    }
    throw new Error('did not settle');
  }
  async function hot(id, picks) {
    // click a point where this hotspot is the one under the pointer (smaller things in front of it win elsewhere)
    const ok = await p.evaluate((id) => { const h = ENGINE.scene().hot.find(h => h.id === id); if (!h) return false;
      for (let k = 0; k < 400; k++) { const x = h.bbox[0] + (h.bbox[2] - h.bbox[0]) * ((k * 0.618) % 1), y = h.bbox[1] + (h.bbox[3] - h.bbox[1]) * ((k * 0.382 + 0.5) % 1);
        const u = ENGINE.hotAt(x, y); if (u && u.id === id) { ENGINE.hooks.click(x, y); return true; } } return false; }, id);
    if (!ok) throw new Error('no hotspot ' + id);
    if (await p.isVisible('.verbs')) await p.click('.verbs [data-v=use]');      // the verbs: take the hand
    const s = await settle(picks); log(' ', id, '->', s.room, '| inv:', s.inv.join(', ')); return s;
  }
  async function exit(name, picks) {
    await p.evaluate((name) => { if (!ENGINE.hooks.exit(ENGINE.room(), name)) { const e = ENGINE.scene().sc.exits[name]; ENGINE.enter(e.to, ENGINE.room()); } }, name);
    await p.waitForTimeout(1500); const s = await settle(picks); log('  exit', name, '->', s.room); return s;
  }
  async function useItem(item, id, picks) { await p.click('#bInv'); await p.waitForTimeout(500);
    await p.click(`#inv .slot[aria-label="${item}"]`); return hot(id, picks); }
  const expect = (cond, msg) => { if (!cond) throw new Error('EXPECT ' + msg); };
  let s;
  log('P1'); await settle();
  s = await exit('door'); expect(s.room === 'office-day', 'door is locked until the notice is read');
  s = await hot('eviction-notice'); expect(s.inv.includes('Eviction notice'), 'notice in inventory');
  s = await exit('door'); expect(s.room === 'corridor', 'out to the corridor');
  s = await exit('stairs'); expect(s.room === 'corridor', 'stairs wait for Pete');
  log('P2'); s = await exit('flat-door'); expect(s.room === 'pete-kate-flat', 'in the flat');
  await hot('pete', ['Anything', 'Spare', 'See you']); log('    heard_book', await p.evaluate(() => GAME.story.variablesState.heard_book));
  s = await hot('kate', ['About', "It's for", 'Think of it']); expect(s.inv.includes("Pete's cigarettes"), 'got the cigarettes');
  log('    kate_gone', await p.evaluate(() => GAME.story.variablesState.kate_gone), errs);
  await hot('pete', ['A place', 'See you']);
  s = await exit('door'); s = await exit('stairs'); expect(s.room === 'doyers-street', 'on Doyers Street');
  log('P3'); s = await exit('tea-house-doors'); expect(s.room === 'tea-house', 'in the tea house');
  await hot('lee-wing', ['And the rent']);
  s = await exit('street'); s = await exit('pawnshop-door'); expect(s.room === 'pawnshop', 'in the pawnshop');
  await hot('sol', ["You've got", 'Who', 'Just']);
  s = await hot('back-door'); expect(s.room === 'pawnshop', 'Sol keeps him out of the back room');
  s = await exit('front-door'); s = await exit('passage'); expect(s.room === 'alley', 'round to the alley by the passage');
  await hot('junkie', ['You pawned', 'Forget']);
  s = await useItem("Pete's cigarettes", 'junkie', ['Lee Wing knows']); expect(s.inv.includes('Pawn ticket 4417'), 'got the ticket');
  s = await exit('back-door'); expect(s.room === 'pawnshop', 'back in the pawnshop');
  s = await useItem('Pawn ticket 4417', 'sol'); expect(s.inv.includes("Lee Wing's account book"), 'got the book');
  log('P4'); s = await exit('front-door'); s = await exit('tea-house-doors');
  s = await useItem("Lee Wing's account book", 'lee-wing', ['Say you']); expect(!s.inv.includes("Lee Wing's account book"), 'book returned');
  log('P5'); s = await exit('street'); s = await exit('apartment-door'); expect(s.room === 'corridor', 'home');
  s = await exit('office-door', ['Who', 'How long', 'What does', 'And the police', 'Why me', 'Maybe', "I'll find"]);
  expect(s.room === 'office-night', 'night in the office'); expect(s.inv.includes('Fifty dollars') && s.inv.includes('Photo of Michael') && s.inv.includes("Michael's door key"), 'Inez gave money, photo, key');
  expect(await p.isVisible('#bNote'), 'notebook unlocked');
  await p.click('#bNote'); await p.waitForTimeout(300); await p.screenshot({ path: (process.env.SHOTS || require('os').tmpdir()) + '/notebook.png' }); await p.click('.notebook .close');
  await p.evaluate(() => { const h = ENGINE.scene().hot.find(h => h.id === 'evidence-board');
    for (let k = 0; k < 400; k++) { const x = h.bbox[0] + (h.bbox[2] - h.bbox[0]) * ((k * 0.618) % 1), y = h.bbox[1] + (h.bbox[3] - h.bbox[1]) * ((k * 0.382 + 0.5) % 1);
      const u = ENGINE.hotAt(x, y); if (u && u.id === 'evidence-board') { ENGINE.hooks.click(x, y); return; } } });
  await p.click('.verbs [data-v=use]');
  await p.waitForSelector('.board:not([hidden]) .pin', { timeout: 15000 }); await p.screenshot({ path: (process.env.SHOTS || require('os').tmpdir()) + '/board.png' });
  await p.click('.board .pin:nth-child(3)'); await p.click('.board .pin:nth-child(4)');
  s = await settle(); expect(s.card, 'To be continued card');
  await p.screenshot({ path: (process.env.SHOTS || require('os').tmpdir()) + '/end.png' });
  log('END: reached the Act 1 card. errors:', errs.length ? errs : 'none');
  await b.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
