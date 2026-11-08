# Remaining issues

## Fixed in this pass

| ID | Issue | Evidence |
|---|---|---|
| B-09 | Mix dropped narration; delivery had no voice | MP4-vs-voice **0.9209**, QA 13/13, 7 audio tests |
| B-05 | Concurrent renders raced on the active manifest | fail-fast file lock; second render raises `ManifestBusy` in 5 s |
| B-07 | `loudness_range_lufs` measured mean dBFS | `loudness_band_db` with a legacy alias |

## Open defects

| ID | Severity | Issue | Why it matters | Smallest next step |
|---|---|---|---|---|
| B-06 | Medium | Two consecutive **full** renders still not run | The reproducibility gate is only proven on 30-frame slices | Run two full 927-frame renders on an idle machine; compare PSNR/SSIM and audio hashes |
| — | Low | Exact pixel MD5 differs between renders | Chrome re-rasterises the SVG grain filter; byte-identity is not achievable here | Keep the structural gate (PSNR ≥ 50 dB, SSIM ≥ 0.995); optionally cache the grain as a pre-rasterised plate |

## Unverified features

- Caption pixels: the data and the renderer agree, but no OCR/frame-diff asserts
  which chunk is visible at which frame.
- Kokoro word boundaries: `pred_dur`, not forced alignment; no ASR.
- Identity beyond structure: no face embedding, no pixel comparison.
- Style distance: RGB palette distance, not CIEDE2000.
- ElevenLabs: adapter never executed.
- Asset forge: not regenerated in this pass; covered by tests.
- Mix intelligibility: correlation proves the voice is present, not that every
  word is understandable; listening is still required.

## Blocked

- Two full renders (24 min each, session budget).
- Any paid provider comparison (spend not authorised).

## Human review still required

- Narrative, acting, rhythm and style integrity of
  `projects/av_direccion_story`.
- Whether the new chunk boundaries read well (typography and reading speed).
- Whether the corrected mix is comfortable to listen to; the gates prove signal,
  not taste.

## Architectural limitations

- One body rig; `silhouette` is descriptive, not geometry.
- 2.5D camera, one authored perspective set; no lens model.
- Preset grips, no IK; prop contact is not tracked.
- UI boxes resolved once per shot; no per-frame reflow.
- Five hand-built sets; no set generator.
- No lip-sync, no multi-aspect output.
- The active manifest is still a swapped global file. The lock makes concurrent
  commands safe (one fails), but it does not enable parallel renders; a
  render-scoped manifest remains the better long-term design.

## Work that needs new assets or assets redesign

- Per-style drawing packs (same silhouettes today).
- Foreground occluders and denser sets.
- Distinct body silhouettes per recurring character.
- Prop atlas with contact points for hand attachment.

## Work that needs a redesign, not a patch

- Concurrent/multi-project rendering (manifest is a file-level global).
- True 3D or lens-based camera.
- Word-level caption emphasis and lip-sync (both need an alignment/viseme
  track, not a renderer tweak).
