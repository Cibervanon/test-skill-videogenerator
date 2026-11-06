# RESEARCH REPORT

Two kinds of findings, kept strictly apart: things **verified by execution** in
this folder, and things **read in documentation** (marked NO VERIFICADO where I
could not test them).

---

## 1. Environment (verified by execution)

Commands run and their output:

```
$ ffmpeg -version | head -1
ffmpeg version 9.0.2-full_build-www.gyan.dev
  --enable-libx264 --enable-libx265 --enable-libvpx --enable-libaom
  --enable-libass --enable-libfontconfig --enable-libfreetype
  --enable-libvmaf --enable-whisper (listed in ./configure flags)
$ python --version      → Python 3.14.7
$ node -v               → v24.21.0
$ npm -v                → 12.1.0
$ npx remotion --version → 4.0.540 (installed)
```

Capability matrix that follows from this (all **verified** unless stated):

| Capability | Available | Method | Constraints |
|---|---|---|---|
| Read video metadata | ✅ | `ffprobe -print_format json` | — |
| Extract frames | ✅ | `ffmpeg -ss … -frames:v 1` | exact-seek accuracy at keyframes varies |
| Detect cuts | ✅ | `select='gt(scene,T)'` + `metadata=print` | frame-difference metric, not semantics |
| Palette | ✅ | rgb24 decode + k-means (own code) | 48 px sampling, k=6 |
| Global motion | ✅ | SAD translation search (own code) | translation only, no zoom/rotation |
| Audio levels / envelope | ✅ | `volumedetect`, 8 kHz s16le decode | no LUFS without `loudnorm` |
| Loudness normalisation | ✅ | `loudnorm` filter | single pass here; two-pass is better |
| Encode H.264/AAC | ✅ | libx264 + aac | verified on the delivered MP4 |
| Render React/SVG to video | ✅ | Remotion 4.0.540 + headless Chromium | CPU-bound, ~500 frames/min at 1080×1920 |
| Synthesise audio | ✅ | Python stdlib (`wave`, `struct`) | additive/KS synthesis only |
| Speech-to-text | ❌ | — | `ffmpeg -filters` shows **no whisper filter** in this build despite the configure flag; no whisper.cpp/librosa installed |
| Object/face detection | ❌ | — | no OpenCV, no model runtime |
| Image/video/voice **generation** | ❌ | — | no verified adapter, no keys, explicitly not attempted |

---

## 2. Freebuff skill format (documentation)

A skill is a folder with `SKILL.md` carrying YAML frontmatter (`name`,
`description`) and a body of operating instructions, plus `references/`,
`scripts/`, `assets/` resources. This build follows that layout: `SKILL.md` at
the root, references in `references/`, runnable code in `scripts/` and `studio/`.

NO VERIFICADO: any loader-side limit on file size, reference depth or script
permissions — not observable from inside the workspace.

---

## 3. Remotion (documentation, partially verified)

Sources: <https://www.remotion.dev/docs/interpolate>,
<https://www.remotion.dev/docs/spring>,
<https://github.com/remotion-dev/skills> (official `remotion-best-practices` skill).

- Animation must be a pure function of `useCurrentFrame()`; CSS transitions and
  keyframes are not serialised by the renderer. **Applied**: every animated
  property in `studio/src/engine` derives from the frame.
- `interpolate()` / `spring()` are the intended easing primitives. **Applied**
  in spirit with own easing helpers (no spring dependency in this build).
- `<Sequence>` composes timelines; `Composition` declares fps/size/duration.
  **Verified**: the 1024-frame render was produced this way.
- Version installed: 4.0.540 (verified via `npx remotion --version`).

---

## 4. Generation landscape (third-party sources, NO VERIFICADO)

Read but not executed — no keys, no GPU, and the brief forbids spending:

- Open-source video model surveys: <https://ltx.io/blog/open-source-video-generation-models-guide>,
  <https://www.thundercompute.com/blog/best-open-source-ai-video-generation-models>,
  <https://www.turingpost.com/p/6-opensource-video-generation-models>,
  <https://fuser.studio/articles/best-open-source-video-models>.
  Reported consensus: Wan 2.2 strong quality but heavy VRAM (reportedly 65–80 GB
  at 720p), LTX-2.x runs on ~24 GB and adds audio, CogVideoX-1.5 is the lighter
  older option.
- FLUX: <https://github.com/black-forest-labs/flux> (weights/licence terms vary
  by variant — must be checked per variant before commercial use).
- ComfyUI as the local orchestration layer for diffusion workflows:
  <https://github.com/comfyanonymous/ComfyUI>.

**None of the above is wired in.** They appear in `MODEL_COMPARISON.md` with
"unverified" status so a later phase can adopt one behind the provider interface.

---

## 5. Techniques used (standard, verified by their output)

| Technique | Where | Evidence |
|---|---|---|
| k-means (Lloyd) on RGB samples | `acs/palette.py` | palettes in `references/measurements.json` |
| SAD block matching ±6 px | `acs/motion.py` | pan ratios reported per video |
| Karplus–Strong pluck + additive bell | `acs/audio_gen.py` | 34.13 s WAV, rms −18.8 dBFS |
| EBU R128 loudness normalisation | `acs/assemble.py` | `loudnorm` in the FFmpeg chain |
| Deterministic PRNG (mulberry32) for particles | `studio/src/engine/math.ts` | identical frames on re-render |
| Frame-difference / freeze / blackdetect gates | `acs/qa.py` | `final_quality_report.md` |

---

## 6. What the research changed

1. The measured cut density (0–1 hard cuts/min) contradicted the assumption of a
   fast-cut short. The demo therefore uses 5 long takes (6–9 s) with one camera
   move each, not 30 micro-shots.
2. The reference's quality comes from set density and light, not character
   detail — so effort went into parallax sets and light pools, and the rig was
   kept deliberately simple.
3. Because no speech-to-text is available locally, `transcript.json` is not
   produced; the pipeline reports that gap instead of inventing a transcript.
