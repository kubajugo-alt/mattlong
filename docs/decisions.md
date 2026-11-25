# Decisions and bible changes

Changes to the *Doyers Street — Game Bible* (25 Nov 2026). Where this file and
the bible disagree, this file wins.

## Production decisions (25 Nov 2026)

- **Title:** *Matt Long: The Bloody Angle*. "Matt Long" is the series name;
  "The Bloody Angle" is this case.
- **Platform:** browser game in TypeScript, own engine, deployed to Netlify.
- **Art:** all AI-generated with the Gemini image API (Canva dropped in M0: it only returns thumbnails); characters are cut-out rigs animated in code.
- **Colour:** greyscale plus red for two things only: Inéz's lipstick and the
  Serenol label. (Resolves the bible's accent-colour question.)
- **Voice:** full cast voiced with ElevenLabs from the first build.
  - Leads cast 25 Nov 2026 (`voices/cast.json`): Matt = Robert, Pete = Jordan, Kate = Quin, Inéz = Monica.
- **Music:** public-domain period jazz (US recordings from 1925 or earlier) and
  CC0 ambience.
- **Devices:** desktop and mobile touch, both first-class.
- **Script:** written by Claude in English from the bible; reviewed by Kuba.
- **Queer content:** period-coded in public scenes, open in private ones (Pete,
  Natalia, Julian). (Resolves the bible's explicitness question.)
- **First milestone:** the Prologue (P1–P5).

- **Interface (25 Nov 2026, replaces the bible's fedora pop-up):** inventory is the inside
  of Matt's open briefcase, sliding up from the bottom edge, items in its felt-lined
  compartments (2 rows of 6); the
  notebook is its own button (journal), not an inventory item. Dialogue choices are
  plain subtitle-style lines low on the screen over a soft shadow, the scene stays
  visible; Mask choices carry a small half-mask icon. UI type is Jost (Futura-like).
  Hotspot highlight is white, not coloured (red stays reserved for the two accents).
  All interface art is painted by Gemini: `art/ui/` (prompts in `art/ui/raw/*.json`).

## Story fixes

1. **Why the bag waits until 4.2.** After Pete's story runs (3.5), Brancato's men
   stake out Sol's pawnshop. Matt has Michael's signed letter from 3.3, but
   walking in would hand them the notebook. Matt sees the watchers on his way
   there after 3.3; this sets up the 4.2 Christmas Eve heist.
2. **Evidence board.** 2–3 deductions per act, gating leads or dialogue. Claude
   designs them and adds them here per act. Prologue: one tutorial link in P5.
3. **The Army greatcoat (1.4).** On an Act 1 hub visit, Lee Wing lends Matt a
   greatcoat from an uncollected laundry order in return for a small favour.
4. **Bank scene (3.4).** Set on 11 Dec 1930, the day the Bank of United States
   closed, at a Lower East Side branch: crowds outside locked doors. (The run
   itself began on 10 Dec at the Bronx branch on Southern Boulevard.)

## Still open

- Romance for Matt (e.g. a spark with Julian): decide before writing Act 3.
- Does Natalia stay engaged to Stefan: decide before writing Act 2.
