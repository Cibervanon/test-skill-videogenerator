# VISUAL STYLE GUIDE — AI CINEMATIC STUDIO

Derived from the reference corpus in `Ejemplos/` (3 vertical shorts + 20 frame
sheets), measured with `scripts/analyze_reference.py`. Every claim below is
marked **[measured]**, **[observed]** (seen in frames) or **[interpretation]**.

---

## 1. What the reference actually is

**[measured]** Container: 608×1080, 30 fps, AV1 video + AAC 44.1 kHz stereo,
60.6–65.2 s per short, mean level −16.8 dBFS, peak −2.2 dBFS.

**[measured]** Editing: the scene detector finds only 0–1 hard cuts per minute and
8.3–11.0 soft changes/min, with a mean detected segment of 8.2–10.1 s and a
longest take of 20.5–30.9 s. Because the frame sheets show many more setups than
the detector finds, the transitions must be largely gradual (dissolves and
camera-carried changes) rather than hard cuts. It is **not** a fast-cut format.

**[observed]** Look: 2D painted/vector illustration. Characters are simple
pill-shaped cut-outs with dot eyes, a small line mouth and a soft nose; strong
ink outline; flat local colour with a lighter rim. Sets are dense, painterly and
layered, with a visible paper/brush texture. Light is motivated: warm practicals
against cold ambient. Frames carry heavy vignetting and film grain.

**[observed]** Captions: lowercase, 2–3 words, centred low-third, white with a
dark outline, changing in sync with narration.

**[interpretation]** The perceived quality comes from *art direction density*
(background detail, colour scripting, light pools) far more than from character
complexity. That is the reproducible part, and it is what the LOCAL engine targets.

---

## 2. Non-negotiable rules

1. **Silhouette first.** Every character reads as a shape at 15% frame height.
2. **Two-value light.** Each scene has one warm and one cool source; never a
   flat fill that kills the split.
3. **No empty plate.** Backgrounds carry three depth planes minimum:
   far (sky/ridge), mid (architecture/props), near (foreground occluder).
4. **One idea per shot.** A shot changes one thing: distance, subject, or light.
5. **Motion is continuous.** Characters breathe and blink even when "still";
   a frozen frame is a defect, not a style.
6. **Captions are part of the design**, not an overlay afterthought.
7. **Negative space is composed**, never leftover.

---

## 3. Characters

| Property | Rule |
|---|---|
| Body | pear/oval, height ≈ 2.4× head diameter, no visible neck joint |
| Head | circle, radius ≈ 0.42× shoulder width |
| Eyes | two ink dots at ~±0.34 R, slightly above centre; blink every 3–4 s |
| Nose | small ellipse outline, below eye line |
| Mouth | one short curve; opens only for speech |
| Outline | constant ink weight (~4 units at R=46); one rim highlight on the key side |
| Palette | one dominant coat colour + one dark trim + cream skin |
| Wardrobe | a *state* of the identity, never a new identity |
| Performance | idle = breath + blink + micro head tilt; walk = 2-frame leg swing + arm counter-swing |

**Proportion lock.** In the engine, `scale` maps 1:1 to frame height
(`height=1` ⇒ 310 px in a 1920-tall frame). Never scale a character by eye per
shot; change the shot's framing instead.

---

## 4. Environments

- **Depth planes:** far (sky + silhouettes) → mid (the set) → near (foreground
  occluder: snow bank, door frame, out-of-focus branch).
- **Palette per scene** (measured dominant clusters):
  - night town: `#101733` `#3b3f74` `#c9d3e8` + warm windows `#ffb765`
  - interior/threshold: `#2a1b25` `#4a2b34` `#ffcf8a` + cold night `#131a36`
  - dawn field: `#3f4a78` `#f2a573` `#fdf0e2` + soil `#7a553f`
- **Light:** practical sources are visible or implied (window, lamp, low sun).
  Add pools and halation, never a uniform ambient wash.
- **Texture:** film grain over the whole frame (opacity ≈ 0.14) + vignette
  (0.5–0.6). The grain must *move* between frames.

