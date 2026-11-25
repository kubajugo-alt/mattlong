# Scenes

Engine data for each room, built by `tools/build_scene.py` from the painting
(`art/rooms/final/`) and an aligned flat-colour object map (`art/rooms/labels/`),
with a legend giving the horizon, object colours, exits, exclusions and lights.

- `bg.png`: the painting.
- `occ/<object>.png`: each piece of furniture cut out; drawn over a character when
  the object's `baseline` (where it stands on the floor) is below the character's feet.
- `walk.png`: walkable floor (1/4 scale). Floor behind a piece of furniture's front
  line, hand-marked exclusions and the bottom strip are removed.
- `floor.png`: all visible floor (1/4 scale); shadows are clipped to it.
- `scene.json`: size, horizon, scale rule, objects, exits and lights.

Depth: a character h metres tall with feet at y is `(y - horizon*H) * h / 1.6` px.
The office horizon was measured on the door leaf (2.1 m), not the frame with its
transom window, and checked against the ceiling line.

Lights: `window` lights cast a parallel shadow in `dir` (day: sun through the right
window, falling left and slightly forward); `point` lights (night: the desk lamp)
cast a shadow away from the lamp's point on the floor, longer with distance, fading
with `reach`. No blob shadow under the feet: each walk frame is anchored at its own
planted foot so the cast shadow starts at the sole.

`demo/office-walk/` is the clickable test (published privately as "Office Walk Test").
