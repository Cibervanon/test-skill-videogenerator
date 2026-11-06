# LIMITATIONS

Everything below is a known, verified gap. None of it is simulated away.

## 1. Generation

- **No image or video generation.** `providers/external.py` contains only
  contracts; every external provider reports *"adapter not implemented in this
  build"* and raises instead of returning placeholder media.
- **Kokoro is the only way to hear a voice, and only in Spanish.** `voice.py`
  also writes LOCAL timings and contains a real ElevenLabs adapter, but that one
  has never been executed: it needs a Voice ID, a key and `--authorize-spend`.
  No ElevenLabs take, no credit and no network call happened in this build.
- **Kokoro's Spanish cast is three voices** (`ef_dora`, `em_alex`, `em_santa`),
  graded "fair" by the model's own voice sheet. Casting is voice + speed, so
  characters are not as distinct as a commercial library allows.
- **Spanish G2P is espeak-ng**, not a learned Spanish front-end: numbers, acronyms
  and proper nouns inherit espeak's rules and can be mispronounced.
- **Kokoro's word timings are predicted, not measured.** They come from
  `pred_dur` normalised to the take's real length; a boundary can be tens of
  milliseconds off and there is no forced alignment in the box.
- **No comparison against ElevenLabs was run**, because that spends credits. The
  claim is "works offline, in Spanish, for free, with usable timings", not
  "sounds better".
- **CPU speed: 1.6× realtime** on this machine, plus ~3 s of model load per call;
  a 5-minute narration takes about 8 minutes. GPU is untested here (no CUDA
  device).
- **Licensing:** Kokoro code and weights are Apache-2.0, `misaki` Apache-2.0,
  `torch` BSD-3; `espeak-ng` (bundled by `espeakng-loader`) is **GPL-3.0** and is
  invoked as a separate phonemiser process — fine locally, a distribution
  consideration if this skill ever ships as a binary bundle.
- **No photoreal output anywhere.** LOCAL mode is painted-vector animation.

## 2. Analysis

- **No speech-to-text.** `ffmpeg -filters` in this build exposes no `whisper`
  filter, and no whisper runtime/package is installed. `transcript.json` is
  therefore **not produced**; the `analysis/` folder contains only what FFmpeg
  measures (metadata, shots, palette, motion, loudness, activity).
- **No object, face or text detection.** Scene understanding is limited to
  frame-difference, colour and level statistics.
- **Cut detection is a difference metric.** Cross-dissolves and camera-carried
  transitions are under-detected; that is why the reference corpus shows 0–1
  hard cuts per minute while the frame sheets show many setups.
- **Motion model is translation-only.** Pan/tilt magnitude is estimated;
  zoom, rotation and true parallax depth are not measured.
- **Activity detector is level-based.** It cannot distinguish speech from music
  or identify speakers.
- **No OCR**, so burned-in captions are verified from the cue plan, not from the
  rendered pixels.

## 3. Renderer

- **Art density is below the reference.** The sets hold 8–20 props; the
  reference holds dozens plus hand-painted brushwork. Grain and gradients
  approximate the paper texture; they do not reproduce brush strokes.
- **Line quality is constant.** No pressure/taper variance like hand inking.
- **Rigid rig.** No cloth, hair or soft-body simulation; poses are parametric.
- **Hands are presets, not IK.** The rig has three grips (`open`, `point`,
  `fist`), a thumb and an elbow angle, but no inverse kinematics: a held prop is
  rigid to the forearm. In `demo_003` S04 the shovel therefore hovers beside the
  grave instead of planting its blade in it — the strike reads, the contact
  does not.
- **One-point perspective only, and only where authored.** `engine/perspective.ts`
  gives correct converging rooms, but the doorway is the only set that uses it;
  the square and the field are still layered 2D. A room only reads as deep when
  its back wall is inset inside the opening — the first attempt proved that the
  maths alone is not enough.
- **No foreground occluder in the square.** The doorway frames the subject with
  its own frame; the night square still has nothing between camera and subject.
- **Facial acting is parametric** (blink, mouth aperture, head tilt). No
  lip-sync to real audio, because there is no voice track in LOCAL mode.
- **Five sets only** (`townNight`, `doorway`, `faceCloseup`, `fieldDawn`,
  `bellInsert`). New sets are code; there is no set generator.
- **Performance.** 1080×1920 SVG with `feTurbulence` grain renders at roughly
  500 frames/min on this machine; a 34 s film takes ~8–10 minutes.

## 4. Audio

- **Synthesis only.** Additive bells, filtered-noise wind, Karplus–Strong plucks
  and noise-burst foley. No speech, no sampled instruments, no real room reverb.
- **Loudness normalisation is two-pass linear** to −14 LUFS / −1.5 dBTP; it
  measures the score first, so the gain is steady instead of pumping.
- **No lip-sync and no pause trimming.** Dialogue would be narration over the
  shot; the rig has no phoneme shapes, and silence between words is not cut.
