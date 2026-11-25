# Matt Long: The Bloody Angle — Build Plan (Prologue)

Source of truth for story: *Doyers Street — Game Bible* (25 Nov 2026), plus the
decisions below. First milestone: the **Prologue, "Rent Day" (P1–P5)**, fully
playable on desktop and mobile, with final-quality art, voices and music.

## 1. Decisions (locked 25 Nov 2026)

| Topic | Decision |
|---|---|
| Title | *Matt Long: The Bloody Angle* (series name + case title) |
| Platform | Browser game, TypeScript, own point-and-click engine, data-driven scenes; deploy to Netlify |
| Repo | `kubajugo-alt/mattlong` |
| Art | All AI-generated in **Canva**; characters as **cut-out rigs** animated in code |
| Colour | Greyscale + red for exactly two things: Inéz's lipstick and the Serenol label |
| Voice | Full cast with ElevenLabs from the first build |
| Music | Public-domain period jazz + ambience |
| Devices | Desktop and mobile (touch) as equals |
| Script | Written by Claude in English, reviewed by Kuba |
| Queer content | Period-coded in public scenes, open in private ones |
| Bag gap (3.3 → 4.2) | Brancato's men watch the pawnshop after Pete's story; walking in would hand them the notebook |
| Evidence board | 2–3 deductions per act, designed by Claude and added to the bible |
| Greatcoat | Lee Wing lends it from an uncollected laundry order for a small favour, Act 1 hub |
| Bank scene 3.4 | 11 Dec 1930, closure day, Lower East Side branch, crowds at locked doors |
| Open | Romance for Matt (decide before Act 3); Natalia/Stefan (decide before Act 2) |

## 2. Prologue scope

**Screens (8 backgrounds):** Matt's office (morning), Matt's office (night, rain),
Pete & Kate's flat, Doyers Street (hub), Lee Wing's tea house, Bowery pawnshop,
alley behind the pawnshop, city map (Prologue shows only Doyers St ↔ Bowery).

**Characters (7, all voiced):** Matt (full rig: walk, idle, talk, reach, pick up,
use), Pete, Kate, Sol Abramowitz, the alley junkie, Lee Wing, Inéz (lighter rigs:
idle, talk, gesture; Inéz also walks in at P5).

**Scene flow and the system each one teaches:**

| # | Scene | Teaches | Gate |
|---|---|---|---|
| P1 | Office, morning: eviction notice, Natalia's photo face-down | Look / right-click (long-press) voice-over, walking, hotspot highlight | Read the notice → leave |
| P2 | Pete & Kate's flat: coffee, hangover, Kate scolds | Dialogue tree; first small Mask line; the "Pete knows and doesn't care" beat | Get Pete's cigarettes |
| P3 | Pawnshop + alley: Lee Wing's stolen account book | Inventory, give/use, map travel | Trade cigarettes to junkie → pawn ticket → book |
| P4 | Tea house: book returned | Rent extension; first journal entry | — |
| P5 | Office, night: Inéz walks in out of the rain | Notebook (journal) unlocks; evidence board tutorial (one link) | Case accepted → "To be continued: Act 1" card |

Target play time: 20–30 minutes.

## 3. Technical architecture

- **Stack:** Vite + TypeScript, no UI framework. Canvas 2D for the scene, DOM
  overlay for text/UI (crisp type, screen readers, easy layout on phones).
- **Logical resolution** 1920×1080, scaled and letterboxed; landscape on phones
  with a "rotate your phone" screen in portrait.
