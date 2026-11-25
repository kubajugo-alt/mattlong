# M0 — Pipeline tests (25 Nov 2026)

**Verdict: all three pipelines work.** Art moves from Canva to the Gemini image
API.

| Pipeline | Result | Notes |
|---|---|---|
| Gemini image → file | **Works** | `tools/gen-image.mjs` calls `gemini-3-pro-image` and saves full-size PNGs (1696×2528 at 2:3, "2K") in about 20 s each, with a `.json` sidecar (prompt, model, refs). Key read from `GEMINI_API_KEY`, never stored in the repo. |
| Matt consistency | **Works** | Reference plus 3 poses generated with the reference attached: same face, hat, suit and tie in all of them. See `m0/matt_sheet.jpg`. The first reference added an overcoat and hid the hands; later prompts said "no overcoat, hands visible" and complied. The walk came out three-quarter instead of side-on; the prompt needs to insist. |
| Cut-out rig | **Works, needs a better parts prompt** | One call produced a parts sheet (`m0/matt_parts.jpg`). Pieces were separated automatically and an arm swung from the shoulder with an elbow bend (`m0/arm_strip.png`, script `tools/rig_test.py`). Head and armless torso with shoulder socket came out perfectly. Problems: arm and leg pieces mixed whole limbs and halves; the mid-grey background keyed badly against grey cloth (light fringes, see-through patches). |
| ElevenLabs voice → file | **Works** | `creative_generate_speech` returns signed MP3 URLs (44.1 kHz mono, 128 kbps) that download directly. Cost: ~83 credits per take for a 13-word line on `eleven_v4`; 2 takes per call by default. Test voice for Matt: "Obsidian" (gritty American, middle-aged). |
| Public-domain jazz → file | **Works** | Internet Archive's George Blood 78rpm collection downloads directly (MP3 and FLAC). Test track: King Oliver's Jazz Band, "Tears" (recorded 1923). Check every track's original recording year, not the reissue date. |
| Canva image → file | **Dropped** | The connector returns only a 133×200 thumbnail; full size needs a second credit-spending step, which hit "Credit quota cooldown". |

## Fixes carried into M4 (art)

- Generate character parts on a **pure green (#00FF00) background**, key it out,
  then convert to greyscale. Grey-on-grey keying is unreliable.
- One parts sheet per limb group (arms, legs) with an explicit piece count and
  overlapping rounded joints, and a skeleton overlay checked by script.
- Insist on "strict side profile" for walk-cycle sources.
