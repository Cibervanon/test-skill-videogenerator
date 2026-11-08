# Bug inventory

Only defects reproduced or proven from code and data are listed. Suspicions are
not promoted to bugs.

| ID | Severity | Description | Evidence | Root cause | Files | Fix | Test | Status |
|---|---|---|---|---|---|---|---|---|
| B-01 | High | `voicecheck` indexed `mix.wav` as if it were always 48 kHz | A mix at another rate is read past its end, reporting a silent voice window | Sample rate discarded (`mixed, _ = read_wav`) and `mix_sr = 48000` hard-coded | `scripts/acs/narration.py` | Read the rate returned by `read_wav`, use it for segments and duration | `tests/test_captions.py::NarrationSampleRateTests` (8 kHz mix) | **Fixed** |
| B-02 | Medium | `qa.caption_coverage` crashed on a shot without a `line` key | `shot["line"]` raises `KeyError`; generated manifests may omit the field | Direct indexing instead of optional access | `scripts/acs/qa.py` | `shot.get("line") or ""` | `CaptionCoverageTests::test_shot_without_a_line_key_does_not_crash_qa` | **Fixed** |
| B-03 | High (quality) | Burned-in captions ignored the take clock and distributed words by character weight | `buildCues` weighted chunks by string length; `words.json` was never read by the renderer | Missing data contract between `voice_plan.json` and the manifest | `captions.py` (new), `studio.py`, `Subtitles.tsx`, `Demo.tsx` | `captions` stage writes `shot.captions` in shot-local seconds; renderer consumes them, fallback retained | 8 tests; real manifest 23 cues; max reveal error **0 ms** (gate 120 ms); `tsc` 0 | **Fixed and structurally verified** |
| B-04 | Low (docs) | `LIMITATIONS.md` claimed ~500 frames/min and an 8–10 min film; the recorded render is 927 frames in 1464.45 s | 927 / 1464.45 × 60 = **38 frames/min** (0.63 fps) | Estimate never reconciled with the measured render | `LIMITATIONS.md` | Replaced with the measured figure and environment caveat | Documentation review | **Fixed** |
| B-05 | High (architectural) | Two concurrent renders can corrupt each other through the single active manifest | `use_manifest` writes `studio/src/data/project.json` then restores it | Process-global file used as render input | `scripts/studio.py` | File lock (`manifest_lock`, `ManifestBusy`) held for the whole command; second process fails in 5 s; locks older than 3 h are discarded | `test_a_second_render_fails_fast_instead_of_swapping_the_manifest` | **Fixed** |
| B-06 | Medium | The “two consecutive full renders” gate was unproven | Only one historical 1464.45 s render existed; no second run | Render cost (24 min) exceeds the session budget | `ROADMAP.md`, `studio.py render` | Added `render --frames`/`--out`; ran two 30-frame renders through the same path and compared decoded frames and audio | PSNR **53.12 dB**, SSIM **0.99696**, mean abs diff **0.39/255**; mix SHA-256 identical across regenerations | **Short gate PASS; full 927-frame double render still open** |
| B-07 | Low | QA threshold key was called `loudness_range_lufs` but the measurement is mean volume in dBFS | `audio.loudness` returns `mean_volume_db`; detail string admits it | Naming drift in the threshold map | `scripts/acs/qa.py`, `config/studio.config.json` | Added `loudness_band_db`; legacy key still accepted as an alias | Existing QA delivery test | **Fixed** |
| B-08 | Informational | `voicecheck` reports S01's take running 0.04 s past the next line | Report: “S01: take runs 0.04s past the next line; trimmed in the stem” | Shot windows overlap on dissolves by design | `kokoro_tts.build_stem` | Already trimmed with a 20 ms fade; warning is truthful | Existing narration tests | **By design** |
| B-09 | **Critical** | The delivered MP4 contained music and effects but **no narration**; `voicecheck` passed anyway | Old MP4 correlated **0.987** with the old mix but **0.0002** with `voice.wav`; per-line correlation ≈ 0.00; old mix peaked at 1.47 and was essentially amplified score. Synthetic tones reproduced it: voice/score ratio 0.001 | The FFmpeg graph reused the voice as `sidechaincompress` key **and** as an `amix` input, and referenced `[ducked]` twice; the mixed output carried no speech | `scripts/acs/mixdown.py`, `studio.py assemble`, `qa.py`, `narration.py` | Replaced the graph with a deterministic NumPy mixer: stems decoded to 48 kHz stereo, 20 ms RMS voice envelope with 10 ms hop, 20 ms attack / 250 ms release, attenuated score, voice summed, linear limiter at 0.89. `assemble` now prefers `mix.wav`; QA adds `voice_in_delivery`; `voicecheck` adds mix-vs-voice correlation and fails when the mix lacks the stem | `tests/test_audio_integrity.py` (7 tests: voice detection, score-only rejection, both stems present, `voicecheck` rejects score-only mix, soundtrack preference, manifest lock) | **Fixed; delivered MP4 re-assembled with voice** |

## B-09 verification detail

| Measurement | Old delivery | Current delivery |
|---|---|---|
| MP4 vs `voice.wav` correlation | 0.0002 | **0.9209** (`voice_in_delivery`) |
| Mix vs voice correlation | not measured | **0.8985** (`voicecheck`) |
| QA | PASS on a mix with no voice | **PASS 13/13**, including `voice_in_delivery` |
| Mix peak | 1.47 (clipped) | **0.844** |
| Deliverable | 30.933 s, no speech | 30.933 s, 17,279,149 bytes, AAC 48 kHz stereo, speech present |

Residual voice correlation after removing the bed is 0.9722; the bed is
attenuated to gain 0.12 while narration is active. The MP4 was re-assembled from
the existing picture, not re-rendered, so its burned-in captions are still from
the previous picture build.

## Confirmed non-bugs

- `use_manifest` restores the previous bytes after success and failure, and the
  restored file kept hash `2af5cfb4a38a5915` after a real storyboard render.
- `assemble` refusing a soundtrack shorter than the picture is intentional and
  overridable only with `--allow-short-audio`.
- Duplicate spoken text is a warning, not a failure: a refrain is legitimate.
- Exact per-pixel MD5 equality across two renders is not achievable here: Chrome
  re-rasterises the SVG grain filter with sub-pixel differences. The measured
  structural difference is 0.39/255 mean (PSNR 53.12 dB, SSIM 0.997), so the
  determinism gate is structural, not byte-exact.

## Reproduction commands

```bash
python -m pytest tests/test_audio_integrity.py -q
python -m pytest tests/test_captions.py -q
python scripts/studio.py mixdown --project projects/av_direccion_story --music-gain 0.20
python scripts/studio.py assemble --project projects/av_direccion_story
python scripts/studio.py voicecheck --project projects/av_direccion_story
python scripts/studio.py qa --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json
python scripts/studio.py render --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json --frames 0-29 --out .tmp/a.mp4
python scripts/studio.py render --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json --frames 0-29 --out .tmp/b.mp4
ffmpeg -i .tmp/a.mp4 -i .tmp/b.mp4 -lavfi "[0:v][1:v]psnr" -f null -
```
