# CHANGELOG

## 0.10.1 — 2026-11-05

Corrective maintenance of the existing story pipeline. No UI work and no second
renderer; the corrected narration demo reuses the same Remotion composition,
cast, sets and asset catalogue.

### Fixed

- `studio.py render` and `storyboard` accepted `--manifest` but ignored it. The
  active project is now swapped for the duration of the command and restored in
  a `finally` block, including after a failed render.
- `library.compose` lowercased catalogue scene keys (`bellInsert` became
  `bellinsert`), which made the storyboard fail with `Unknown scene`. The
  renderer receives the camelCase scene name again.
- `library.compose` dropped top-level `narration`, so a narration project could
  silently become a character-voice project. The field is preserved.
- Narration used the visible character's voice on S01/S02. A project with
  `narration: true` now resolves every spoken line to `narrator`; a shot can
  opt into character dialogue explicitly with `dialogue: true`.
- `voicecheck` rejected a short stem even when it covered every spoken line.
  Coverage is now measured to `narration_end`, not to the final frame, and
  `assemble` rejects a soundtrack shorter than the picture unless
  `--allow-short-audio` is passed deliberately.
- `qa` gained an `audio_duration` gate, so an MP4 whose audio ends early cannot
  pass on container duration alone.
- The render provider buffered all Remotion output in memory, leaving
  `logs/render.log` empty for the whole 24-minute render. It now streams stdout
  and stderr to the log named by `studio.py render`.
- The identity audit now reports the measured head/body ratio against the rig's
  170 px body height, with a calibrated 0.35–0.65 band.

### Evidence

- Corrected demo: `projects/av_direccion_story/output/final_video.mp4` —
  30.933 s, 1080×1920, 30 fps, 927 frames, H.264/AAC 190.8 kb/s, 17.3 MB.
- `voicecheck`: 8/8 lines on one `ef_dora` narrator, 58 words, 23.09 s of speech;
  stem 31.183 s, last spoken line 30.188 s, mix 30.933 s.
- `qa`: **PASS 12/12**; `inspect`: **0/10 flagged**, UI mode A, 0 overlays;
  `evaluate`: **10 measured PASS, 4 human dimensions pending**.
- `python -m pytest tests -q`: **159 passed**. `npx tsc --noEmit`: exit 0.
- Render through `studio.py render --manifest`: 1464.45 s.
- Mix at `music_gain=0.20`: 47 windows within 3 dB of the voice → **5**.

### Limits

- Human review of narrative, acting, rhythm and style integrity is still
  pending; the structural QA does not replace it.
- No lip-sync, no forced alignment and no ASR; `voicecheck` measures signal, not
  intelligibility.
- The identity audit is structural plus a head/body ratio; it does not compare
  pixels or faces. The `cientifico` and `widow` cast entries are unused in this
  film and are reported as warnings, not deleted.
- The “two consecutive full renders through the provider” gate remains open;
  this pass exercised one full render through the provider with logs now
  streaming for future runs.

## 0.10.0 — 2026-11-05

Shared asset system on the existing catalogue and renderer. No video was
rendered for this change; the proof is a pair of Remotion stills.

### Added

- `scripts/acs/asset_forge.py` + `studio.py assets generate` — creates layered
  sets, character identities, reusable expressions, props, motion graphics and UI
  from Spanish/English requests using local deterministic SVG primitives.
- Schema-2 `assets/registry.json` entries with stable ids, style, resolution,
  aspect, preview, usage, scene/character metadata, dependencies, append-only
  versions, provenance, licence, compatibility and validation status.
- `scripts/acs/references.py` + `assets/references.json` — persistent, selected
  reference metadata with provenance/licence checks.
- `GeneratedScene`, `PropLayer`, generated cast merging and expression overrides
  in the existing Remotion composition. Generated graphics resolve through the
  existing `OverlayLayer`; no second renderer.
- `projects/asset_forge/` — a proof project that combines a generated set,
  character, expression, prop and comparison graphic with the existing
  `set:doorway` and `character:elder`.
- `ASSET_SYSTEM.md`, expanded `ASSETS.md`, and tests for generation, versioning,
  previews, search, similarity, composition, references and proof stills.

### Evidence

