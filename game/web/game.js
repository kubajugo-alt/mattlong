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
  const PEOPLE = { pete: 'pete', kate: 'kate', 'lee-wing': 'lee', sol: 'sol', junkie: 'junkie', 'inez-seated': 'inez', newsboy: 'newsboy', 'tea-women': 'women' };
  const NAME = { VO: '', MATT: 'Matt', PETE: 'Pete', KATE: 'Kate', LEE: 'Lee Wing', SOL: 'Sol', JUNKIE: 'The kid', INEZ: 'Inéz', NEWSBOY: 'Newsboy', OPERATOR: 'Operator', MEI: 'Mei', LAN: 'Lan' };
  const ITEMS = { 'eviction-notice': 'Eviction notice', flask: 'Hip flask', cigarettes: "Pete's cigarettes", 'pawn-ticket': 'Pawn ticket 4417',
    'account-book': "Lee Wing's account book", money: 'Fifty dollars', 'coffee-cup': "Kate's spare cup", change: 'Loose change', clarion: 'The Evening Clarion', 'michael-photo': 'Photo of Michael', key: "Michael's door key" };
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
  const G = { inv: ['flask', 'change'], journal: [], notebook: true, seenFlat: false, selected: null };
  const STORY = E.STORY; STORY.talking = () => busy;
  // the time of day the scenes are lit for, from where the story has got to
  STORY.phase = () => { if (!story) return 'morning'; const v = story.variablesState;
    return v.book_returned ? 'dusk' : v.met_lee ? 'afternoon' : v.kate_gone ? 'noon' : 'morning'; }; STORY.hidden = new Set(['inez-seated']); STORY.hiddenHot = new Set();

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
  bNote.hidden = false;      // the notebook is on screen from the start; entries arrive as the story gives them
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
      case 'give': if (!G.inv.includes(arg)) G.inv.push(arg); renderInv(); flash($('bInv'));
        if (E.act && G.lastHot && !E.acting()) E.act('reach', G.lastHot[0]); break;       // he takes it: a reach toward where it came from
      case 'take': G.inv = G.inv.filter(i => i !== arg); if (G.selected === arg) select(null); renderInv(); break;
      case 'hide': if (arg === 'kate-at-table') STORY.kateGone = true; else { STORY.hidden.add(arg); STORY.hiddenHot.add(E.room() + ':' + arg); } break;
      case 'go': await fadeTo(() => E.enter(arg, E.room())); break;
      case 'scene': if (E.room() !== arg) await fadeTo(() => E.enter(arg, null)); break;
      case 'radio': E.radio(arg === 'on'); break;
      case 'pigeons': E.pigeonsFly(); break;
      case 'sfx': if (arg !== 'rain') E.shot(arg, arg === 'radio_dance_band' ? 0.5 : 0.7, [E.M.x, E.M.y]); break;   // rain: the night office's own rain bed
      case 'anim': { const [who, a] = arg.split(':');
        if (who === 'inez') { await inez(a); break; }
        if (who === 'matt') { if (E.act) E.act(a, G.lastHot ? G.lastHot[0] : null); break; }    // his actions run alongside the lines
        const occ = { kate: 'kate-at-table', junkie: 'junkie', inez: 'inez-seated', sol: 'sol', lee: 'lee-wing', newsboy: 'newsboy' }[who];
        if (who === 'kate' && a === 'stand') { await kateLeaves(occ); break; }          // she gets up and goes; the empty table follows
        if (who === 'sol' && a === 'book') { await E.anim(occ, a); break; }      // he holds it out (and holds it, `hold`) while Matt takes it
        if (occ && a !== 'walk_out') E.anim(occ, a); break; }
      case 'journal': if (!G.journal.includes(arg)) G.journal.push(arg); if (G.notebook) flash(bNote); break;
      case 'unlock': if (arg === 'notebook') { G.notebook = true; bNote.hidden = false; flash(bNote); } break;
      case 'card': await showCard(arg); break;
      case 'board': break;     // the board's pins are drawn by openBoard
    }
  }
  // Kate: gets up from the table (the sheet, up to her first step), then walks along the front of the table and away
  // to the door as an actor; Matt steps aside if he's on her way
  async function kateLeaves(occ) {
    const sc = E.scene().sc, A = sc.actors && sc.actors.kate;
    if (!A) { await E.anim(occ, 'leave'); return; }
    const near = (p, q) => { const dx = q[0] - p[0], dy = q[1] - p[1], t = Math.max(0, Math.min(1, ((E.M.x - p[0]) * dx + (E.M.y - p[1]) * dy) / (dx * dx + dy * dy)));
      return Math.hypot(E.M.x - p[0] - t * dx, E.M.y - p[1] - t * dy) < 170; };
    if (near(A.start, A.turn) || near(A.turn, A.door)) E.walkTo(A.clear[0], A.clear[1], () => E.face(A.turn[0]));
    await E.anim(occ, 'leave');
    // her last stand-up frame dissolves into the first steps of the walk on the same spot, and the walk starts from a
    // standstill, so the turn from three-quarter to profile reads as a turn, not a cut
    if (E.ghost) E.ghost(occ, A.blend || 0.5);
    const walk = E.actorWalk('kate', 'side', A.start, A.turn, null, A.secs_side, { fadeIn: A.blend || 0.5, ease: 0.14 });   // starts this frame (sheet loaded with the room)
    STORY.kateGone = true;
    await walk;
    if (E.door) E.door('door', true, 0.8);                                         // she opens the door as she reaches it,
    const through = (E.doorInside && E.doorInside('door')) || A.door;              // walks through it, and pulls it shut behind her:
    await E.actorWalk('kate', 'back', A.turn, through, E.door ? null : 'out', A.secs_back, { stay: true });   // the leaf hides her
    if (E.door) { E.door('door', false, 0.9, 0.15); await sleep(1100); } if (E.actorClear) E.actorClear('kate');
  }
  // Inez: in from the door to the sofa (walk, then sits), and back out; the lines run while she walks. Without the
  // sheets (an older build) she just appears and goes.
  let inezWalk = null;
  async function inez(a) {
    const sc = E.scene().sc, A = sc.actors && sc.actors.inez;
    if (!A) { if (a === 'walk_in') STORY.hidden.delete('inez-seated'); if (a === 'walk_out') STORY.hidden.add('inez-seated'); return; }
    if (a === 'walk_in') {
      if (Math.hypot(E.M.x - A.door[0], E.M.y - A.door[1]) < 500 || Math.hypot(E.M.x - A.stand[0], E.M.y - A.stand[1]) < 300) E.walkTo(A.clear[0], A.clear[1], () => E.face(A.stand[0]));   // out of her way
      // in at the door, across to the sofa and straight down onto it, while Matt looks her over
      if (E.door) { E.door('door', true, 0.5); setTimeout(() => E.door('door', false, 0.9), 1700); }   // the door opens, she comes in, it swings to
      // she starts once the door is mostly open
      const behind = (E.doorInside && E.doorInside('door')) || A.door;           // she's behind the door when it opens
      inezWalk = sleep(E.door ? 300 : 0).then(() => E.actorWalk('inez', 'front', behind, A.stand, E.door ? null : 'in', A.secs_in)).then(() => { STORY.hidden.delete('inez-seated'); return E.anim('inez-seated', 'sit'); });
    }
    if (a === 'sit') { if (inezWalk) await inezWalk; inezWalk = null; }
    if (a === 'stand') await E.anim('inez-seated', 'sit', true);
    if (a === 'walk_out') { STORY.hidden.add('inez-seated'); if (E.door) E.door('door', true, 0.7, 1.2);
      const through = (E.doorInside && E.doorInside('door')) || A.door;
      await E.actorWalk('inez', 'back', A.stand, through, E.door ? null : 'out', A.secs_out, { stay: true });
      if (E.door) { E.door('door', false, 0.9, 0.15); await sleep(1100); } if (E.actorClear) E.actorClear('inez'); }
  }
  const flash = (el) => { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); };

  // ---------------------------------------------------------------- running the script
  // the built site packs the voice lines into a few files (voice/pack-*.mp3, offsets in lines.json): a line is
  // fetched as a byte range; where the host ignores ranges, the pack is fetched once and sliced
  const packs = {};
  async function voiceSrc(v) {
    if (!v.pack) return 'voice/' + v.file;
    try {
      if (!packs[v.pack]) {
        const r = await fetch('voice/' + v.pack, { headers: { Range: 'bytes=' + v.off + '-' + (v.off + v.len - 1) } });
        if (r.status === 206) return URL.createObjectURL(new Blob([await r.arrayBuffer()], { type: 'audio/mpeg' }));
        packs[v.pack] = r.arrayBuffer();
      }
      const buf = await packs[v.pack];
      return URL.createObjectURL(new Blob([buf.slice(v.off, v.off + v.len)], { type: 'audio/mpeg' }));
    } catch (e) { return 'voice/' + v.file; }
  }
  async function speak(line) {
    const m = line.match(/^([A-Z]+):\s*(.*)$/); if (!m) return;
    const [, sp, text] = m; showCaption(sp, text);
    const id = lines[sp + '|' + text];
    const who = sp === 'VO' ? 'matt' : sp.toLowerCase();
    let done;
    const skipP = new Promise(r => { skip = r; });
    if (id) { const v = lines.__man[id];
      done = voiceSrc(v).then(src => E.sayFile(who, src, v.cues ? (CUES[id] || null) : null)).then(() => sleep(250)); }
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
    // people get the mouth (talk) instead of the hand: touching them is rare, talking is the point
    const ub = verbs.querySelector('[data-v=use]'); ub.setAttribute('aria-label', PEOPLE[h.id] ? 'Talk to ' + h.name : 'Use ' + h.name);
    ub.querySelector('img').src = PEOPLE[h.id] ? 'ui/verb-mouth.webp' : 'ui/verb-hand.webp';
    verbs.querySelector('[data-v=look]').setAttribute('aria-label', 'Look at ' + h.name);
    pick = { h, x, y }; verbs.hidden = false;
  }
  // Talking to someone, Matt stands beside them, turned to face them, never in front of them: try spots left and
  // right at their depth, keep the one where his figure covers the least of theirs, then the nearest to him.
  function talkSpot(h) {
    const sz = E.scene().sc.size, cx = (h.bbox[0] + h.bbox[2]) / 2, feet = Math.min(h.bbox[3], sz[1] - 10);
    const area = (h.bbox[2] - h.bbox[0]) * (h.bbox[3] - h.bbox[1]); let best = null;
    for (const side of [-1, 1]) for (const k of [0.55, 0.8, 1.1, 1.5, 2]) for (const dy of [-30, 0, 40, 120, 220, 320]) {   // deeper rows: people behind counters
      const H0 = E.figureH(feet + dy), want = side < 0 ? h.bbox[0] - k * 0.32 * H0 : h.bbox[2] + k * 0.32 * H0;
      const t = E.nearestWalkable(want, feet + dy); if (!t) continue;
      const H = E.figureH(t[1]), half = 0.17 * H;                   // his figure: about a third as wide as he is tall
      let cover = 0;
      if (t[1] > feet - 15) {                                      // in front of them: he could hide them
        const ox = Math.max(0, Math.min(t[0] + half, h.bbox[2]) - Math.max(t[0] - half, h.bbox[0]));
        const oy = Math.max(0, Math.min(t[1], h.bbox[3]) - Math.max(t[1] - H, h.bbox[1]));
        cover = ox * oy / area;
      }
      const off = Math.abs(t[0] - want) + Math.abs(t[1] - (feet + dy));     // pushed far from where we asked: a wall, a counter
      const score = cover * 10 + off / 400 + Math.max(0, dy) / 2500 + Math.hypot(t[0] - E.M.x, t[1] - E.M.y) / 4000 + Math.abs(t[0] - cx) / 3000;
      if (!best || score < best.score) best = { t, score };
    }
    return best ? best.t : [cx, Math.min(h.bbox[3] + 30, sz[1] - 10)];
  }
  function goDo(h, path) {
    if (PEOPLE[h.id]) {
      noticed.add(E.room() + ':' + h.id);          // he came to talk: no separate greeting
      const [x, y] = talkSpot(h), cx = (h.bbox[0] + h.bbox[2]) / 2; G.lastHot = [cx, y];
      E.walkTo(x, y, () => { E.face(cx); run(path); });
      return;
    }
    const tx = (h.bbox[0] + h.bbox[2]) / 2, ty = Math.min(h.bbox[3] + 30, E.scene().sc.size[1] - 10); G.lastHot = [tx, ty];
    E.walkTo(tx, ty, () => { if (path === 'BOARD') openBoard(); else run(path); });
  }
  verbs.addEventListener('click', (ev) => {
    const b = ev.target.closest('button'); if (!b || !pick) return;
    ev.stopPropagation();
    const { h, x, y } = pick; closeVerbs();
    if (h.id === 'matt') { G.lastHot = null; run(b.dataset.v === 'look' ? 'matt_self.look' : 'matt_self.use'); return; }     // his watch, his pockets
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
    lastInput = performance.now();
    if (mattAt(x, y)) {                                         // Matt himself: his watch and pockets, or an item on himself
      if (G.selected) { const it = G.selected.replace(/-/g, '_'); run(has('matt_self.' + it) ? 'matt_self.' + it : 'item__default.use'); select(null); return true; }
      const H = E.figureH(E.M.y); openVerbs({ id: 'matt', name: 'Matt', bbox: [E.M.x - H * 0.2, E.M.y - H, E.M.x + H * 0.2, E.M.y] }, x, y, ev); return true;
    }
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
  // Matt is clickable: his figure, a third as wide as he is tall
  function mattAt(x, y) { const H = E.figureH(E.M.y); return H > 0 && Math.abs(x - E.M.x) < H * 0.17 && y < E.M.y && y > E.M.y - H * 0.97; }
  // people notice him: the first time he comes near someone in a visit, they say so (knot <room>__<who>.notice)
  let noticed = new Set(), lastInput = performance.now();
  setInterval(() => {
    if (!story || busy || !verbs.hidden || E.busyRoom()) return;
    const sc = E.scene(); if (!sc) return; const room = E.room(), H = E.figureH(E.M.y);
    for (const h of sc.hot) {
      if (!PEOPLE[h.id] || noticed.has(room + ':' + h.id) || (h.id === 'kate' && STORY.kateGone)) continue;
      const knot = PFX[room] + '__' + h.id.replace(/-/g, '_') + '.notice'; if (!has(knot)) continue;
      const cx = (h.bbox[0] + h.bbox[2]) / 2, dx = Math.max(0, Math.abs(E.M.x - cx) - (h.bbox[2] - h.bbox[0]) / 2), dy = Math.abs(E.M.y - h.bbox[3]);
      if (dx < H * 0.45 && dy < H * 0.5) { noticed.add(room + ':' + h.id); run(knot); return; }
    }
    // left standing a while, Matt thinks out loud
    if (performance.now() - lastInput > 45000 && !E.M.moving) { lastInput = performance.now(); run('matt_idle'); }
  }, 300);
  cv.addEventListener('pointerdown', () => { lastInput = performance.now(); });
  E.hooks.entered = (room) => {
    noticed = new Set([...noticed].filter(k => !k.startsWith(room + ':')));      // a new visit: they can notice him again
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
    kateGone: STORY.kateGone, hidden: [...STORY.hidden], hiddenHot: [...STORY.hiddenHot], radio: E.radioState() })); } catch (e) {} }
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
      story.state.LoadJson(saved.ink); Object.assign(G, saved.G); STORY.kateGone = saved.kateGone; STORY.hidden = new Set(saved.hidden); STORY.hiddenHot = new Set(saved.hiddenHot); if (saved.radio) E.radioSet(saved.radio);
      G.notebook = true; bNote.hidden = false; renderInv();
    } else {
      clearSave(); if (E.room() !== 'office-day') await E.enter('office-day'); renderInv(); run('prologue_start');
    }
  };
  renderInv();
  window.GAME = { get story() { return story; }, G, run, knotFor, get busy() { return busy; } };     // for tests and debugging
})();
