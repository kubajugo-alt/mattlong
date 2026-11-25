# Matt — cut-out rig source

All images are Gemini (`gemini-3-pro-image`) on chroma green; each has a `.json`
with its prompt, model and references.

- `source/master.png`: strict side profile. Sets the frame every piece is placed in.
- `source/noarm.png`: edit of the master with the near arm removed (torso with shoulder socket).
- `source/oneleg.png`: edit of the master with the far leg removed.
- `source/torso_only.png`: edit of `noarm.png` with the legs removed, so the jacket keeps its natural hem.
- `source/arm_free.png`: the near arm drawn alone (crisp outline); fitted back into place.
- `source/fararm_free.png`: the far arm drawn alone from its inner side (palm and thumb toward us), same frame as `arm_free.png`.
- `source/leg_free.png`: the near leg drawn alone from hip to sole, including the part hidden by the jacket.
- `joints.json`: joint positions in master pixels, the collar cut line for the head, and cut settings.

Rebuild:

    python3 tools/register_part.py art/characters/matt/source art/characters/matt/joints.json arm
    python3 tools/register_part.py art/characters/matt/source art/characters/matt/joints.json leg
    python3 tools/build_rig.py art/characters/matt/source art/characters/matt/joints.json <out dir>
    python3 tools/build_mesh.py <out dir> art/characters/matt/joints.json

The register step writes `arm.png`, `fararm.png` and `leg.png` (the free drawings
fitted into the master frame). The head is cut along the top edge of the collar
and holds only hat, face and neck skin, with a short skin-only neck that tucks
under the collar. The far leg is a darker copy of the near leg.

Joint blending: elbows and knees get a soft-edged patch cut from the rest-pose
drawing, drawn over both pieces and turned halfway between them (`follow` in
the rig file); the overlapping ends of the forearm and shin fade in. Settings
live under `blend` in `joints.json` (defaults in `tools/build_rig.py`).

Skinned mesh (`build_mesh.py`, default renderer): head, torso, whole arm and
whole leg each get a triangle grid; vertices are weighted to bones so limbs bend
smoothly, shoulders and hips stretch with the torso, and the jacket skirt is
pulled by the thighs and carries a spring "jiggle" factor for follow-through.
Settings live under `mesh` in `joints.json` (grid size, blend widths, skirt
pull, jiggle). The rigid pieces and joint patches remain as the fallback renderer.

Proportions: joints follow standard adult proportions (Drillis & Contini),
as fractions of stature from the floor: shoulder (humeral head centre) 0.79,
elbow 0.63, wrist 0.485, hip 0.53, knee 0.285, ankle 0.05 in shoes. Matt
measures 7.3 heads (crown 174, chin 480, soles 2413 in master pixels; the
crown is under the hat, so it is placed from the eye line). The neck pivot is
mid-neck. `joints.json` records these measurements under `proportions`.

Skeleton (mesh renderer): pelvis (root, at the hip) -> chest (bends at the
waist, carries head and arms); legs thigh -> shin -> foot (ankle) -> toe (ball of
the foot). `foot` in `joints.json` holds the ball joint and the heel, ball and
toe contact points; `footNeutral` in `mesh.json` levels the drawn shoe, which
stands slightly on its toes.

Motion (review player, `review/index.html`): the body moves forward at a
steady pace and footprints are placed on the floor ahead of time; each foot
lands on the heel, rolls flat, lifts the heel and pushes off the toes, then
swings in an arc to the next footprint. Legs are solved hip-to-ankle with
two-bone IK, so planted feet cannot slide; the hip is lowered only when a leg
could not otherwise reach. (An earlier version drove the legs from recorded
gait angles and derived the body position from the lowest foot; with our limb
lengths that made the body jerk backwards at every step.) Two-bone IK also
drives reaching; `node tools/check-walk.js review` checks for sliding,
floating and backward motion; head stabilised
against pelvis and chest with spring lag; cloth springs on the jacket skirt and
trouser hems respond to acceleration; poses blend over 0.45 s when switching.

Walk tuning: the gait parameters live in one object `G` in the player
(stride, heel placement, push-off angle, swing lift, bob, lean, gaze, arm
swing) and are matched against Muybridge's plate 1 (`reference/muybridge-plate1`).
Rotations are clockwise-positive on screen and Matt faces right, so a forward
lean or a raised limb is negative and looking down is positive.
