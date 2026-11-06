# ATTRIBUTION

This project contains code and design ideas adapted from third-party work.
Nothing here is copied wholesale; each item says what was taken and what was
rewritten.

## what-if-animation

- Source: <https://github.com/kelano86/what-if-animation>
- Copyright (c) 2026 FreshStack
- Licence: MIT

```
MIT License

Copyright (c) 2026 FreshStack

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### What was taken

| File here | Origin | What changed |
|---|---|---|
| `scripts/acs/storyboard.mjs` | `scripts/stills.mjs` | rewritten for this project's single composition, a JSON frame list instead of episode files, ESM top-level await, scale default |
| `scripts/acs/storyboard.py` | `scripts/board.py` | rewritten: key frames computed from `project.json`, Pillow layout, project-local output paths |
| `studio/src/composition/CastSheet.tsx` | `studio/src/CastSheet.tsx` | rewritten for this rig and cast; layout and labels are new |
| `studio/src/engine/atmosphere.tsx` (`LightVeil`, `Cone`) | `studio/src/engine/light.tsx` | reimplemented with this project's palette and API |
| `studio/src/engine/math.ts` (`backOut`, `settle`, `kf`, `easeInCubic`) | `studio/src/engine/anim.ts` | same maths, retyped and documented here |
| `scripts/acs/voice.py` | `scripts/voice.py` | rewritten: one provider interface, explicit authorisation, local timing provider, no pause-trimming yet |
| `scripts/acs/mixcheck.py` | `scripts/mixcheck.py` | rewritten to report "not applicable" when there is no speech stem |
| `scripts/acs/assemble.py` (two-pass loudnorm) | `scripts/master.py` | adapted into the existing assemble step, keeping fades and trim |

### What was not taken

- Their characters (Pip, Mo, the sister, the mother, the man in the suit), their
  stories and their episode scripts.
- Their 40 MP3 sound effects in `studio/library/sfx/`: generated on their
  ElevenLabs account, so they are not redistributed here. This project synthesises
  its own score and effects in `scripts/acs/audio_gen.py`.
- Their Google Fonts setup: this project renders without remote fonts.
- Their room-perspective engine and segment/power-look system (see
  `REPOSITORY_COMPARISON.md` for why).

## Everything else

All sets, characters, scripts, score, captions, tests and documentation in this
repository are original to AI CINEMATIC STUDIO.

## Kokoro TTS (local voice)

- **Kokoro-82M** — model weights and inference code, © hexgrad, **Apache-2.0**
  (https://github.com/hexgrad/kokoro, https://huggingface.co/hexgrad/Kokoro-82M).
  Used unmodified through the official `kokoro` Python package, in `.venv-kokoro`.
- **misaki** 0.9.4 — G2P library used by Kokoro, **Apache-2.0**.
- **espeak-ng** — Spanish phonemisation, **GPL-3.0**, delivered by the
  `espeakng-loader` wheel and invoked as a separate process; no espeak code is
  linked into this project.
- **PyTorch** 2.15.0 — **BSD-3-Clause** and bundled third-party licences.
- **soundfile / libsndfile** — **BSD-3-Clause**.
- Voices used: `ef_dora`, `em_alex`, `em_santa` (Spanish, part of Kokoro-82M v1.0).
