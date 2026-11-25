# Review desk

The page where Kuba reviews work in progress: art, animation (live cut-out
rigs), voices and music, each with a verdict (Approve / Changes / Reject) and
notes.

- Published (private): https://claude.ai/artifact/Sbs5UsA855DLjP1jwZu56i
- `samples.json` lists milestones and samples; files live under `samples/<milestone>/`.
- Sample kinds: `image` (`src`, optional `full`), `audio` (`tracks`, optional `line`
  and `credit`), `rig` (a rig JSON: parts with file, parent, `at`, `pivot`, `z`,
  optional `rest` axis, `scale`, `shade`).
- Verdicts are stored in the artifact's database, collection `reviews`, one
  document per sample id: `{status, note, title, milestone, updatedAt}`.
  Claude reads them before each round of work.
- To add samples: add files and entries, then republish the page with every
  new file in `files`.
- `tools/review-screenshot.js <review dir> <out dir>` takes desktop and phone
  screenshots for a quick check before publishing.