- `python -m pytest tests -q`: **148 passed**.
- `cd studio && npx tsc --noEmit`: exit 0.
- `python scripts/studio.py assets validate`: 38 assets, OK.
- Remotion `AssetForgeDemo` stills: `projects/asset_forge/preview/`, contact sheet
  `contact_sheet.jpg`.

### Limits

- The forge composes vector primitives; it is not an image/diffusion model.
- Generated assets are fixed to 1080×1920 / 9:16; other formats are rejected
  until a format pass exists.
- The set grammar is laboratory-led; new grammars belong in `_set_spec`, not in a
  second renderer.
- Reference selection is purpose/tag based, not visual embedding search.

## 0.9.0 — 2026-11-05

Audiovisual direction on the existing pipeline. The renderer, cast, sets, voice
cache and asset catalogue are reused; the new layer decides the edit.

### Added

- `scripts/acs/av_director.py` + `studio.py av` — a beat sheet becomes the same
  render manifest, with `beat`, `scale`, `cameraMotive`, `transitionMotive` and
  timed `sound` cues. Unmotivated dissolves and unknown assets are rejected.
- `scripts/acs/avqa.py` + `studio.py avqa` — structural creative QA for hook and
  close, scale variety and runs, camera variety and motives, movement balance,
  transition motives, action/reaction shots, sound coverage, duplicate lines and
  duration. It writes `quality/av_audit.json` and `.md`.
- `avqa --baseline` — measured before/after against another manifest;
  `quality/before_after.md` in the demo.
- `montage` as an evaluation dimension, measured only when `av_audit.json` exists.
- `trackLeft`, `trackRight` and `reframe` camera moves, registered in the asset
  catalogue and the preproduction brief.
- `projects/av_direccion/` — 10 shots, 30.933 s, the eight original narration
  lines, two wordless reaction/pause shots and 15 timed sound events. Rendered
  MP4: 927 frames, 17.5 MB, QA 11/11, inspect 0/10, evaluation 10 measured PASSes
  and 4 pending human dimensions.
- `AV_DIRECTION.md`; tests for planning, creative QA, comparison and sound cues.

### Changed

- Explicit per-shot sound cues now own the soundtrack (an empty list is
  intentional silence); manifests without `sound` keep the old scene effects.
- The demo mix uses `music_gain=0.20`; windows within 3 dB of the voice fell from
  40 at the default 0.45 to 4, without removing the score.

### Fixed

- `write_preproduction` subtracted a transition for every boundary even when the
  shot was a hard cut, so the storyboard claimed 28.4 s for a 30.933 s edit. It
  now sums each shot's own `transitionIn`.

## 0.8.0 — 2026-11-05

Character identity and real narration, on the same pipeline. No second engine,
no new provider, no UI work.

### Fixed

- `cast.json` declared `height` and a silhouette, but `Character.tsx` ignored
  both: every character was the same body with another coat. Identity height is
  now applied before the shot scale, and the Python/TypeScript overlay anchors
  use the same factor, so labels still land on the corrected head.
- The beanie band was drawn at `-0.36H..-0.10H`, across the eye line; at close
  range it hid the eyes and the face lost its strongest identity cue. The band
  now sits on the brim, above the brows.
- `kokoro_tts.build_stem` summed overlapping takes at S01/S02 and S03/S04
  (0.16 s of two voices). A line now ends where the next begins, with a 20 ms
  fade instead of a doubled word.
- The mix limiter auto-levelled to 0 dBFS. It now limits at 0.89 with a 1 ms
  attack and 0.9 output gain. The intermediate mix still reports one 0.0 dBFS
  sample at S04; the delivered MP4 is capped by two-pass loudnorm (−1.5 dBTP).

### Added

- `scripts/acs/identity.py` + `studio.py identity` — canonical cast audit:
  required identity fields, unique ids, no shot-level identity overrides,
  registered wardrobe, per-character coverage. Writes `identity_audit.md`.
- `IdentitySheet` composition — the same identity in seven poses (frontal,
  three-quarters, profile, walk, talk, surprise, action) for the two recurring
  characters, plus `identity_shots.png`, the same character cropped from every
  shot it appears in.
- `scripts/acs/narration.py` + `studio.py voicecheck` — per-line take/stem/mix
  RMS and peak, silence, duration, ordering, duplicate text and trimmed tails;
  writes `narration_validation.md`.
- Tests: 6 identity + 3 narration (128 total).

## 0.7.0 — 2026-11-04

