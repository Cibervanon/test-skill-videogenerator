# Kokoro local TTS — integration record

Kokoro runs on this machine, in Spanish, with no API key, no credits and no audio
leaving the computer. This file records the audit, the decisions, what was
measured and what is still weak. Demo: `projects/kokoro_demo/`.

## 1. Audit of the existing voice path

| Piece | Before this change | Where |
| --- | --- | --- |
| Provider registry | `local` (timings only) and `elevenlabs` (gated) | `scripts/acs/voice.py` |
| Voice identity | `config/voices.json`, one entry per character, `voice_id: null` | `config/voices.json` |
| Cache | SHA-1 of (text, voice id, settings) → `assets/voice_cache/*.mp3` | `voice.py` |
| Timestamps | LOCAL: estimated from words/second; ElevenLabs: character alignment | `voice.py` |
| Cut | Shot clock; `scripts/acs/edit.py` aligns boundaries to word times | `edit.py` |
| Subtitles | Caption plan derived from shot lines | `qa.py`, `edit.caption_cues` |
| Mixing | Score only; `mixcheck.py` reports "not applicable" without a voice stem | `mixcheck.py` |
| Cost | `generation/voice/costs.json`, credits counted per character | `voice.py` |
| CLI | `studio.py voice --provider local\|elevenlabs` | `studio.py` |

Two things made the integration small: the voice stage already wrote a
provider-agnostic `voice_plan.json` with per-word records, and `edit.py` already
consumed global word times.

## 2. What Kokoro offers (official repo, cloned to `.tmp/research/kokoro`)

- Model **Kokoro-82M v1.0**, StyleTTS2 + ISTFTNet, **Apache-2.0** weights and code
  (repo `LICENSE` is Apache-2.0; the model card says "Apache-licensed weights").
- Python package `kokoro 0.9.4`, `requires-python >=3.10,<3.14`, depends on
  `torch`, `transformers`, `misaki[en]`, `huggingface_hub`, `soundfile`.
- Languages: `a` en-US, `b` en-GB, **`e` Spanish**, `f` French, `h` Hindi,
  `i` Italian, `j` Japanese, `p` pt-BR, `z` Mandarin.
- Spanish voices: **`ef_dora` (female), `em_alex` (male), `em_santa` (male)** —
  three, and that is the whole Spanish cast.
- Spanish G2P goes through **espeak-ng** (`misaki.espeak.EspeakG2P`), not a
  learned Spanish G2P. This matters: numbers, acronyms and proper nouns depend on
  espeak's Spanish rules, and the model inherits espeak's mistakes.
- The pipeline exposes **`pred_dur`**, one predicted duration per phoneme
  (600-sample frames at 24 kHz → 40 frames a second). `KPipeline.join_timestamps`
  only fills word timestamps for English (`lang_code in 'ab'`); for Spanish the
  tokens are `None`, so the integration does the grouping itself.
- No word-level alignment is shipped for non-English. There is no forced
  alignment in the package.

## 3. Decisions

