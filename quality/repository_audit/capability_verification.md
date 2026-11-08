# Capability verification

Status vocabulary is deliberately narrow:

- **verified** — implementation exists, is exercised by a test and by a real
  artefact in this workspace;
- **partial** — works with a documented gap or only structural evidence;
- **adapter only** — interface exists, real provider never executed;
- **missing** — no code;
- **blocked** — the gate needs resources not available in this session.

| Capability | Documented | Implementation | Evidence in this audit | Verified status |
|---|---|---|---|---|
| `--manifest` selects the rendered film | yes | `studio.use_manifest` | real storyboard (10 stills, 54 s); active hash unchanged before/after | **verified** |
| Concurrent renders cannot swap the manifest | yes | `studio.manifest_lock` / `ManifestBusy` | second process fails in 5 s; lock test in `test_audio_integrity.py` | **verified** |
| Storyboard stills + contact sheet | yes | `acs/storyboard.py` | 10 PNGs + `storyboard.jpg` regenerated 2026-11-06 | **verified** |
| One narrator in narration mode | yes | `voice.speaker_of`, `narration.validate` | `voicecheck`: 8 lines, one `ef_dora`, 58 words, 23.09 s | **verified (signal, not ASR)** |
| Audio covers the last spoken line | yes | `narration.validate`, `assemble`, `qa.audio_duration` | QA `audio_duration` PASS, delta 0.000 s on 30.933 s | **verified** |
| Narration is actually present in the delivery | yes | `qa.voice_fit` / `voice_in_delivery` | MP4-vs-voice **0.9209**; score-only delivery rejected by test | **verified** |
| Mix contains the narration stem | yes | `narration.mix_voice_correlation` | mix-vs-voice **0.8985**; `voicecheck` fails on a score-only mix | **verified** |
| Ducking keeps score below the voice | yes | `mixdown.py` NumPy envelope mixer | **3 windows** within 3 dB at `music_gain=0.20`; bed gain 0.12 | **verified by measurement, not by ear** |
| Word-timed burned-in captions | previously “not timed” | `captions.py` + `Subtitles.tsx` + `shot.captions` | 23 cues, 0 ms reveal error vs plan, 8 tests, `tsc` 0, storyboard renders | **partial** — chunk-level, predicted timings, final MP4 not re-rendered |
| SRT from real take timings | yes | `acs/subtitles.py` | existing `preproduction/subtitles.srt`; no regeneration needed | **verified structurally** |
| Kokoro local Spanish TTS | yes | `kokoro_tts.py`, cached takes | 8 cached takes; no model run in this session | **verified from artefacts**, not re-synthesised |
| Kokoro word timings | yes, predicted | `kokoro_worker.words_from_pred` | `source: pred_dur` in every word | **partial** — not forced alignment |
| Procedural score and foley | yes | `acs/audio_gen.py` | score present; QA loudness −16.9 dB after mastering | **verified** |
| Character identity audit | yes, structural | `acs/identity.py` | cast + manifest audit; 3 canonical characters | **partial** — no pixels/face embedding |
| Canonical cast shared Python/TS | yes | `cast.json` | same file consumed by `cast.ts` and `identity`/`overlays` | **verified** |
| One catalogue with validation | yes | `library.py`, `catalog.json` | exercised by the **174-test** suite | **verified** |
| Asset forge (SVG, not images) | yes | `asset_forge.py` | forge tests in suite; no new forge run | **verified structurally** |
| AV beat planning + creative QA | yes | `av_director.py`, `avqa.py` | tests; existing `av_audit` artefacts | **verified structurally** |
| UI modes A–F and placement | yes | `ui_director.py`, `overlays.py` | tests in suite | **verified structurally** |
| Two consecutive **short** renders are structurally identical | new | `render --frames` / `--out` | 30 frames × 2: PSNR **53.12 dB**, SSIM **0.99696**, mix SHA identical | **verified structurally** |
| Two consecutive **full** provider renders | open | `providers/local.py` | only one historical 1464.45 s render; short gate passed | **blocked** |
| ElevenLabs narration | adapter only | `providers/external.py`, `voice.py` | never executed; spend gate intact | **adapter only** |
| Lip-sync / visemes | missing | — | mouth is a parametric shape | **missing** |
| ASR / transcript | missing | — | `LIMITATIONS.md` §2 | **missing** |
| Other aspect ratios | missing | — | forged assets reject non-9:16 | **missing** |
| CIEDE2000 style distance | missing | palette RGB distance only | — | **missing** |

## Documentation corrections made

- `README.md`: test count 159 → **174**; caption and audio stages added to the
  story pipeline; delivery evidence updated to QA 13/13 and 3 mix windows.
- `CAPABILITY_MATRIX.md`: burned-in captions moved from “shot-synced, not timed”
  to chunk-timed; mixdown described as the NumPy envelope mixer; lock and
  delivery-voice rows added.
- `LIMITATIONS.md`: caption gap rewritten; render-speed claim replaced with the
  measured 38 frames/min; mix peak and voice-correlation limits documented.
- `ROADMAP.md`: caption gate closed; Stage 0 updated with the lock and the short
  determinism gate.
- `CHANGELOG.md`: 0.10.3 records the critical audio defect, the lock and the
  render flags.

## What remains unproven

- That the rendered pixels show the exact chunk at the exact frame. The data is
  exact and the renderer compiles and renders, but there is no OCR or frame-diff
  assertion in this pass.
- That Kokoro's predicted word boundaries match the acoustic signal; no ASR.
- That identity is perceptually stable; only the rig data and the audit are
  verified.
- That two full-length renders match; only two 30-frame slices were compared.
