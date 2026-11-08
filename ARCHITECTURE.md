# ARCHITECTURE

## 1. Principle

Deterministic code is the production path. External generation is a swappable
capability behind an interface, disabled by default and impossible to trigger in
LOCAL mode. The film is data; the renderer is a pure function of that data.

```
                    ┌──────────────────────────┐
  reference.mp4 ──► │ analysis (FFmpeg)        │ ──► measurements, shots, palette
                    └──────────────────────────┘
                              │
                    ┌─────────▼─────────────┐
  project.json ───► │ preproduction         │ ──► script, storyboard, bibles, continuity
  cast.json          └─────────┬─────────────┘
                              │
                    ┌─────────▼─────────────┐
                    │ selector              │ ──► code / reuse / external per element
                    └─────────┬─────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
  audio_gen (WAV)      Remotion (MP4)         provider registry
  procedural score     vector scenes          (local + gated external)
        │                     │
        └────────► assemble (FFmpeg) ◄──────────┘
                              │
                              ▼
                     qa gates + reports
```

## 2. Modules

### `scripts/acs/` — Python pipeline

| Module | Responsibility |
|---|---|
| `ffmpeg.py` | tool detection, ffprobe JSON, PCM/rgb24 decode, error surfacing |
| `scenes.py` | cut detection, shot list, micro-shot merging |
| `frames.py` | shot-relative frame grabs, contact sheets |
| `palette.py` | deterministic k-means palette + tonal spread |
| `motion.py` | SAD translation search → pan/tilt/energy (no OpenCV) |
| `audio.py` | loudness, RMS envelope, activity heuristic |
| `report.py` | markdown report builder |
| `selector.py` | code / reuse / external decision engine |
| `audio_gen.py` | additive-synthesis score, foley, ambience |
| `assemble.py` | mux, loudnorm, fades, H.264/AAC export, preview |
| `qa.py` | black/freeze/motion/duration/loudness/caption gates |
| `project.py` | folder layout, bibles, continuity, manifest hashes |
| `library.py` | asset catalogue derived from cast/scenes/engine/voices/score, search, validation, reuse report |
| `storyboard.py` + `storyboard.mjs` | key-frame stills (one bundle, N stills) and the captioned contact sheet |
| `av_director.py` | authored beat sheet → the same render manifest, with scales, camera motives, sound cues and a carried actor ledger |
| `avqa.py` | structural creative audit (including `character_continuity`) and before/after comparison; subjective dimensions stay human |
| `voice.py` | voice plan and word timings; narration mode, LOCAL by default, ElevenLabs behind explicit authorisation, content-hashed cache, credit log |
| `kokoro_tts.py` | local Spanish takes, cache, timeline stem, optional shot fitting; never imports torch in the main process |
| `narration.py` | take/stem/mix RMS, one-voice and last-spoken-line coverage gates |
| `captions.py` | word timings from the voice plan → `shot.captions` in shot-local seconds, with stale-plan rejection |
| `mixdown.py` + `mixcheck.py` | deterministic NumPy mix: RMS voice envelope, attack/release ducking, linear limiter; voice-vs-bed measurement; "not applicable" without a speech stem |
| `identity.py` | canonical cast audit, per-shot override rejection, head/body proportion band |
| `providers/` | `base.py` (interfaces, CostGuard, JSONL log), `local.py`, `external.py`, `registry.py` |

### `studio/` — Remotion engine (TypeScript)

```
src/
  index.ts, Root.tsx            composition registration
  data/project.json             shots, camera, actors, captions (single source of truth)
  data/cast.json                character identities (shared with Python)
  engine/tokens.ts              palettes + measured rhythm constants
  engine/math.ts                easing, seeded PRNG, hashes
  engine/CameraRig.tsx          camera vocabulary + SVG parallax group
  engine/FilmFinish.tsx         grain, grade, vignette, halation
  engine/texture.tsx            procedural materials (stone, plank, shingle, snow, carpet, wallpaper, frost)
  engine/atmosphere.tsx         cast shadows, light shafts, fog, dust, glow, LightVeil, Cone
  engine/Subtitles.tsx          word-timed caption chunks (shot.captions) + fallback
  engine/Snow.tsx               deterministic particles
  characters/Character.tsx      the rig (pose, gait, blink, props)
  characters/cast.ts            cast loader (typed view of cast.json)
  composition/Actors.tsx        performance presets
  composition/CastSheet.tsx     cast sheet composition (identity check)
  composition/Demo.tsx          shot timeline, crossfades, assembly of the film
  scenes/*.tsx                  TownNight, Doorway, FaceCloseup, FieldDawn, BellInsert, Workshop
```

