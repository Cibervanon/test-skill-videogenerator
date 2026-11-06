# INSTALLATION

## 1. Requirements

| Requirement | Version used here | Needed for |
|---|---|---|
| Python | 3.14.7 (3.11+ works, stdlib only) | pipeline, analysis, audio synthesis, edit, QA |
| Node.js | 24.21.0 | Remotion studio + render |
| npm | 12.1.0 | dependencies |
| FFmpeg + FFprobe | 9.0.2 (libx264, aac, loudnorm) | analysis, assembly, QA |
| Chromium | downloaded by Remotion on first render | headless rendering |

No Python packages are required. No API key is required in LOCAL mode.

## 2. Verify the environment

```bash
python --version
node -v
ffmpeg -version | head -1
ffprobe -version | head -1
```

Then:

```bash
python scripts/studio.py status
```

This prints the active mode, the provider matrix with availability and reasons,
the budget, and the detected FFmpeg paths. If FFmpeg is missing you get an
explicit error, not a silent empty analysis.

## 3. Install the render engine

```bash
cd studio
npm install
```

`npm install` must complete without blocking esbuild's postinstall script — on
npm 12 you may need:

```bash
npm install-scripts approve esbuild
cd .. && cd studio && npm install
```

First render downloads a headless Chromium build (~150 MB) into the Remotion
cache. That download is the only network access the LOCAL pipeline performs.

## 4. Smoke test

```bash
# type-check the engine
cd studio && npx tsc --noEmit && cd ..

# render a single frame (fast, proves bundling + Chromium)
cd studio && npx remotion still src/index.ts CinematicDemo ../projects/demo_001/output/still_000.png --frame=0 && cd ..

# unit tests (no browser, no network)
python -m unittest discover -s tests -v
```

## 5. Produce the demo film

```bash
python scripts/studio.py audio    --project projects/demo_001
python scripts/studio.py render   --project projects/demo_001
python scripts/studio.py assemble --project projects/demo_001
python scripts/studio.py qa       --project projects/demo_001
```

Output: `projects/demo_001/output/final_video.mp4` (+ `_preview.mp4`).

## 6. Optional external providers (HYBRID / PREMIUM)

Nothing here is enabled by default, and no adapter ships verified.

1. Obtain the key from the provider (see `MODEL_COMPARISON.md` for options).
2. Export it in the environment, never in the repo:
   - `FLUX_API_KEY`, `VIDEO_API_KEY`, `TTS_API_KEY` (names expected by `providers/external.py`)
3. Implement + verify the HTTP contract in `scripts/acs/providers/external.py`
   and set `implemented = True`.
4. Ask the user for a budget, set `generation.authorize_spend: true` and
   `generation.budget_usd` in `config/studio.config.json`.

Until step 3 is done, every external provider reports *"adapter not implemented
in this build"* — by design.

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `FFmpeg/FFprobe not found in PATH` | install FFmpeg and reopen the shell |
| `studio dependencies not installed` | run `npm install` in `studio/` |
| Remotion hangs on first render | it is downloading Chromium; check network/proxy |
| render is slow | 1080×1920 SVG frames are CPU-bound: lower `--concurrency`, or render at 608×1080 |
| `refusing to overwrite an input file` | choose a different output path |
| QA fails on `duration` | render and soundtrack disagree: re-run `audio`, then `assemble` |