- **Word-cued editing exists but is not driving the cut yet.** `scripts/acs/edit.py`
  aligns shot boundaries to word timings within a tolerance and reports the
  drift; it was run on `demo_003` (all six boundaries within ±0.45 s) and tested
  with synthetic timings. Because LOCAL mode produces timings but no audio,
  nothing is cut *to* a real spoken word yet; the shot clock still leads.
- **The score does not follow the picture beat-for-beat** beyond the event list
  derived from shot timings.

## 5. Pipeline

- **One live manifest at a time.** `studio/src/data/project.json` is the film being
  rendered; `projects/<id>/manifest.json` keeps the copy each delivery used, and
  `assets/catalog.json` records what the library offered at that point;
  `projects/<id>/preproduction/project.source.json` keeps the copy used for a
  given delivery, so history is traceable but not multi-project concurrent.
- **Windows-first scripts.** FFmpeg commands are portable; the Remotion provider
  uses `shell=True` on Windows only.
- **Budget/authorization is file-based**, not a signed ledger. It is enforced in
  code, and every attempt is logged, but a user with write access to the config
  can change it — that is inherent to a local tool.

## 6. Claims I deliberately do not make

- That the demo reaches Rickclips-level fidelity. It reaches the *formal* parts
  (framing, rhythm, palette logic, caption treatment) and not the illustration
  density.
- That quality scores are objective. The QA gates are calibrated on this
  engine's own renders and catch regressions; they are not a measure of cinema.
- That model prices/limits in `MODEL_COMPARISON.md` are current or tested.

## 7. Styles, information layer and direction (0.6.0)

- **A style is a token set, not a new art style.** All five styles share the same
  rig, sets and camera; they change palette, type, density, plate treatment and
  motion. A cartoon *drawing* pack does not exist.
- **Thirteen overlay types, all 2D.** No 3D charts, no maps with real geometry.
- **Labels are geometric, not perceptual.** Placement uses the rig geometry and
  the face circle; it does not detect an actual occlusion in pixels.
- **The inspector does not see semantics.** No OCR, no object detection, no
  judgement of acting, story or taste. Those dimensions stay `pending` until a
  human writes `preproduction/visual_review.json`.
- **Palette drift is RGB distance**, not a perceptual metric (CIEDE2000 is
  pending); grain and grade can move it slightly.
- **Feedback does not learn automatically.** It records, classifies and scopes;
  promotion to a rule requires an applied change plus validation evidence.
- **The director is rule-based.** Its narration from a title is a template,
  explicitly flagged `requires_author_approval`; it does not write prose.
- **One style per project.** Per-shot style overrides are not supported, by
  design: they are the fastest way to break visual consistency.
- **Data graphics require provenance.** Without a source the renderer prints
  `ilustrativo`; there is no fact-checking, only labelling.

## 8b. Character identity and narration (0.8.0)

- **One body rig, many identities.** Height, head radius, hat, facial hair and
  palette are canonical data; the torso, legs and arms are still the same paths
  for every character. The declared `silhouette` is descriptive, not geometry.
  Distinct body outlines are on the roadmap.
- **Yaw is a 2D face shift, not a profile.** The rig moves the features inside
  the head circle and keeps the silhouette; a true three-quarter or profile
  head would need a second drawing.
- **The identity audit is structural, not perceptual.** It proves that a shot
  references the canonical id and does not override coat/head/hat; it does not
  compare pixels. `IdentitySheet` and `identity_shots.png` are for human review;
  there is no face embedding and no automatic identity score.
- **Narration is verified by signal, not by ear.** `voicecheck` measures take,
  stem and mix RMS/peak and checks order, duplicates and trims. It does not
  transcribe, so it cannot prove the words are intelligible or correctly
  pronounced; listening is still required.
- **Burned-in captions are shot-synced, not word-synced.** The SRT and
  `words.json` carry real take timings, but `buildCues` still distributes the
  burned-in words by character weight. This is the open roadmap item, not a
  claim of lip-sync.
- **The takes are cached from real Kokoro runs.** `voicecheck` proves the WAVs
  exist and are audible; the plan marks them `cached`, and regenerating them is
  only necessary when text, voice or speed changes.
- **The intermediate mix can still peak at 0.0 dBFS in one window (S04); the
  delivery is capped by two-pass loudnorm at −1.5 dBTP.** `voicecheck` reports
  the peak instead of hiding it. The mix file is an intermediate, not a master.

## 8c. Audiovisual direction (0.9.0)

- **The planner completes an authored beat sheet; it does not understand a
  story by itself.** It validates functions, scales, camera motives and sounds,
  and fills defaults. Deciding what the hook is remains a writing decision.
- **`scale` is a declared unit, not focal length.** The renderer still applies
  actor scale and a 2.5D camera transform; there is no depth of field, true
  parallax or lens model. A close-up is close because the actor is large and the
  camera moves in, not because a lens was chosen.
- **The creative audit is structural.** It can prove that a reaction shot exists,
  that scales vary and that a dissolve has a motive. It cannot see whether the
  reaction is good, whether the composition works or whether the film is moving.
  Those stay `pending` until a human writes a review.
- **Continuity is asserted, not tracked.** Character ids, positions, wardrobe
  and props are in the manifest; there is no 3D scene or hand-off tracker, so a
  prop can change hands between shots if the plan says so.
