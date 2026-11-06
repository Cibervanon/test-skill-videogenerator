# Visual audit — demos 001/002/003 against the reference corpus

This is an inspection record, not a marketing page. Everything below was looked
at frame by frame (ffmpeg stills, `remotion still`, and the renders themselves).
Where a defect was found it says so, whether it was fixed or not.

## 1. What the references actually do

The three reference films are 608×1080, 30 fps, 60–65 s, vertical, and share a
production grammar:

| Trait | Reference evidence | Demo 001 | Demo 002 |
| --- | --- | --- | --- |
| Set density | *The Ancient Jar*: stone arches, columns, carved throne, carpet border, gold dragon sculpture, dozens of props | sparse: 2 houses + bell post | sparse: houses + doorway |
| Perspective | floor tiles and colonnades converge; the camera sits at standing height | flat, no vanishing point | flat wall behind the doorway |
| Character | stick figures (thin black limbs, white head), *not* detailed humans | vector coats, static hands | vector coats, no hands |
| Light | warm key, haze, one strong pool per scene, foreground falloff | flat gradient | lamp glow only |
| Composition | foreground occluder (a sign, a column) frames the subject | none | door frame only |
| Captions | heavy white sans, black stroke, 1–3 words at a time | yes | yes |
| Acting | walk cycles, arm swings, impacts | pendulum | pendulum |

So the gap was never "more detail in the characters" — the references keep
characters simple and spend the budget on the set. The gaps that mattered were
**depth, light and acting**.

## 2. The three fixes implemented

1. **Hands, elbows, head turn** (`characters/Character.tsx`).
   Mitten hands with a thumb, three grips (`open`, `point`, `fist`), an explicit
   elbow angle per arm, and a `yaw` that slides the face over the head silhouette
   instead of rotating the skull.
2. **One-point perspective rooms** (`engine/perspective.ts`, `scenes/Doorway.tsx`).
   The interior is a room with an **inset** back wall, converging side walls,
   ceiling beams, floor boards and a rug laid in room coordinates. The first
   attempt kept the back wall the size of the door opening and the depth did not
   read at all; the inset is what fixed it (see the two stills in
   `projects/demo_003/preproduction/frames/`).
3. **Acting with beats** (`composition/Actors.tsx`).
   `reach`, `turn` and `call` follow anticipation → travel → overshoot → settle.
   `dig` rebounds after each strike. `walkIn` ramps its speed instead of starting
   at full stride.

Plus a contrast pass (`LightVeil`) in both the square and the doorway, so the
moon/lamp pools survive while the mid-tones sink.

## 3. Defects found in this pass (and what happened to them)

| Defect | Found in | Status |
| --- | --- | --- |
| Demo 003 S01: the two characters overlapped into one silhouette | first render | **fixed** — walk-in target moved to x=760 |
| Demo 003 S02: interior read as a flat lit panel | first render | **fixed** — back wall inset 296–784, walls/ceiling now visible |
| Lamp hung in front of the picture frame | still check | **fixed** — frame moved to (612, 776) |
| S05: the reaching hand landed next to the apprentice's head | still check | **fixed** — apprentice moved to x=812 |
| The shovel in S04 never touches the grave; the strike reads as leaning | stills | **not fixed** — the prop is rigid to the forearm, so the blade cannot be planted. Needs an IK hand target. |
| Sets are still far thinner than the references | all frames | **not fixed** — density is authored per scene; the doorway got the most work, the square is still two boxes and a post |
| Faces are vector circles with a moustache; the references' faces are simpler but better staged | all frames | **not fixed** — staging improved, drawing style did not |
| No foreground occluder in the square | S01/S05 | **not fixed** — the doorway has its frame, the square has nothing |

## 4. What the three films look like side by side

`projects/demo_003/preproduction/comparison_001_002_003.jpg` stacks the same
moment from each film (001 at 18 s, 002 at 12 s, 003 at 13 s).

- **001** is a flat wall of houses; the character is a silhouette against a
  gradient.
- **002** adds the warm doorway and the lamp, but the interior is a painted
  rectangle.
- **003** has the room's geometry, hands on the coat, a subtle head turn, and a
  caption that opens on the spoken word.

## 5. Honest conclusion

The three targeted gaps are closed at the level of *system*: the rig can hold and
point, the sets can have real perspective, the presets have beat structure, and
editing can follow the words. The films are still **not** at the reference level
of set density, and the character drawing style is a deliberate, simpler choice
that a viewer will read as "flat vector", not as the references' painterly
storybook. Calling this "the same look" would be false.
