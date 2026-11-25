// Compile an ink script with inkjs and report errors: node tools/ink-check.js <in.ink> <out.json>  (needs: npm i inkjs@2.2.3)
const { Compiler } = require('inkjs/compiler/Compiler');
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const errs = [];
const c = new Compiler(src, { errorHandler: (m, t) => errs.push(m) });
let story; try { story = c.Compile(); } catch (e) { console.log('THROW', e.message); }
console.log(errs.length ? errs.join('\n') : 'compiled OK, no errors/warnings');
if (story) {
  const json = story.ToJson(); fs.writeFileSync(process.argv[3], json);
  // play the opening
  const { Story } = require('inkjs');
  const s = new Story(json); while (s.canContinue) { const l = s.Continue(); console.log('>', l.trim(), s.currentTags.join(' ')); }
}