1. **Separate interpreter, one process boundary.** torch has no Python 3.14
   wheels (the skill's default interpreter is 3.14.7), so Kokoro lives in
   `.venv-kokoro` (Python 3.12). `scripts/acs/kokoro_worker.py` runs there and
   talks JSON; the main pipeline never imports torch. Consequence: the skill's
   environment stays clean, and the provider is installable/uninstallable alone.
2. **Provider, not a second pipeline.** `studio.py voice --provider kokoro`
   writes the same `voice_plan.json`/`words.json` the other providers write, and
   the same `edit.py`, `subtitles`, `mixdown` and `assemble` stages consume it.
3. **Word timings from `pred_dur`, labelled as such.** Per-phoneme durations are
   grouped by the spaces espeak emits and normalised to the length of the audio
   the model actually produced. Every record carries `"source": "pred_dur"`; if
   phoneme and word counts disagree the worker falls back to syllable-weighted
   distribution and says `"source": "syllables"`. Nothing claims to be an ASR
   alignment.
4. **Cache keyed on everything that changes the take**: provider, model id,
   voice, language, speed, config version, text. Takes are reused across projects
   (`assets/voice_cache/kokoro/`), so a character keeps its voice between films.
5. **Downloads are explicit.** `--allow-model-download` is required unless the
   weights and that voice are already on disk (`studio.py kokoro` shows which).
   Models live in `.models/kokoro` (HF layout), outside git.
6. **The voice can move the cut.** `kokoro_tts.fit_shots()` and
   `studio.py voice --fit-shots` stretch only shots whose line overflows, and
   write `preproduction/manifest_fitted.json`; the active manifest is never
   rewritten silently.
7. **Music is ducked by the voice**, not by a static gain: `mixdown.py` runs
   `sidechaincompress` keyed on the voice and writes both the sum (`mix.wav`) and
   the ducked bed (`music_ducked.wav`). `mixcheck.py` now measures the voice
   against the ducked bed — measuring it against the final mix would compare the
   voice with itself and flag every window.

## 4. Installation (reproducible, isolated)

```bash
# Python 3.12 is required: kokoro declares <3.14
"C:/Users/W10/AppData/Local/Programs/Python/Python312/python.exe" -m venv .venv-kokoro
.venv-kokoro/Scripts/python.exe -m pip install "kokoro>=0.9.4" soundfile espeakng-loader

python scripts/studio.py kokoro          # runtime, torch, device, per-voice weights
python scripts/studio.py voice --project projects/kokoro_demo \
  --manifest projects/kokoro_demo/manifest.json --provider kokoro --allow-model-download
```

- `espeakng-loader` supplies the espeak-ng library on Windows; no system
  installer or service is started.
- Hardware: CPU-only here (no CUDA device). The worker honours `device` in
  `config/kokoro.json` (`cpu`); on a CUDA machine, set `"device": "cuda"`.
- Footprint on this machine: `.venv-kokoro` 1.2 GB, weights + voices 313 MB.
- Nothing in this integration calls a commercial API. `ELEVENLABS_API_KEY` is not
  needed and was not set for any of these runs.

## 5. Configuration surface

`config/kokoro.json`: provider, interpreter, repo id, model id, models dir, cache
dir, `lang_code` (`e` = Spanish), sample rate, device, `authorize_download`,
alignment strategy, per-character voice + speed. Character casting:

| Character | Kokoro voice | Speed | Why |
| --- | --- | --- | --- |
| narrator | `ef_dora` | 0.98 | the only female Spanish voice; neutral read |
| elder | `em_alex` | 0.92 | lower and slower |
| young | `em_santa` | 1.05 | brighter, faster |

Three voices is the model's limit; casting is voice + speed, not timbre range.

## 6. Measured on this machine (CPU)

| Metric | Value |
| --- | --- |
| Spanish lines generated | 4 (34 words) |
| Audio per line | 4.00 s / 3.60 s / 3.18 s / 1.85 s |
| Synthesis speed | 1.6× realtime (4.0 s of audio in 6.5 s), plus ~3 s model load per call |
| Sample rate | 24 kHz mono, PCM_16 |
| Alignment | `pred_dur`, 100 % of words (no syllable fallback) |
| Stem | `generation/voice/voice.wav`, peak-normalised to −1.5 dBFS |
| Mix | `generation/audio/mix.wav`, sidechain duck, 8 windows within 3 dB of the voice (was 53 before ducking) |
| Cost | **0 credits, 0 USD** |

## 7. What is honestly weak

- **Spanish quality is "fair", not "excellent".** Kokoro's own voice grades put
  the Spanish voices at the low end of the model's range; pronunciation is
  espeak-driven, so proper nouns and numbers can come out castilianised or
  wrong. No Spanish voice was trained as a narrator.
- **Timing is predicted, not measured.** `pred_dur` is the duration predictor's
  opinion. It tracks the audio closely (normalised to the real clip length), but
  it is not forced alignment; a word boundary can be off by tens of
  milliseconds.
- **1.6× realtime on CPU** — a 5-minute narration takes ~8 minutes. No GPU here
  to compare.
- **No lip-sync.** The rig has no phoneme shapes; the voice is narration over the
  shot.
- **No comparison with ElevenLabs was run**, because that would spend credits.
  Claiming Kokoro sounds better or worse would be unfounded; what is measured is
  that Kokoro works offline, for free, in Spanish, with usable timings.
- **Licences:** Kokoro code and weights Apache-2.0; `espeak-ng` (bundled by
  `espeakng-loader`) is **GPL-3.0** and is invoked as a separate phonemiser
  process — fine for local use, a distribution consideration if the skill is
  ever shipped as a binary bundle.

## 8. Narration validation (0.8.0)

`studio.py voicecheck` reads the plan, every cached take, the timeline stem and
`mix.wav`, and writes `quality/narration_validation.{json,md}`. It checks that
each line has a WAV, that the stem and the mix are audible inside that line's
window, that the starts are ordered, that no text is duplicated, and that no take
peaks at full scale. Result on `ui_direccion`: 8 lines, 58 words, 23.34 s of
speech, 0 problems.

The stem used to sum overlapping windows at S01/S02 and S03/S04 (0.16 s each)
because shot windows overlap on dissolves. `build_stem` now ends a line at the
next line's start and applies a 20 ms fade; the plan reports the trim and the
words keep their original take timings. This is not a crossfade between two
speakers, it is one narrator stopping before the next line starts.

The mix chain now limits at 0.89 with a 1 ms attack, `level=false` and a 0.9
output gain, instead of auto-levelling to 0 dBFS. The delivery is still
normalised to −16 LUFS / −1.5 dBTP by `assemble`.

## 9. Verification performed

- `python -m unittest discover -s tests` — see `TEST_REPORT.md` §9 (unit tests
  with mocks/fixtures; they never synthesise).
- Real generation: `projects/kokoro_demo/generation/voice/*.wav` (cached takes,
  hash-named) and `voice.wav` timeline.
- `projects/kokoro_demo/preproduction/subtitles.srt`: 12 cues on real word times.
- `projects/kokoro_demo/generation/audio/mix.wav` + `narracion_es.m4a` (AAC 192k).
- `projects/kokoro_demo/preproduction/mix_check.md`: flags after ducking.
- `python scripts/studio.py assets validate` still 30/30; no previous render was
  touched (`demo_001`, `demo_002`, `demo_003` outputs unchanged).
