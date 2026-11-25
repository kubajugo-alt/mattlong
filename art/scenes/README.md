# Scenes

All eight Prologue rooms are built: `office-day`, `office-night`, `corridor`, `pete-kate-flat`, `doyers-street`,
`tea-house`, `pawnshop`, `alley`. The corridor joins Matt's office, Pete & Kate's flat and the stairs down to the street. Each room's horizon (and how it was measured) is in its legend
(`art/rooms/labels/<room>.legend.json`) and in `art/rooms/rooms.json`; `tools/scale_check.py` drops Matt
into a room at several depths to check it.

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

## Hotspots

`hotspots.json` lists every object in the room as a clickable shape (polygons in scene
pixels), with no actions yet; `hotspots.md` is the readable list. Built by
`tools/segment_objects.py` (Gemini finds and labels every object; OpenCV GrabCut cuts
each outline, or the box is kept where it fails) and `tools/build_hotspots.py`
(furniture takes its exact shape from the label map; curation in
`art/rooms/labels/office-day.hotspots.json` drops duplicates and names things).
The smallest hotspot under the pointer wins. Night shares the day list for now.

## Solid furniture

Each solid object has a footprint on the floor plan in metres (its painted width at its
front line, back by `depth_m`); a character's feet stay `body_radius_m` (0.25 m) clear.
The desk was repainted with a solid wooden front so Matt can sit behind it.

## Ambient

The walk test adds subtle life: dust in the light, slow cloud dimming and heat shimmer
by day; neon flicker, rain shadows and a faint lamp waver by night; smoke from the
ashtray in both. All procedural, toggled by "Ambient".

## Legend options added for the other rooms

- `islands`: furniture standing out in the room (the flat's table and chairs, the tea-house stools, the street
  lamp). Matt walks round it; only its floor-plan footprint blocks him, and floor its picture hides counts as floor.
- `column_cut`: furniture set at an angle (the pawnshop and tea-house counters): per column, only floor above its
  lowest painted pixel is behind it.
- `include` / `exclude`: hand-marked boxes of floor to add or remove (fractions of the image).
- `min_feet_y`: no walking beyond this depth (the far end of Doyers Street).
- Exits can be a coloured region (a door) or a `box` at the edge of the screen (the end of a street), with an
  optional `stand` point. `to: "map"` means the city map, which is not drawn yet.

Object detection output for the new rooms is in `art/rooms/labels/<room>-seg/` (masks + objects.json); curation
in `art/rooms/labels/<room>.hotspots.json`.

## Props: seated characters

`props` in a legend places cast-style character sprites in a room (Kate at the kitchen table, the whole table set
being part of her sprite; Pete astride his desk chair). Their furniture is painted out of the room and its painted
shadows cleared; the engine draws props always, hides Matt behind them by their front line, blocks him with their
footprint and casts their shadows from the room's lights like his. Furniture standing nearer the camera than a prop's
floor contact is cut out of the prop so the painting shows in front.

## Faces: lip sync and blinking

`tools/face_crops.py` crops each talking character's head from the highest-resolution art behind its engine frame;
Gemini edits change only the mouth (Rhubarb shapes A-H) or the eyelids (half, closed); `tools/face_patches.py`
registers each edit to the base, cuts a feathered mouth ellipse / eye region and scales it to engine pixels;
`tools/install_faces.py` writes `<name>-face` sheets and a `face` entry onto the scene objects (run it after
`build_scene.py`, which rewrites scene.json). Rhubarb (`rhubarb -f json -d <script.txt> --extendedShapes GHX`)
turns each voice line into `voices/lipsync/<id>.json`; the engine shows the cue under `audio.currentTime`, blinks
every few seconds, and applies both before the breathing mesh. Faces in `art/faces/<id>/` (check.png = review sheet).
