// Matt Long: The Bloody Angle, Prologue. The game layer on top of the room engine (index.html):
// runs the ink script (prologue.json, inkjs), plays the voiced lines with captions and lip sync, handles
// look/use/talk, the briefcase inventory, the notebook, the evidence board, title cards and the save.
(() => {
  'use strict';
  const E = window.ENGINE;
  const $ = (id) => document.getElementById(id);
  const PFX = { 'office-day': 'office', 'office-night': 'office', corridor: 'corridor', 'pete-kate-flat': 'flat', 'doyers-street': 'doyers',
    'tea-house': 'tea', pawnshop: 'pawn', alley: 'alley' };
  // exits that the script decides (gates, door sounds, the night scene); others just walk through
  const EXIT_KNOT = { 'office-day:door': 'office__door.use', 'corridor:flat-door': 'corridor__flat_door.use', 'corridor:office-door': 'corridor__office_door.use',
    'corridor:stairs': 'corridor__street_door_below.use', 'pete-kate-flat:door': 'flat__front_door.use', 'doyers-street:apartment-door': 'doyers__apartment_door.use',
    'doyers-street:tea-house-doors': 'doyers__tea_house_doors.use', 'doyers-street:far-end': 'doyers__far_street_lamp.look', 'alley:far-end': 'doyers__far_street_lamp.look',
    'alley:back-door': 'alley__back_door.use', 'pawnshop:front-door': 'pawn__front_door.use', 'tea-house:bead-curtain': 'tea__default.use',
    'tea-house:laundry': 'tea__default.use', 'office-night:door': 'office__default.use' };
  const PEOPLE = { pete: 'pete', kate: 'kate', 'lee-wing': 'lee', sol: 'sol', junkie: 'junkie', 'inez-seated': 'inez', newsboy: 'newsboy' };
  const NAME = { VO: '', MATT: 'Matt', PETE: 'Pete', KATE: 'Kate', LEE: 'Lee Wing', SOL: 'Sol', JUNKIE: 'The kid', INEZ: 'Inéz', NEWSBOY: 'Newsboy' };
  const ITEMS = { 'eviction-notice': 'Eviction notice', flask: 'Hip flask', cigarettes: "Pete's cigarettes", 'pawn-ticket': 'Pawn ticket 4417',
    'account-book': "Lee Wing's account book", money: 'Fifty dollars', 'michael-photo': 'Photo of Michael', key: "Michael's door key" };
  const JOURNAL = {
    'lee-book': ['Rent', "Lee Wing's account book was stolen from the tea house on Tuesday night. Thirty years of who owes him what. Get it back and he might forget the rent."],
    'find-book': ['Rent', 'Lee: bring the book to his counter and the rent can wait two weeks. A thin boy in a big coat was seen running toward the Bowery.'],
    'need-ticket': ['Rent', "Sol has the book behind the wire. No ticket, no book. Whoever pawned it went out the back, into the alley."],
    'junkie-ticket': ['Rent', 'The kid in the alley has the ticket. He wants two packs of cigarettes. I have one, and it is Kate’s.'],
    'rent-two-weeks': ['Rent', "Book returned. Two weeks' grace from Lee Wing. He will remember that I am “available”."],
    'case-harlan': ['Case: Capt. Michael Harlan', 'Army Medical Corps surgeon, Governors Island. Missing nine days, since Armistice Day. Army says “on leave”; police wrote “lovers’ quarrel”. Client: Miss Inéz Venta, $50 retainer. His key: West 84th Street.'],
    'lead-apartment': ['Case: Capt. Michael Harlan', 'He never takes leave, and the Army is not worried. Somebody is lying, or has been told to. Start where he lived.'],
  };
  let story, lines = {}, paths = new Set(), busy = false, skip = null, pendingActs = [], CUES = {};
  const G = { inv: ['flask'], journal: [], notebook: false, seenFlat: false, selected: null };
  const STORY = E.STORY; STORY.hidden = new Set(['inez-seated']); STORY.hiddenHot = new Set();

  // ---------------------------------------------------------------- UI
  const hud = document.querySelector('.hud');
  for (const id of ['cap', 'dlg', 'card']) { const el = $(id); if (el) el.remove(); }
  const mk = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const cap = mk('div', 'cap'); cap.setAttribute('role', 'status'); hud.append(cap);
  const dlg = mk('div', 'dlg'); const ol = mk('ol'); dlg.append(ol); hud.append(dlg);
  const fade = mk('div', 'gfade'); hud.append(fade);
  const card = mk('div', 'card gcard'); hud.append(card);
  const using = mk('div', 'using'); using.hidden = true; hud.append(using);
  const note = mk('div', 'notebook'); note.hidden = true; hud.append(note);
  const board = mk('div', 'board'); board.hidden = true; hud.append(board);
  const menu = mk('div', 'gmenu'); menu.hidden = true; hud.append(menu);
  const replaceBtn = (id) => { const o = $(id); const n = o.cloneNode(true); o.replaceWith(n); return n; };
  const bNote = replaceBtn('bNote'), bMap = replaceBtn('bMap'), bMenu = replaceBtn('bMenu');
  bNote.hidden = true;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  function showCaption(sp, text) { cap.innerHTML = ''; if (NAME[sp]) { const b = mk('b'); b.textContent = NAME[sp]; cap.append(b); }
    const t = mk('span'); t.textContent = text; cap.append(t); cap.classList.toggle('vo', sp === 'VO'); cap.classList.add('on'); }
  const hideCaption = () => cap.classList.remove('on');

  function renderInv() {
    const inv = $('inv'); let grid = inv.querySelector('.slots');
    if (!grid) { inv.classList.add('deco'); inv.querySelectorAll('.slot').forEach(s => s.remove()); inv.append(mk('p', 'kicker', 'Matt\u2019s pockets')); grid = mk('div', 'slots'); inv.append(grid); }
    grid.innerHTML = '';
    G.inv.forEach((id, k) => {
      const b = mk('button', 'slot');
      b.setAttribute('aria-label', ITEMS[id]); b.dataset.tip = ITEMS[id]; b.setAttribute('aria-pressed', G.selected === id ? 'true' : 'false');
      const im = mk('img'); im.alt = ''; im.src = 'ui/item-' + id + '.webp'; b.append(im);
      b.addEventListener('click', () => { select(G.selected === id ? null : id); });
      b.addEventListener('contextmenu', (e) => { e.preventDefault(); run('item__' + id.replace(/-/g, '_') + '.look'); });
      grid.append(b);
    });
    for (let k = G.inv.length; k < 8; k++) grid.append(mk('span', 'slot blank'));
  }
  function select(id) { G.selected = id; renderInv(); using.hidden = !id;
    if (id) { using.innerHTML = ''; const im = mk('img'); im.src = 'ui/item-' + id + '.webp'; im.alt = ''; using.append(im, document.createTextNode('Use ' + ITEMS[id] + ' on…')); $('inv').classList.remove('open'); $('bInv').setAttribute('aria-pressed', 'false'); } }

  function renderNotebook() {
    note.innerHTML = ''; const page = mk('div', 'page deco'); page.append(mk('p', 'kicker', 'Matt Long'), mk('h2', 'ptitle', 'Notebook'), mk('div', 'rule'));
    if (!G.journal.length) page.append(mk('p', 'empty', 'Nothing written down yet.'));
    let last = null;
    for (const id of G.journal) { const [sec, txt] = JOURNAL[id] || ['', id]; if (sec !== last) { const s = mk('h3'); s.textContent = sec; page.append(s); last = sec; }
      const p = mk('p'); p.textContent = txt; page.append(p); }
    const c = mk('button', 'close', 'Close'); c.onclick = () => { note.hidden = true; }; page.append(c); note.append(page);
  }

  async function showCard(kind) {
    card.innerHTML = '';
    const box = mk('div');
    if (kind === 'prologue') box.innerHTML = '<h2>Prologue</h2><p>Rent Day</p><small>Doyers Street · Thursday, 20 November 1930</small>';
    else box.innerHTML = '<h2>To be continued</h2><p>Act 1</p><small>The Missing Captain</small>';
    const go = mk('button', 'cardbtn', kind === 'prologue' ? 'Begin' : 'Play the Prologue again'); box.append(go); card.append(box);
    card.classList.add('open');
    const t0 = performance.now();      // ignore the click that opened the card (it bubbles here)
    await new Promise(r => { go.onclick = (e) => { e.stopPropagation(); r(); }; card.onclick = kind === 'prologue' ? () => { if (performance.now() - t0 > 400) r(); } : null; });
    card.onclick = null;
    card.classList.remove('open');
    if (kind !== 'prologue') { clearSave(); location.reload(); }
  }

  async function fadeTo(fn) { fade.classList.add('on'); await sleep(350); await fn(); await sleep(120); fade.classList.remove('on'); }

  // ---------------------------------------------------------------- evidence board (P5 tutorial: one link)
  function openBoard() {
    const CARDS = [['photo', 'Capt. Michael Harlan', 'ui/item-michael-photo.webp'], ['key', 'His key, West 84th St.', 'ui/item-key.webp'],
      ['leave', 'Army: “on leave”', null], ['nine', 'Gone nine days, since Armistice Day. Never took a day’s leave.', null]];
    board.innerHTML = '<div class="bpage deco"><p class="kicker">The Harlan case</p><h2 class="ptitle">Evidence board</h2><div class="rule"></div><p class="hint">Pick the two notes that don’t add up together.</p><div class="pins"></div><button class="close">Close</button></div>';
    const pins = board.querySelector('.pins'); const sel = [];
    for (const [id, label, img] of CARDS) {
      const b = mk('button', 'pin'); if (img) { const i = mk('img'); i.src = img; i.alt = ''; b.append(i); } const t = mk('span'); t.textContent = label; b.append(t);
      b.onclick = async () => { b.classList.toggle('on'); const k = sel.indexOf(id); if (k >= 0) sel.splice(k, 1); else sel.push(id);
        if (sel.length === 2) { const ok = sel.includes('leave') && sel.includes('nine'); board.hidden = true;
          if (ok) await run('office__evidence_board_night.link_leave'); else await run('item__default.use'); } };
      pins.append(b);
    }
    board.querySelector('.close').onclick = () => { board.hidden = true; };
    board.hidden = false;
  }

  // ---------------------------------------------------------------- engine actions from the script
  async function act(cmd) {
    const [verb, ...rest] = cmd.split(':'); const arg = rest.join(':');
    switch (verb) {
      case 'give': if (!G.inv.includes(arg)) G.inv.push(arg); renderInv(); flash($('bInv')); break;
      case 'take': G.inv = G.inv.filter(i => i !== arg); if (G.selected === arg) select(null); renderInv(); break;
      case 'hide': if (arg === 'kate-at-table') STORY.kateGone = true; else { STORY.hidden.add(arg); STORY.hiddenHot.add(E.room() + ':' + arg); } break;
      case 'go': await fadeTo(() => E.enter(arg, E.room())); break;
      case 'scene': if (E.room() !== arg) await fadeTo(() => E.enter(arg, null)); break;
      case 'sfx': if (arg !== 'rain') E.shot(arg, arg === 'radio_dance_band' ? 0.5 : 0.7, [E.M.x, E.M.y]); break;   // rain: the night office's own rain bed
      case 'anim': { const [who, a] = arg.split(':');
        if (who === 'inez' && a === 'walk_in') STORY.hidden.delete('inez-seated');
        if (who === 'inez' && a === 'walk_out') STORY.hidden.add('inez-seated');
        if (who === 'kate' && a === 'stand') break;
        const occ = { kate: 'kate-at-table', junkie: 'junkie', inez: 'inez-seated' }[who]; if (occ && a !== 'walk_out') E.anim(occ); break; }
      case 'journal': if (!G.journal.includes(arg)) G.journal.push(arg); if (G.notebook) flash(bNote); break;
      case 'unlock': if (arg === 'notebook') { G.notebook = true; bNote.hidden = false; flash(bNote); } break;
      case 'card': await showCard(arg); break;
      case 'board': break;     // the board's pins are drawn by openBoard
    }
  }
  const flash = (el) => { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); };

  // ---------------------------------------------------------------- running the script
  async function speak(line) {
    const m = line.match(/^([A-Z]+):\s*(.*)$/); if (!m) return;
    const [, sp, text] = m; showCaption(sp, text);
    const id = lines[sp + '|' + text];
    const who = sp === 'VO' ? 'matt' : sp.toLowerCase();
    let done;
    const skipP = new Promise(r => { skip = r; });
    if (id) { const v = lines.__man[id];
      done = E.sayFile(who, 'voice/' + v.file, v.cues ? (CUES[id] || null) : null).then(() => sleep(250)); }
    else done = sleep(1200 + text.length * 45);
    await Promise.race([done, skipP]); skip = null; E.stopTalk();
  }
  async function pump() {
    while (true) {
      while (story.canContinue) {
        const out = story.Continue().trim();
        while (pendingActs.length) await act(pendingActs.shift());
        if (out) await speak(out);
      }
      while (pendingActs.length) await act(pendingActs.shift());
      hideCaption();
      if (!story.currentChoices.length) break;
      const i = await choose(story.currentChoices); story.ChooseChoiceIndex(i);
    }
  }
  function choose(choices) {
    return new Promise(res => { ol.innerHTML = '';
      choices.forEach((c, i) => { const li = mk('li'), b = mk('button'); b.type = 'button'; b.textContent = c.text;
        if ((c.tags || []).some(t => t.startsWith('mask:'))) { const im = mk('img', 'mask'); im.src = 'ui/icon-mask.webp'; im.alt = 'Mask choice'; im.title = 'A Mask choice: how much of himself Matt shows'; b.append(im); }
        b.onclick = (e) => { e.stopPropagation(); dlg.classList.remove('open'); res(i); }; li.append(b); ol.append(li); });
      dlg.classList.add('open'); });
  }
  async function run(path) {
    if (!path) return;
    while (busy) await sleep(80);          // wait for the scene's own lines (e.g. entering the flat) instead of dropping the click
    busy = true; document.body.classList.add('busy');
    try { story.ChoosePathString(path); await pump(); } catch (e) { console.error(path, e); }
    busy = false; document.body.classList.remove('busy'); hideCaption(); save();
  }
  const has = (p) => paths.has(p);
  function knotFor(hotId, verb) {
    const base = PFX[E.room()] + '__' + hotId.replace(/-/g, '_');
    if (E.room() === 'office-night' && hotId === 'evidence-board' && story.variablesState.case_taken) return verb === 'look' ? 'office__evidence_board_night.look' : 'BOARD';
    if (verb === 'look') return has(base + '.look') ? base + '.look' : PFX[E.room()] + '__default.look';
    if (G.selected) { const it = G.selected.replace(/-/g, '_'); return has(base + '.' + it) ? base + '.' + it : 'item__default.use'; }
    if (has(base + '.talk')) return base + '.talk';
    if (has(base + '.use')) return base + '.use';
    return PFX[E.room()] + '__default.use';
  }

  // ---------------------------------------------------------------- input
  // Click a hotspot: the eye (look) and the hand (use / talk) open beside it and the player picks one.
  // Clicking anywhere else walks there (or through an exit). With an item from the briefcase in hand,
  // a click uses it on the hotspot straight away.
  const cv = $('c');
  const verbs = document.createElement('div'); verbs.className = 'verbs'; verbs.hidden = true;
  verbs.innerHTML = '<button type="button" data-v="look" aria-label="Look"><img alt="" src="ui/verb-eye.webp"></button>'
    + '<button type="button" data-v="use" aria-label="Use"><img alt="" src="ui/verb-hand.webp"></button>';
  document.querySelector('.hud').append(verbs);
  let pick = null;                        // {h, x, y} the hotspot the verbs are open for, and the click point
  function closeVerbs() { verbs.hidden = true; pick = null; }
  function openVerbs(h, x, y, ev) {
    const st = document.querySelector('.stage').getBoundingClientRect(), sz = E.scene().sc.size;
    const fx = ev ? (ev.clientX - st.left) / st.width : x / sz[0], fy = ev ? (ev.clientY - st.top) / st.height : y / sz[1];
    verbs.style.left = Math.min(94, Math.max(6, fx * 100)) + '%'; verbs.style.top = (fy * 100) + '%';
    verbs.classList.toggle('below', fy < 0.2);     // near the top edge, open below the pointer
    verbs.querySelector('[data-v=use]').setAttribute('aria-label', PEOPLE[h.id] ? 'Talk to ' + h.name : 'Use ' + h.name);
    verbs.querySelector('[data-v=look]').setAttribute('aria-label', 'Look at ' + h.name);
    pick = { h, x, y }; verbs.hidden = false;
  }
  function goDo(h, path) {
    const tx = (h.bbox[0] + h.bbox[2]) / 2, ty = Math.min(h.bbox[3] + 30, E.scene().sc.size[1] - 10);
    E.walkTo(tx, ty, () => { if (path === 'BOARD') openBoard(); else run(path); });
  }
  verbs.addEventListener('click', (ev) => {
    const b = ev.target.closest('button'); if (!b || !pick) return;
    ev.stopPropagation();
    const { h, x, y } = pick; closeVerbs();
    if (b.dataset.v === 'look') { run(knotFor(h.id, 'look')); return; }
    const path = knotFor(h.id, 'use');
    const scripted = !/__default\.use$/.test(path) && path !== 'item__default.use';
    if (!scripted && E.exitAt(x, y)) { E.plainWalk(x, y); return; }      // a door with nothing to say: just go through
    goDo(h, path);
  });
  E.hooks.click = (x, y, ev) => {
    if (busy) { if (skip) skip(); return true; }
    note.hidden = true;
    if (!verbs.hidden) { closeVerbs(); return true; }          // a click away from the verbs just closes them
    const h = E.hotAt(x, y);
    if (h && G.selected) { goDo(h, knotFor(h.id, 'use')); return true; }
    if (h) { openVerbs(h, x, y, ev); return true; }
    if (G.selected) select(null);
    return false;
  };
  cv.addEventListener('contextmenu', (ev) => ev.preventDefault());
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && !verbs.hidden) closeVerbs(); });
  E.hooks.exit = (room, exn) => {
    const k = EXIT_KNOT[room + ':' + exn]; if (!k) return false;
    run(k); return true;
  };
  E.hooks.entered = (room) => {
    if (room === 'pete-kate-flat' && !G.seenFlat && story) { G.seenFlat = true; setTimeout(() => run('flat_enter'), 0); }
  };
  cap.addEventListener('click', () => skip && skip());
  bNote.addEventListener('click', () => { renderNotebook(); note.hidden = !note.hidden; });
  bMap.addEventListener('click', () => run('doyers__far_street_lamp.look'));
  bMenu.addEventListener('click', () => {
    menu.innerHTML = '<div class="mpage deco"><p class="kicker">Matt Long · The Bloody Angle</p><h2 class="ptitle">Paused</h2><button data-a="resume">Resume</button><label><input type="checkbox" id="gSound"> Sound</label><button data-a="restart">Start the Prologue again</button><p>The game saves itself as you play.</p></div>';
    const snd = menu.querySelector('#gSound'); snd.checked = $('sound').checked; snd.onchange = () => { $('sound').checked = snd.checked; $('sound').dispatchEvent(new Event('change')); };
    menu.querySelector('[data-a=resume]').onclick = () => { menu.hidden = true; };
    menu.querySelector('[data-a=restart]').onclick = () => { clearSave(); location.reload(); };
    menu.hidden = false;
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { select(null); note.hidden = true; board.hidden = true; menu.hidden = true; }
    if ((e.key === ' ' || e.key === 'Enter') && busy && skip && !dlg.classList.contains('open')) { e.preventDefault(); skip(); } });

  // ---------------------------------------------------------------- save
  const KEY = 'mattlong-prologue-save-v1';
  function save() { try { localStorage.setItem(KEY, JSON.stringify({ ink: story.state.ToJson(), G: { ...G, selected: null }, room: E.room(),
    kateGone: STORY.kateGone, hidden: [...STORY.hidden], hiddenHot: [...STORY.hiddenHot] })); } catch (e) {} }
  function loadSave() { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
  function clearSave() { try { localStorage.removeItem(KEY); } catch (e) {} }

  // ---------------------------------------------------------------- boot: title screen, then the story
  E.hooks.boot = async () => {
    const [js, man, ps, cues] = await Promise.all([fetch('prologue.json').then(r => r.text()), fetch('voice/lines.json').then(r => r.json()), fetch('paths.json').then(r => r.json()), fetch('voice/cues.json').then(r => r.json())]);
    CUES = cues;
    story = new inkjs.Story(js); story.BindExternalFunction('act', (c) => { pendingActs.push(c); }, false);
    lines = { __man: man }; for (const [id, v] of Object.entries(man)) lines[v.speaker + '|' + v.text] = id;
    paths = new Set(ps);
    // only hotspots the script has lines for are live; every other mapped hotspot stays in the data, switched off
    const liveIds = new Set(ps.filter(q => q.includes('__') && q.includes('.')).map(q => q.split('.')[0]).filter(k => !/__default$/.test(k)));
    E.STORY.live = (room, id) => liveIds.has(PFX[room] + '__' + id.replace(/-/g, '_'));
    const saved = loadSave();
    await E.enter(saved ? saved.room : 'office-day');
    // title
    card.innerHTML = ''; const box = mk('div');
    box.innerHTML = '<h2>Matt Long</h2><p>The Bloody Angle</p><small>Prologue · Rent Day</small>';
    const bNew = mk('button', 'cardbtn', saved ? 'Start again' : 'Begin'); box.append(bNew);
    let bCont = null; if (saved) { bCont = mk('button', 'cardbtn', 'Continue'); box.append(bCont); }
    const tip = mk('small', 'how', 'Click something to look at it or use it · click anywhere else to walk · the fedora opens the briefcase'); box.append(tip);
    card.append(box); card.classList.add('open', 'title');
    const choice = await new Promise(r => { bNew.onclick = (e) => { e.stopPropagation(); r('new'); }; if (bCont) bCont.onclick = (e) => { e.stopPropagation(); r('cont'); }; });
    card.classList.remove('open', 'title');
    window.dispatchEvent(new Event('pointerdown'));      // wake the audio
    if (choice === 'cont') {
      story.state.LoadJson(saved.ink); Object.assign(G, saved.G); STORY.kateGone = saved.kateGone; STORY.hidden = new Set(saved.hidden); STORY.hiddenHot = new Set(saved.hiddenHot);
      bNote.hidden = !G.notebook; renderInv();
    } else {
      clearSave(); if (E.room() !== 'office-day') await E.enter('office-day'); renderInv(); run('prologue_start');
    }
  };
  renderInv();
  window.GAME = { get story() { return story; }, G, run, knotFor, get busy() { return busy; } };     // for tests and debugging
})();
