# Matt — cut-out rig source

- `source/master.png`: strict side profile on chroma green (Gemini, `gemini-3-pro-image`).
- `source/noarm.png`: Gemini edit of the master with the near arm removed.
- `source/oneleg.png`: Gemini edit of the master with the far leg removed.
- `source/*.json`: the prompt, model and references for each image.
- `joints.json`: joint positions in image pixels and cut settings.

Rebuild the pieces:

    python3 tools/build_rig.py art/characters/matt/source art/characters/matt/joints.json <out dir>

The far arm and far leg are darker copies of the near ones. Pieces keep their
position from the master, so the rest pose reproduces it exactly.