---

## 4b. Materials (added in v0.2.0)

A flat fill is what makes a vector set look like a diagram. Rules:

1. **Every surface declares a material** — stone, plank, shingle, snow, carpet,
   wallpaper, frost, fabric. No large area stays a single flat colour.
2. **At least three materials per set**, one of them on the ground plane.
3. **Scale the pattern to the object**, not to the frame: stone units ~46 px at
   1080 wide, planks ~26 px, shingles ~22 px.
4. **Pattern contrast stays low** (10–25 % of the base value): texture must be
   felt, not read.
5. **Every object casts a shadow** on the surface it touches; the shadow is a
   blurred ellipse, never a hard shape.
6. **Light comes from somewhere**: a visible or implied source plus a shaft or
   spill shape, with `screen` blending.
7. **One foreground occluder per wide shot**, out of focus.

Implementation: `engine/texture.tsx` (`MaterialDefs`), `engine/atmosphere.tsx`
(`CastShadow`, `LightShaft`, `FogBand`, `DustMotes`, `Glow`).

## 5. Camera language

| Move | Use it for | Curve |
|---|---|---|
| `pushInSlow` / `dollyIn` | realisation, intimacy, pressure | ease-out, 1.00→1.18 scale |
| `dollyOut` | loneliness, reveal of context | ease-in-out, 1.18→1.03 |
| `panLeft` / `panRight` | following a walk, scanning a space | ease-in-out, ±7% translate |
| `tiltUp` | scale, arrival at an object | ease-in-out, 3% vertical |
| `craneDown` | establishing arrival | ease-in-out |
| `drift` | a hold with life | sinusoid, < 0.1% amplitude |
| `static` | deliberate stillness, only when justified | none |

Rules: one move per shot, motivated by the line; no handheld shake unless the
scene is unstable; never combine zoom and pan to fake parallax.

---

## 6. Motion and animation

- Character: primary action + secondary action (head, hands) + ambient (cloth,
  breath). Ambient motion must be motivated by the set (wind, snow, flame).
- Sets: parallax by depth, never uniform translation.
- Particles: deterministic (seeded), frame-indexed, looping seamlessly.
- **Forbidden:** digital zoom on a still, speed-ramped pans, random camera jitter.

---

## 7. Type and captions

- Family: humanist sans (Nunito/Trebuchet fallback), weight 900, lowercase.
- Size: ≈ 4.8% of frame width, centred, max 3 words per cue.
- Outline: 2.2 px at 1080 wide + soft drop shadow for legibility over snow.
- Position: 83% of frame height; never over a face.

---

## 8. Sound

- Sparse bed: filtered-noise wind + low drone (root/fifth/octave).
- Motif: plucked pentatonic figure, ~68 bpm, sparse (≈ 70% of beats).
- Events: bell hits, snow footsteps, digging impacts, tied to shot time.
- Loudness target: −16 LUFS, TP −1.5 dB. Music with licence only — the LOCAL
  score is synthesised, so there is nothing to license.

---

## 9. What code reproduces well (and what it does not)

**Reproducible in code:** silhouette-based characters, colour scripting,
layered parallax, motivated light pools, caption typography and pacing, camera
moves, animated ambience, grain/vignette, sound design, edit rhythm.

**Approximated:** painterly brush texture (grain + gradients substitute for real
brushwork), background density (fewer props than the reference), cloth and hair
physics, facial micro-expression.

**Needs external generation or real footage:** photoreal rendering, realistic
human motion, complex hand interaction, actor performance, bespoke hand-painted
illustration at reference density.

---

## 10. Acceptance checklist for a shot

- [ ] silhouette reads at thumbnail size
- [ ] one warm and one cool light, both motivated
- [ ] three depth planes, near plane present
- [ ] one camera move, motivated, within the curves above
- [ ] character breathes/blinks at least once per 4 s
- [ ] captions ≤ 3 words, over the lower third, not over a face
- [ ] no freeze longer than 0.4 s, no black frame
- [ ] grain and vignette applied
