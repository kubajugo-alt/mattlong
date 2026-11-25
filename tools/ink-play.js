// Play the Prologue critical path through the compiled story and print every line and engine action: node tools/ink-play.js (run next to prologue.json)
const { Story } = require('inkjs'); const fs = require('fs');
const s = new Story(fs.readFileSync('prologue.json', 'utf8')); const acts = []; s.BindExternalFunction('act', (c) => { acts.push(c); console.log('    [act ' + c + ']'); }, false);
let lines = 0;
function run(path, picks = []) {
  s.ChoosePathString(path); console.log(`\n### ${path}`);
  while (true) {
    while (s.canContinue) { const l = s.Continue().trim(); if (l) { lines++; console.log('  ' + l + (s.currentTags.length ? '   #' + s.currentTags.join(' #') : '')); } }
    if (!s.currentChoices.length) break;
    const want = picks.shift(); const i = want === undefined ? s.currentChoices.length - 1 : s.currentChoices.findIndex(c => c.text.startsWith(want));
    if (i < 0) { console.log('  !! no choice', want, s.currentChoices.map(c => c.text)); break; }
    console.log('  >> ' + s.currentChoices[i].text + (s.currentChoices[i].tags?.length ? '  #' + s.currentChoices[i].tags.join(' #') : '')); s.ChooseChoiceIndex(i);
  }
}
run('prologue_start'); run('office__door.use'); run('office__eviction_notice.use'); run('office__door.use');
run('corridor__street_door_below.use'); run('flat_enter');
run('flat__pete.talk', ['Anything', 'Spare', 'See you']);
run('flat__kate.talk', ['About Pete', 'It\'s for', 'Think of it']);
run('flat__pete.talk', ['A place', 'See you']);
run('corridor__street_door_below.use');
run('tea__lee_wing.talk', ['And the rent']);
run('pawn__sol.talk', ["You've got", 'Who pawned', 'Lee Wing won', 'Just']);
run('alley__junkie.talk', ['You pawned', 'Forget']); run('alley__junkie.cigarettes', ['Lee Wing knows']);
run('pawn__sol.pawn_ticket'); run('tea__lee_wing.account_book', ['Say you']);
run('corridor__office_door.use', ['Who is', 'How long', 'What does', 'And the police', 'Why me', 'Maybe', "I'll find"]);
run('office__evidence_board_night.link_leave');
console.log('\nvars:', ['read_notice','heard_book','has_cigs','kate_gone','met_lee','has_ticket','has_book','book_returned','case_taken','mask'].map(v => v + '=' + s.variablesState[v]).join(' '), '| spoken lines:', lines);
