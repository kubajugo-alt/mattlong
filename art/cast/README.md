# Cast designs

24 static character designs (12 main, Michael's wounded variant, 11 minor), for
sprite animation in Ludo.ai later.

- `cast.json`: the shared style block, the shared proportion rule, and each
  character's description, height and hat flag. Descriptions follow the bible.
- `style-anchor-matt.png`: Matt on chroma green; every other figure was
  generated with this image attached, so style, light, pose and framing match.
- `final/<id>.png`: transparent cut-outs, strict greyscale (only Inéz's lips are red).
- `lineup-main.jpg`, `lineup-minor.jpg`: everyone at real relative heights.
- `lineup-eyelevel.jpg`: everyone scaled to the same eye height, the proportion check.
- `source-meta/`: prompt, model and references for each generated image.

Pipeline (Gemini `gemini-3-pro-image` via `tools/gen-image.mjs`):

    # 1. generate each <id>.png into a work dir with --ref style-anchor-matt.png
    #    and prompt = style + proportions + " Character: " + look
    python3 tools/finish_cast.py <work dir> art/cast            # cut out, greyscale, lineups
    python3 tools/eyeline_cast.py art/cast <pose model> art/cast/lineup-eyelevel.jpg

Proportions: about 7.5 heads tall, the same head-to-body ratio and leg length
as Matt; heavier or older builds are shown by width, posture and clothes only.
The proportion check found Natalia, Corrigan, Sol, Hartley and Stefan with
heads too large and Inéz, Kate and Zofia with heads too small; all were
regenerated with the rule.

## Bathhouse and shower variants

Matt, Pete and Julian each have a bath-towel version and a white 1930s
boxer-shorts version (group `bathhouse`), generated with the style anchor plus
the man's own design as a second reference so face, body and body hair carry
over. Bodies are ordinary 1930s builds with natural, untrimmed body hair.

Shower versions (group `shower`) are non-explicit: front three-quarter view with
both hands covering the groin. Matt's and Julian's exist. Pete's front view and
all three back views were refused by Google's image model; see `blocked` in
`cast.json`. They were not retried. No full-frontal versions are made.