UI as direction. The overlay layer stops being a set of fixed cards and becomes
a per-shot decision: whether the line needs UI, in which presentation mode,
where it can live without covering a face, a body or the captions, and for how
long a viewer needs it.

### Added

- `scripts/acs/ui_director.py` + `studio.py ui` — intent classification, mode
  choice (A–F), budgeted size, adaptive box, reading window and an audit trail
  (`reason`, `reading_seconds`, `window_seconds`, `escalated_from`).
- Six presentation modes rendered by the existing composition:
  A scene only · B clarification over the scene · C actor-bound UI ·
  D attenuated scene · E independent explainer · F full-bleed bridge.
- `scripts/acs/uiqa.py` — mode/placement/timing QA, plus `measure_render`, which
  samples the real MP4 and measures UI contrast and scene detail per mode.
- `projects/ui_direccion/` — 27.4 s demo, Spanish Kokoro narration, 8 shots that
  exercise A, B, C, D, E and F, 20 SRT cues, storyboard and QA reports.
- `UI_DIRECTION.md`, this changelog, roadmap and matrix updated.
- Tests: 25 new for intent, modes, reading time, adaptive placement, escalation
  and UI QA (118 total).

### Fixed

- `overlays.circle_hits_box` mixed normalised box coordinates with pixel face
  centres, so any face below the top third read as uncovered. A chart could sit
  on a head and pass. Fixed and covered by a regression test; the audit now
  reports 2 face overlaps in `sistema_demo` (0 in the new demo).
- The bridge card was clamped by the 6 % safe area, leaving a strip of scene
  around what must be a full-bleed transition. Mode F now sets `safe: false` in
  the planner and the QA exempts it.
- Charts kept compact type sizes inside a focus box, so mode D/E showed a stamp
  in an empty plate. Bar, donut, line, ranking, counter and process now scale
  their type and geometry from the resolved box.
- The first storyboard of the new demo silently rendered the *previous* active
  manifest (`studio/src/data/project.json`). The demo now writes the planned
  manifest as active before storyboarding; the mismatch was caught by looking at
  the stills, not by a passing test.
- Render evidence sampled the storyboard keyframe, so a bridge starting at 0.45
  was measured while still fading in. The probe now samples the middle of each
  element's own window and reports no UI contrast for actor-bound labels instead
  of a misleading 0.0.
- `evaluate` flagged E/F plates as empty scenes while `inspect` already exempted
  them. Both now apply the same rule: emptiness judges scene shots A–D, and E/F
  are judged as graphic plates by `ui_composition` and `legibility`.
- A full-bleed bridge no longer warns that it covers the actors' heads: that is
  the mode's purpose, and the warning trained the reader to ignore warnings.

## 0.6.0 — 2026-11-04

From a shot assembler to a system that can look at its own output: style tokens,
a motion-graphics and UI layer, structured feedback, inspection, evaluation and
rule-based creative direction. No second pipeline: everything renders through
the existing Remotion composition and the existing manifest.

### Added

- `studio/src/engine/styles.tsx` + `studio/src/data/styles.json` — five styles
  (cinematic, editorial, infographic, minimal, cartoon) as tokens over one
  engine; the same file is read by the Python inspector and the director.
- `studio/src/motion-graphics/` — 13 overlay types (label, badge, callout,
  panel, hud, highlight, arrow, counter, bar, donut, line, ranking, process),
  data-driven, frame-deterministic, with in/out windows relative to the shot.
- `motion-graphics/layout.ts` — actor anchoring: labels follow the body, prefer
  above the head, never cover the face, clamp to a 6% safe area.
- `scripts/acs/overlays.py` — validation of payload, provenance, safe area,
  face and caption-band collisions; constants are checked against the
  TypeScript by a test.
- `scripts/acs/feedback.py` + `feedback/records.jsonl` — structured corrections
  with category, severity, scope and status; generated `USER_FEEDBACK.md`,
  `VISUAL_PREFERENCES.md`, `STYLE_RULES.md`, `IMPROVEMENT_LOG.md` and
  `REGRESSION_CASES`-style cases. Records and scopes only: it does not learn by
  itself.
- `scripts/acs/inspect.py` — pixel inspection (emptiness, edge energy, local
  caption contrast, palette drift, depth bands) plus manifest geometry.