- **Dialogue:** [Ink](https://github.com/inkle/ink) via `inkjs`. Branching, variables
  (Mask score, flags) and per-line tags (`#speaker:pete #vo:p2_014`) that drive
  portraits and voice files. Compiled at build time.
- **Scene data:** one file per screen: background layers, walkable polygon
  (navmesh + A* pathfinding), depth scaling, hotspots (polygon, verbs, ink knot),
  exits, actors, ambient sound, light source.
- **Game state:** flags, inventory, journal, board, Mask score, current scene —
  one serialisable object. Auto-save per scene + 3 manual slots in localStorage.
- **Rendering:** parallax layers, cut-out rig animator (bone hierarchy, keyframed
  poses, mouth flaps synced to voice amplitude), post-FX pass: film grain, gate
  weave, vignette, optional projector filter. Red accent drawn as a separate
  masked layer so the rest of every image stays strictly grey.
- **Input:** one smart cursor/tap. Desktop: left = act, right = voice-over, Tab =
  show hotspots. Touch: tap = act, long-press = voice-over, on-screen buttons for
  hotspots, inventory and journal; 44 px minimum targets.
- **Audio:** Web Audio with three buses (voice, music, ambience/SFX), ducking
  under voice, subtitles always on by default, text speed setting.
- **Repo layout:**
  ```
  src/engine/   renderer, rig, nav, input, audio, save, ink bridge
  src/ui/       inventory (fedora pop-up), journal, evidence board, map, menus
  game/scenes/  scene data          game/ink/  dialogue scripts
  assets/       art/, voice/, music/, sfx/  (+ SOURCES.md for every asset)
  tools/        asset processing (greyscale, rig slicing, loudness), checks
  docs/         bible updates, style guide, voice casting sheet
  ```

## 4. Asset pipelines

**Art (Canva).**
1. Style guide first: one master prompt (1930 NYC, film-noir lighting, painted,
   one dominant light source, 8–12 greys) and 2–3 approved reference images used
   as `imageReferences` on every later generation for consistency.
2. Backgrounds generated at 16:9, then `tools/` converts to strict greyscale,
   levels and adds a depth/foreground split where needed.
3. Characters: a turnaround sheet per character (approved by you), then each body
   part generated or cut separately, background removed in Canva, assembled into
   a rig file. Silhouette rules from the bible (fedora, fur collar, etc.).
4. Every image logged in `assets/SOURCES.md` (prompt, Canva link, date).

**Voices (ElevenLabs).** Casting sheet with one designed voice per character
(light period accents, never caricature) for your approval before any lines are
generated. Lines generated from the ink script tags, so a changed line only
regenerates that file. I'll quote the credit cost and confirm before each batch.

**Music and ambience.** US sound recordings from 1925 and earlier are public
domain as of 2026, which is period-correct for a 1930 setting. Sources: Library
of Congress National Jukebox, Internet Archive 78rpm collections, Musopen;
ambience from CC0 libraries (Freesound CC0 only). Each file logged with its
licence in `SOURCES.md`.

## 5. Milestones (one draft PR each)

| # | Milestone | Done when |
|---|---|---|
| M0 | **Pipeline spikes** | Canva images reach the repo as files; 3 Matt test poses look like one man; one rigged arm animates; one ElevenLabs line lands as a file; one PD jazz track sourced with licence |
| M1 | **Engine skeleton** | P1 playable with grey placeholder art: walk, hotspots, voice-over, scene exit, desktop + touch input |
| M2 | **Core systems** | Ink dialogue, inventory + combine, journal, map, saves, settings, hotspot highlight; whole Prologue playable with placeholders |
| M3 | **Script** (runs alongside M1–M2) | Full Prologue dialogue in ink, reviewed and approved by you |
| M4 | **Art** | Style guide approved; 8 backgrounds, 7 rigs, post-FX, red accent |
| M5 | **Audio** | Voice casting approved; all lines voiced and lip-synced; music + ambience |
| M6 | **Polish and ship** | Automated playthrough passes; checked on desktop Chrome/Safari/Firefox and an iPhone/Android viewport; deployed to Netlify |

**Testing:** Vitest for engine logic (nav, inventory, saves, state); an ink check
that every knot is reachable and every line has a speaker and voice file; a
Playwright test that plays the Prologue start to finish on desktop and a phone
viewport. GitHub Actions runs all of it on every PR.

## 6. Risks

| Risk | Mitigation |
|---|---|
| AI characters drift between images | Turnaround sheets + references on every call; cut-out rigs need only one approved image set per character |
| Getting Canva/ElevenLabs output into the repo as files | Proven in M0 before anything depends on it |
| Voice lines regenerated as the script changes (credits) | Script approved (M3) before the full voice batch; per-line regeneration only |
| Mobile performance with grain/post-FX | Post-FX quality setting; tested on a phone viewport each milestone |
| Writing that spoils the reveal ladder | Script reviewed against the bible's "no facts before their rung" rule |

## 7. Needed from Kuba

- Approve this plan (or change it).
- Later: approve the art style guide (M4) and the voice casting sheet (M5),
  review the Prologue script (M3).
- For deploy (M6): a Netlify site linked to this repo (I can set it up through
  the connected Netlify account with your OK).