- **Acting remains preset-based.** The plan coordinates actor, listener and
  reaction, but the rig has no IK, cloth or visemes; a reach is a parametric arm
  arc, not a hand locked to the rope.
- **The audio cues are synthesised, not recorded.** Bell, footstep and dig are
  procedural; ambience is a wind bed. The mix was measured for voice competition
  (4 windows within 3 dB at `music_gain=0.20`), not judged as a soundtrack.
- **The demo's two wordless shots are intentional, not missing captions.** S04 is
  the pause after the rope arrives; S06 is the keeper's reaction. The caption
  coverage check reports 8/10 because the plan says so.
- **The composition exemption for S04 is narrow and declared.** Its 60.3% flat
  tiles are reported as `declared_insert_max`; only a shot marked
  `beat=insert` and `scale=detail` is exempt. A normal scene above the 55%
  threshold still fails.

## 8. UI direction (0.7.0)

- **Boxes are resolved once per shot, not per frame.** The solver validates the
  cast pose of that shot; a long pan can move a body under a screen-space card
  mid-shot. The rendered frames are sampled, but there is no per-frame reflow.
- **The body envelope is a proxy.** Head, torso, coat and the arm swing are
  covered; fingers and props are not. A hand can enter a card's margin without
  the geometry noticing.
- **Intent is a keyword classifier or a declared field.** It does not read the
  script semantically; a line without its keyword falls back to `narracion`.
- **Reading time is an estimate (4 words/s).** There is no eye tracking and no
  human reading test; the QA only proves the window is at least that long.
- **No morph between modes.** D dims, E replaces, F covers. Each boundary is a
  cut or a dissolve, not a transformation of the set into a diagram.
- **The modes are templates.** D always uses the style scrim; E always uses the
  same neutral plate; F is a card, not a bespoke transition design.
- **Pixel evidence confirms the mode switch, not quality.** `measure_render`
  shows that B/C keep scene detail and that E/F are graphic plates; it cannot
  say whether the composition is good.
- **The demo declares its intents.** Automatic classification exists and is
  tested, but the 8-shot film fixes `intent` per shot so the decision is
  auditable; it is not evidence of understanding a free-form script.

## 9. Shared asset system (0.10.0)

- **The forge composes deterministic SVG primitives; it does not generate
  images.** A request produces a renderable vector asset, not photorealism and
  not a diffusion-model result. No credits or network calls are involved.
- **The set grammar is laboratory-led.** `_set_spec` builds the laboratory room;
  other subjects currently reuse that grammar. A genuinely different location
  needs a new grammar in the same module, not a second renderer.
- **One body rig.** Generated characters can change identity data, palette,
  hat/hair, proportions within the calibrated band and expressions, but not
  anatomy or a new rig.
- **Props are primitive compositions.** The lamp is a real renderable prop; the
  generic object is a small box/screen form. The hand-authored `hold` union
  remains the route for props attached to the actor's hand.
- **Fixed format.** Forged assets render at 1080×1920 / 9:16. Other resolutions
  and aspect ratios are rejected explicitly; there is no format pass yet.
- **Previews are SVG.** They prove the asset spec and composition, not a final
  pixel render. The proof stills at `projects/asset_forge/preview/` are the pixel
  evidence for this delivery; no MP4 was generated.
- **Reference selection is tag/purpose based.** It does not embed images or
  understand visual similarity. References must have a real source path and a
  known licence; unknown provenance is rejected.
- **Validation is structural.** It checks metadata, previews, versions,
  dependencies, format and renderer compatibility. It does not judge whether the
  generated background is aesthetically good.

## 10. Story recovery and narration consistency (0.10.1)

- **One narrator is a project mode, not automatic dialogue detection.**
  `narration: true` forces every line without `dialogue: true` to `narrator`.
  A future dialogue scene must opt in per shot; the system does not infer who is
  speaking from the visible actor.
- **Audio coverage is checked against the last spoken line.** A deliberately
  silent tail is valid; an audio file that ends before the last word is not.
  `qa.audio_duration` also catches a container whose audio stream is shorter than
  its picture.
- **The 18.45 s WAV cited in the brief is not this film's stem.** The latest
  story stem is 31.183 s (8 lines, last line ends at 30.188 s), and the mix is
  30.933 s. The 18.45 s file in the workspace belongs to `projects/kokoro_demo`.
  This is an ownership mismatch, not a truncation in the rendered MP4.
- **Music can still sit close to the voice.** With `music_gain=0.20` five windows
  are within 3 dB; that is a measured warning, not proof of intelligibility.
  Listening remains a manual QA step.
- **Identity is canonical but not pixel-perceptual.** `head_to_body` is measured
  from the rig geometry; there is no face embedding, no pixel diff and no
  automatic identity score. The two unused cast entries remain available for
  other stories and are warnings, not failures.
- **The render-provider gate is only partly closed.** Progress now streams to
  `logs/render.log` and the manifest is restored on failure, but only one full
  provider render has been exercised after the change; two consecutive renders
  remain the acceptance gate.
