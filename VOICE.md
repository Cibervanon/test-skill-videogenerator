# VOICE — narration and dialogue (ElevenLabs-ready, off by default)

LOCAL mode is the default and **never** calls a provider: it writes the timing
plan only. Nothing in this repository spends credits unless you say so twice
(`authorize_spend` in the config *and* `--authorize-spend` on the command).

## What exists today

```
shot.lines ──► scripts/acs/voice.py ──► generation/voice/voice_plan.json
                                    └─► generation/voice/words.json   (word timings)
```

```bash
python scripts/studio.py voice --project projects/demo_002
# provider=local speech=False lines=5 words=47
```

`voice_plan.json` gives, per shot: the speaker, the text, the shot window in
seconds, and word-level start/end times estimated at 2.45 words/s and compressed
to fit the shot. `estimated: true` marks them as derived, not measured.

`mixcheck` reports "not applicable" while there is no speech stem. That is
deliberate: a gate that cannot run must not report a pass.

## Turning on ElevenLabs (when you decide to)

1. Choose a voice in your ElevenLabs account and copy its **Voice ID**. Nothing
   here invents one: `config/voices.json` ships with `voice_id: null`.
2. Paste it into `config/voices.json` for the character (`narrator`, `elder`,
   `young`), then set `"authorize_spend": true`.
3. Put the key in the environment, never in a file that is committed:

   ```bash
   export ELEVENLABS_API_KEY=...      # Windows PowerShell: $env:ELEVENLABS_API_KEY="..."
   ```

4. Ask for a take, explicitly:

   ```bash
   python scripts/studio.py voice --project projects/demo_002 --provider elevenlabs --authorize-spend
   ```

Before the request is built, the command prints nothing but the plan; the module
raises `VoiceError` if the Voice ID, the key or the authorisation is missing. It
never makes a partial call.

### Cost

ElevenLabs bills characters: a 356-character take is ~78 credits (measured on
the reference project by its author). This module logs what it spent in
`generation/voice/costs.json` and prints the total. It cannot know your plan, so
it does not estimate money — only credits.

### Caching

Takes are cached by `sha1(text, voice_id, settings)` in `assets/voice_cache/`.
Re-running to retune pauses is free; changing a word is not. This is the same
trick the external repository uses, and the reason its second run cost less.

## What is NOT implemented (say it, don't fake it)

- **No lip-sync.** The rig has no mouth shapes driven by phonemes. Dialogue is
  narration over the shot, and the mouth keeps its acting curve.
- **No pause trimming.** The external repo cuts silence between words to hit the
  genre's pace (`gaps` in its `episode.json`). Here the score still owns the
  pacing; trimming arrives with the first real take.
- **Word-cued edit is implemented but has no take to follow.** `scripts/acs/edit.py`
  aligns shot boundaries to `words.json` (and `studio.py edit` reports the drift),
  so the timings are already wired into the cut; what is missing is real speech,
  because LOCAL mode writes timings only. The external repo's `plan.py` cuts on
  spoken words. Our edit is authored per shot.

## Why the score stays

`audio_gen.py` synthesises a deterministic score (bell, footsteps, wind, digging)
at zero cost and zero latency. It is the reason a LOCAL render is a complete
film. When a real voice exists, `mixcheck` keeps the score under it and
`assemble` masters the sum to −14 LUFS.

## Kokoro (local, Spanish)

Kokoro runs in an isolated interpreter because torch has no Python 3.14 wheels:

```bash
python -m venv .venv-kokoro                                  # Python 3.12
.venv-kokoro/Scripts/python.exe -m pip install "kokoro>=0.9.4" soundfile espeakng-loader
python scripts/studio.py kokoro                              # runtime + which weights are on disk
python scripts/studio.py voice --project projects/kokoro_demo \
  --manifest projects/kokoro_demo/manifest.json --provider kokoro --allow-model-download
python scripts/studio.py subtitles --project projects/kokoro_demo
python scripts/studio.py mixdown --project projects/kokoro_demo
```

- Casting lives in `config/kokoro.json` (`ef_dora`, `em_alex`, `em_santa`), with a
  per-character speed.
- Weights go to `.models/kokoro` (gitignored) and are only fetched with
  `--allow-model-download`; `studio.py kokoro` says which voice is missing.
- Word times are grouped from the model's `pred_dur` and written on the film clock,
  so `edit.py`, `subtitles.py` and `mixdown.py` work unchanged.
- Cache: `assets/voice_cache/kokoro/<hash>.wav` + `.json`, keyed on text, voice,
  model, language, speed and config version — a character keeps its voice between
  films and identical lines are never regenerated.
- If a line is longer than its shot, `voice --fit-shots` writes
  `preproduction/manifest_fitted.json` instead of silently retiming the film.
- No key, no credits, no network at synthesis time. ElevenLabs stays gated exactly
  as before.