- `scripts/acs/evaluate.py` — scorecard where every dimension declares its
  evidence kind; subjective dimensions stay `pending` without a human review;
  reference snapshot + metric diff.
- `scripts/acs/director.py` + `studio.py direct` — title/idea/script → concept,
  beats, style decision with rationale, casting, overlays, spec and manifest.
  Narration written from a template is flagged as needing author approval.
- `studio.py feedback | inspect | evaluate | styles`, `compose` carries `style`,
  `assemble --audio` muxes the voice mix.
- `projects/sistema_demo/` — hybrid demo: two characters, two sets, Spanish
  narration, character label, bar chart, callout, HUD, panel and transitions.
- `projects/creado_desde_titulo/` — generation from a title, with stills.
- Tests: 22 new (feedback, overlays incl. anti-drift, director, inspection,
  evaluation).

### Fixed

- Kokoro worker failed when launched as a script: `scripts/acs` on `sys.path`
  shadowed numpy's bootstrap (`attempted relative import with no known parent
  package`). Both invocations now pass `-P`.
- `overlays.resolve_box` ignored `placement.box` in Python while the renderer
  used it; default boxes for panels, bars, donuts, lines, rankings and process
  diagrams also reached into the caption band. Both fixed, and the mirror is
  now tested against the TypeScript constants.
- The inspector called legible captions unreadable: it measured a percentile of
  the whole caption band. It now measures local contrast per cell.

## 0.5.0 — 2026-11-04

Kokoro TTS as a local voice provider, in Spanish, running on CPU. See
`KOKORO_INTEGRATION.md` for the audit, the licence notes and the measurements.

### Added

- `scripts/acs/kokoro_worker.py` — Kokoro + torch in `.venv-kokoro` (Python 3.12),
  called over a JSON boundary; the main pipeline never imports torch.
- `scripts/acs/kokoro_tts.py` — provider contract: config, availability probe,
  explicit-download guard, cache keyed on text/voice/model/lang/speed/version,
  timeline stem, and `fit_shots()` so a long line can stretch its shot.
- `scripts/acs/subtitles.py` + `studio.py subtitles` — SRT from real word times.
- `scripts/acs/mixdown.py` + `studio.py mixdown` — sidechain duck of the score
  under the voice, writing both the mix and the ducked bed.
- `studio.py kokoro` — runtime, device and per-voice weight report (no download).
- `config/kokoro.json` — interpreter, model, paths, Spanish voices per character.
- `projects/kokoro_demo/` — four Spanish lines, real audio, stem, SRT and mix.

### Changed

- `voice.py` accepts `--provider kokoro` and records `pred_dur` word timings on
  the film clock, plus per-line audio duration and shot overflow.
- `mixcheck.py` measures the voice against the **ducked bed**, never against the
  final mix (which contains the voice itself).
- `.gitignore` excludes `.venv-kokoro/`, `.models/`, `.cache/`.

## 0.4.0 — 2026-11-03

Visual pass after auditing the reference corpus against demos 001 and 002. The
three gaps that mattered were acting, depth and light; each was fixed in the
existing components instead of replacing the engine. New film: `demo_003`.

### Added

- **Hands, elbows and head turn** in the rig: an open mitten with a thumb, a
  pointing fist, explicit elbow angles and a `yaw` that slides the face without
  turning the head silhouette.
- **Acting presets** `reach`, `turn` and `call` with the beat structure the old
  rig lacked: anticipation, travel, overshoot, settle, hold. The walk-in ramps in
  and out, and the digging strike rebounds.
- **One-point perspective rooms** (`engine/perspective.ts`): `makeRoom`, `P/Q`,
  `onFloor`. The doorway interior is rebuilt as a room instead of a lit
  rectangle: converging side walls, floor boards to the vanishing point, a rug and
a patch of window light laid in room coordinates.
- **Contrast veil in the square** (`LightVeil` in `TownNight`): the moon and the
  lantern keep their pools, mid-tones sink.
- **Word-guided editing** (`scripts/acs/edit.py`, `studio.py edit`): cues from
  word timings, boundary alignment with a tolerance that is reported when
exceeded, caption windows derived from the same clock.
- **Project composition through the catalogue** (`library.compose`,
  `studio.py compose`): a spec names scenes, cameras and characters by asset id;
an unknown id aborts before a manifest exists. `demo_003` is built this way and
reuses every asset of the two previous films (0 new assets).

### Changed

- `demo_003/` ("The Rope", 28.8 s, 6 shots) replaces the active manifest; demos
  001 and 002 and their renders are untouched.

## 0.3.0 — 2026-11-03

Repository audit and selective integration of
<https://github.com/kelano86/what-if-animation> (MIT, © FreshStack). The existing
engine stays the base; only what measurably helps was taken. See
`REPOSITORY_COMPARISON.md` and `ATTRIBUTION.md`.

### Added

- **Asset library and catalogue** (`scripts/acs/library.py`, `assets/catalog.json`):
  stable ids for characters, rig, sets, engine modules, voices, sound events,
  camera moves and transitions; derived from the real sources so it cannot drift;
  `search`, `show`, `validate`, `reuse`, `rebuild`; version from file mtime;
  licence and dependency checks; `projects/<id>/manifest.json` freezes what each
  film was rendered from.
- **Storyboard stage** (`scripts/acs/storyboard.mjs`, `storyboard.py`,
  `studio.py storyboard`): one still per shot at its key frame, bundled once, laid
  out as a captioned contact sheet — review a shot in seconds instead of a
  26-minute render.
- **Cast sheet** (`composition/CastSheet.tsx`, `studio.py cast`): every character
  side by side plus acting states, so identity drift is caught before animating.
- **Voice pipeline** (`scripts/acs/voice.py`, `config/voices.json`, `studio.py
  voice`): provider-agnostic, LOCAL by default (word timings only, no speech, no
  network), ElevenLabs behind an explicit Voice ID + key + `--authorize-spend`,
  cached by content hash, credits logged. No lip-sync is claimed.
- **Mix check** (`scripts/acs/mixcheck.py`, `studio.py mix`): flags music or
  effects within 3 dB of the voice; reports "not applicable" when there is no
  speech stem instead of passing silently.
- **Contrast pass** (`LightVeil`, `Cone` in `engine/atmosphere.tsx`), applied in
  the doorway set: mid-tones sink, lamp and door stay bright, characters keep full
  brightness.
- **Animation helpers** (`engine/math.ts`): `backOut`, `settle`, `kf`,
  `easeInCubic`.
- **Mastering**: two-pass linear `loudnorm` to −14 LUFS / −1.5 dBTP.

### Changed

- Walk-in acting ramps in and out instead of snapping to full gait, and settles
  when the foot lands; the digging strike overshoots and rebounds.
- The active manifest is now `demo_002`, reusing every asset of `demo_001`
  through the catalogue.

### Kept

- The 4 sets, rig, score, QA gates and tests stay this project's own; the
  external room-perspective engine, segment/power-look timeline, characters and
  MP3 library were deliberately not adopted.

## 0.2.1 — 2026-11-03

Second review pass, driven by frames decoded from the delivered v2 MP4.

### Fixed

- **Timeline overlap was subtracted from the wrong shot** (`composition/Demo.tsx`):
  `shotTimeline` used each shot's own `transitionIn` instead of the next one's, so
  the film ran 0.47 s longer than the score and the dissolves behaved as fades
  from black. `audio_gen.spec_from_project`, `qa.caption_coverage` and the audio
  unit test now share the same arithmetic (35.133 s, 1054 frames).
- **Black strip on the trailing edge** of the doorway shot: `panLeft`/`panRight`
  shifted the canvas 7 % against a 1.10x zoom (5 % overscan per side). They now
  use 1.16x with a 5.5 % shift, so the pan can never expose the background.
- **Headstones that read as spoons**: the cross kind was a thin shaft with a wide
  arm near the top. It is now a solid slab with the cross carved on its face, and
  the stones are slightly larger.
- **Duplicate shovel** at the open grave (the apprentice already carries one) and
  a flat-looking pit: the spare prop is gone and the pit has an inner shadow.
- **`qa.py`** deleted `fade` inside its shot loop, which raised `NameError` from
  the second shot on; the duration now uses `float(shot["seconds"])` directly.

## 0.2.0 — 2026-11-03

Visual-density pass after an independent review of the v1 render against the
reference corpus. v1 is preserved in `projects/demo_001/output/v1/`.

### Added

- **Procedural materials** (`studio/src/engine/texture.tsx`): stone ashlar,
  timber planks with grain, shingle roofs, speckled snow, carpet motifs,
  wallpaper, frost and brush hatching — all as `<pattern>` definitions with a
  scene prefix so crossfades cannot collide on ids.
- **Light and grounding** (`studio/src/engine/atmosphere.tsx`): cast shadows,
  volumetric light shafts, fog bands, glows and deterministic dust motes.
- **Architecture in the sets**: timber-framed houses with stone footings, sills,
  icicles, chimneys with smoke, shop signs; a full interior behind the doorway
  (rug, table, chair, shelf, coat, picture, hanging lamp); louvred belfry with
  iron-strapped headstock; carved headstones, chapel, fence and open grave.
- **Foreground occluders** (blurred branch, snow lip, rope) for real depth.

### Changed

- **Character rig**: volume gradient on the coat, occlusion under the chin and
  hem, two-segment arms with a driven elbow, boots, brows with emotion tilt,
  sideburns under headwear, head lead/lag in the walk and coat sway.
- **Composition** (`studio/src/data/project.json`): actors moved to thirds,
  shot scales re-tuned (1.40 / 2.05 / 5.15 / 1.85), foreground framing added.

### Fixed

- Nested `<defs>` inside `<defs>` for material patterns (replaced by a fragment).
- Unused palette binding left in `TownNight` after the rebuild.

## 0.1.0 — 2026-11-03

First working build. Everything listed was executed on this machine unless
marked otherwise.

### Added

- **Reference analysis** (`scripts/analyze_reference.py`, `scripts/acs/`):
  FFprobe metadata, cut detection at two thresholds, shot list with micro-shot
  merging, shot-relative frame extraction, contact sheets, deterministic k-means
  palette, SAD translation motion estimate, loudness/RMS/activity, markdown report.
- **Provider subsystem** (`scripts/acs/providers/`): `Provider` interface, cost
  models, `CostGuard` (authorization latch + hard budget), JSONL operation log,
  registry with mode gating, three local providers, three external contracts that
  refuse to run instead of faking output.
- **Automatic strategy selector** (`scripts/acs/selector.py`): reuse → code →
  external, with reasons and quality-risk labels.
- **Preproduction** (`scripts/acs/project.py`): folder layout, script,
  storyboard, shot list, character bible from `cast.json`, environment bible,
  continuity report, SHA-256 manifest.
- **Procedural soundtrack** (`scripts/acs/audio_gen.py`): wind bed, drone,
  plucked motif, bell/footstep/dig events, WAV export, deterministic seed.
- **Remotion engine** (`studio/`): 1080×1920 composition, SVG character rig with
  gait/blink/breath/props, five sets with SVG parallax, camera vocabulary,
  word-chunked captions, film grain/vignette/halation, deterministic particles,
  crossfade timeline.
- **Assembly and QA** (`scripts/acs/assemble.py`, `qa.py`): mux + loudnorm +
  H.264/AAC export, preview, black/freeze/motion/duration/format/loudness/caption
  gates with a markdown report.
- **Pipeline CLI** (`scripts/studio.py`): `status`, `analysis`, `preproduction`,
  `plan`, `audio`, `render`, `assemble`, `qa`, `produce`.
- **Tests**: 21 unit tests over shots, selector, guard, registry, audio
  determinism, preproduction, QA.
- **Docs**: `SKILL.md`, `VISUAL_STYLE_GUIDE.md`, `ARCHITECTURE.md`,
  `INSTALLATION.md`, `USER_GUIDE.md`, `RESEARCH_REPORT.md`,
  `MODEL_COMPARISON.md`, `LIMITATIONS.md`, `TEST_REPORT.md`,
  `references/reference-style-analysis.md`.

### Fixed during the build

- Parallax layers were HTML `<div>`s inside `<svg>` and were silently dropped —
  replaced with `ParallaxGroup` (`<g>`).
- Actors rendered as bare `<g>` outside any `<svg>` and were invisible — actors
  now have their own SVG layer.
- Character head was double-offset (figure appeared upside down) — single
  translate + local rotation.
- `FilmFinish` painted an opaque fill over the whole frame (black render) — it is
  now an overlay-only stack.
- Audio activity gate used a fixed median+8 dB offset that climbed above the
  peaks on compressed mixes — now anchored on the 90th percentile.

### Known gaps

See `LIMITATIONS.md`. Notably: no image/video/voice generation, no
speech-to-text, art density below the reference, translation-only motion model.