**Layering rule:** environment renders a set only; the *shot* owns the camera and
the actors. This is what allows the same set to be re-framed without redrawing it.

**SVG rule:** anything inside an `<svg>` must be SVG (`<g>`), never a `<div>`.
The first build silently dropped every parallax layer because of this; the code
now uses `ParallaxGroup`, and the actors have their own `<svg>` layer.

## 3. Data contracts

`studio/src/data/project.json`

```jsonc
{
  "id": "demo_002",
  "library": ["rig:default", "character:elder", "set:doorway", ...],  // ids reused from the catalogue
  "format": { "width": 1080, "height": 1920, "fps": 30 },
  "transitionFrames": 14,
  "shots": [{
    "id": "S01",
    "scene": "townNight",              // key into the environment registry
    "camera": "panLeft",               // CameraMove union
    "cameraIntensity": 0.8,            // 0.35..1.35; static uses 0
    "seconds": 8,    "line": "caption text",
    "captions": [{"text": "caption text", "start": 0.0, "end": 1.4}], // optional, shot-local seconds from the take
    "actors": [{"id": "elder", "preset": "walkIn", "x": 470, "y": 1690,
                 "scale": 1.5, "facing": 1, "from": -180, "to": 0,
                 "start": 0.06, "end": 0.86, "hold": "lantern",
                 "sequence": [{"preset": "walkIn", "start": 0.02, "end": 0.62},
                              {"preset": "turn", "start": 0.66, "end": 1.0}]}]
  }]
}
```

`studio/src/data/cast.json` — identity, proportions, palette, voice, wardrobe
states. Read by `cast.ts` **and** by `acs/project.py`; never duplicated.

## 4. Modes and spend control

- `Registry.select(capability)` filters by `MODE_RANK` and hard-skips every
  external provider when `mode == "local"`.
- `CostGuard.check(estimate, is_external=True)` raises `SpendNotAuthorized` when
  `authorize_spend` is false and `BudgetExceeded` past `budget_usd`.
- `OperationLog` writes JSONL to `projects/<id>/logs/generation_history.jsonl`
  for every registration, selection, request, result and failure.
- `ACS_MODE` can only *lower* the mode (env override), never raise it silently.

## 5. Extension points

| Goal | Do this |
|---|---|
| new scene | add `scenes/X.tsx` + register in `composition/Demo.tsx` + environment bible entry |
| new character | add an entry to `cast.json`; nothing else |
| new camera move | add to `CameraMove` + `transformFor` + the intent table in the style guide |
| new performance | add a branch in `Actors.perform` (pure function of frame + progress) |
| new paid capability | subclass `Provider` in `providers/external.py`, set `implemented=True` only after verifying the HTTP contract, add price + docs |
| new QA gate | add a check in `qa.py` returning `{id, pass, value, detail}` |
| new reusable asset | put it in the source of truth (cast/scenes/config) and run `studio.py assets rebuild`; hand-written extras go in `assets/registry.json` |
| new voice | add an entry to `config/voices.json` with its Voice ID, then `studio.py voice --provider elevenlabs --authorize-spend` |

## 6. Failure strategy

- Analysis, render, assemble and QA each fail loudly with the real tail of the
  FFmpeg/Remotion error; nothing is swallowed.
- The pipeline stops at the first hard failure (`produce`), but every stage can
  be re-run alone and resumes from the artefacts on disk.
- A missing tool (`FFmpeg`, `node_modules`) is reported as unavailable by the
  provider, not simulated.
- Sources are never overwritten: `assemble` refuses an output path equal to an
  input path.
