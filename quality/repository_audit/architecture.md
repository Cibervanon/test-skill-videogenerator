# Repository architecture audit

Audited on 2026-11-06 against the working tree at commit `5eaec1e`, not against
the README. The repository is a single pipeline with one Remotion composition,
one manifest contract and one asset catalogue.

## 1. Entry points

| Entry point | Path | Role |
|---|---|---|
| Pipeline CLI | `scripts/studio.py` | every stage: analysis, preproduction, audio, voice, mixdown, render, assemble, qa, inspect, evaluate, identity |
| Remotion entry | `studio/src/index.ts` → `Root.tsx` | registers `CinematicDemo`, `CastSheet`, `IdentitySheet` |
| Active manifest | `studio/src/data/project.json` | the file Remotion imports at bundle time |
| Project manifest | `projects/<id>/manifest.json` | the delivery copy; activated for the duration of a render by `studio.use_manifest` |
| Voice plan | `projects/<id>/generation/voice/voice_plan.json` | real take paths, word timings and durations |

## 2. Actual pipeline

```
studio.py <command>
  ├─ project loading (manifest + cast.json merged with generated cast)
  ├─ preproduction  → script/storyboard/bibles/continuity
  ├─ audio          → procedural score (no network)
  ├─ voice          → Kokoro takes + voice_plan.json + words.json + SRT
  ├─ captions       → shot.captions (word-timed, shot-local seconds)
  ├─ mixdown        → score + stem, RMS-envelope ducking → mix.wav
  ├─ render         → activate --manifest, npx remotion render, restore bytes
  ├─ assemble       → FFmpeg mux, two-pass linear loudnorm, preview
  └─ qa/inspect/evaluate/avqa/identity → reports in quality/
```

The renderer is a pure function of the manifest: `Demo.shotTimeline` builds the
shot clock, `ShotView` renders the set, actors, overlays and captions, and
`FilmFinish` applies grain/vignette over the whole composition.

## 3. Source-of-truth map

| Domain | Canonical source | Consumers |
|---|---|---|
| Film structure, camera, actors, lines | `projects/<id>/manifest.json` | Python stages and Remotion |
| Character identity | `studio/src/data/cast.json` | `characters/cast.ts`, `acs/project.py`, `acs/identity.py` |
| Asset metadata | `assets/catalog.json`, derived from cast/scenes/config by `library.build` | `library.compose`, `assets` CLI |
| Hand-written asset extras | `assets/registry.json` | `library.build` |
| Word timings / takes | `generation/voice/voice_plan.json` | `captions`, `subtitles`, `voicecheck`, `edit` |
| Caption reveal windows | `shot.captions` in the manifest | `engine/Subtitles.tsx` |
| Style tokens | `studio/src/data/styles.json`, `engine/tokens.ts` | every scene and overlay |

## 4. Duplicate implementations and coupling

- **Shot clock in two languages.** `edit.shot_windows` and
  `Demo.shotTimeline` implement the same overlap rule (`cursor += frames −
  transitionIn`). `captions.attach` reuses the Python one; the story was checked
  line by line and the eight spoken lines start at exactly the same timestamps
  (delta 0.000 s). The duplication is still a risk: no automated cross-language
  test would catch a change to only one side.
- **Rig geometry mirrored in Python.** `identity.py` hard-codes
  `RIG_BODY_HEIGHT_PX = 170.0` to compute head/body without importing TSX.
  A change to `characters/geometry.ts` would silently change the meaning of the
  audit band.
- **Scene registry in two places.** `Demo.tsx` maps the five hand-built scenes;
  `generated_assets.json` supplies forged sets. An unknown key throws at render
  time, which is the correct failure mode.
- **UI placement logic** lives in `motion-graphics/layout.ts` and is mirrored in
  `acs/overlays.py` for the Python solver. The two are exercised by tests but
  not proven pixel-identical.

## 5. Risk areas

1. **The active manifest is still a global swap, now serialised by a lock.**
   `use_manifest` writes `studio/src/data/project.json`, runs the child renderer
   and restores the previous bytes in `finally`. `manifest_lock` holds a lock
   file for the whole command; a second process raises `ManifestBusy` in 5 s
   instead of racing. This makes concurrent commands safe, not parallel.
2. **Caption coverage is measured from the plan, not from pixels.** No OCR; the
   renderer can still drop or clip a cue without QA noticing.
3. **Full render cost.** 927 frames took 1464.45 s on this machine (≈0.63 fps).
   Two 30-frame slices match structurally (PSNR 53.12 dB, SSIM 0.99696), but the
   two-consecutive-**full**-renders gate could not be completed in this session.
   Exact pixel MD5 is not stable because Chrome re-rasterises the SVG grain.
4. **Subjective quality is not measured.** Identity, acting, rhythm and style
   remain human dimensions; the audit does not score them.
5. **No ASR and no forced alignment.** Word timings come from Kokoro `pred_dur`;
   a timing can be tens of milliseconds off the acoustic word even though the
   manifest and renderer agree exactly.

## 6. Unverified or blocked capabilities

- Two consecutive **full** provider renders (blocked by cost/time; the 30-frame
  structural gate passes and one historical full render is documented).
- ElevenLabs narration (adapter only, never executed; requires spend).
- Face-embedding identity and CIEDE2000 style distance (not implemented).
- Lip-sync/visemes (not implemented).
- Per-frame UI reflow (boxes resolved once per shot).
- Word-level caption emphasis (chunk timings exist; emphasis does not).
