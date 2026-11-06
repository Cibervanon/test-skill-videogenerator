---
name: ai-cinematic-studio
description: Deterministic, code-first cinematic animation studio. Turns a reference video plus one instruction into a vertical short film produced entirely in code (Remotion/React/SVG/CSS/FFmpeg/Python), with optional, budget-gated external generation in HYBRID/PREMIUM mode. Use for storyboard-driven animated shorts, style-matched recreations, procedural soundtracks, automated editing and quality gates.
---

# AI CINEMATIC STUDIO

A production system, not a prompt. Everything below is either implemented and
runnable in this folder, or explicitly marked as unavailable.

- **Default mode: LOCAL.** No key, no credit, no network call. The renderer is code.
- **External generation is opt-in, budgeted and logged.** It can never be triggered
  by a config typo: `LOCAL` refuses external providers in code (`providers/registry.py`).
- **Nothing claims to be generated when it is not.** Stubbed adapters raise
  `ProviderUnavailable`; they never return placeholder "generated" media.
- **Five visual styles over one engine** (`studio/src/data/styles.json`), a
  13-type motion-graphics/UI layer (`studio/src/motion-graphics/`), a structured
  feedback memory (`scripts/acs/feedback.py`) and a rule-based director
  (`studio.py direct`) that turns a title into a plan — then flags its own
  template narration as needing approval.
- **UI is directed per shot** (`scripts/acs/ui_director.py`): modes A–F,
  adaptive placement that avoids faces/bodies/captions, reading-time windows and
  an escalation path (B → D → E) when there is no free zone. The renderer draws
  the decision; `uiqa` audits it and samples the real MP4. See `UI_DIRECTION.md`.

## When to use this skill

Use it when the user wants:

- a vertical (9:16) or landscape animated short built from code;
- a reference video re-created with original characters and script;
- a storyboard → shots → captions → soundtrack → final cut pipeline;
- an auditable, zero-cost production path with optional paid upgrades.

Do **not** use it to claim photoreal AI footage. In LOCAL mode the look is
painted-vector animation; photorealism is an explicitly documented limitation.

## The three modes

| Mode | What runs | Spend |
|---|---|---|
| `local` | vector rig, procedural sets, procedural score, FFmpeg edit | **0** |
| `hybrid` | local + external providers *only where code cannot reach* and the user authorised a budget | budget-capped |
| `premium` | best available provider per capability, still budget-capped and logged | budget-capped |

Enforced in `scripts/acs/providers/registry.py`; `authorize_spend` must be set to
`true` **after** the user agrees, and `budget_usd` is a hard ceiling.

## Pipeline (each stage is resumable)

```bash
python scripts/studio.py status                                     # mode, providers, budget, FFmpeg
python scripts/studio.py analysis  --project projects/demo_001 \
        --reference "Ejemplos/Video/reference.mp4"                  # probe, cuts, palette, motion, audio
python scripts/studio.py preproduction --project projects/demo_001   # script, storyboard, bibles, continuity
python scripts/studio.py plan      --project projects/demo_001       # code / reuse / external per element
python scripts/studio.py assets    --project projects/demo_001       # library: list/search/validate/reuse
python scripts/studio.py assets generate --prompt "Genera un fondo de laboratorio" --id laboratorio
python scripts/studio.py ui        --project projects/ui_direccion     # decide modes, boxes and windows (--apply)
python scripts/studio.py storyboard --project projects/demo_001      # one still per shot + contact sheet
python scripts/studio.py cast      --project projects/demo_001       # cast sheet (identity check)
python scripts/studio.py identity  --project projects/ui_direccion    # canonical ids + seven-pose sheet + per-shot crops
python scripts/studio.py voice     --project projects/ui_direccion --provider kokoro --allow-model-download
python scripts/studio.py voicecheck --project projects/ui_direccion   # take/stem/mix RMS, order, trims
python scripts/studio.py audio     --project projects/demo_001       # procedural score (WAV)
python scripts/studio.py render    --project projects/demo_001       # Remotion → silent MP4
python scripts/studio.py assemble  --project projects/demo_001       # mux + 2-pass loudnorm + preview
python scripts/studio.py mix       --project projects/demo_001       # dialogue vs score (needs a voice stem)
python scripts/studio.py qa        --project projects/demo_001       # gates + report
python scripts/studio.py produce   --project projects/demo_001 --reference "..."
```

The film itself is data: `studio/src/data/project.json` (shots, camera, actors,
captions) + `studio/src/data/cast.json` (identity). Both are single sources of
truth shared by the renderer and the Python pipeline.

## Production protocol (act as director of production)

1. **Read the reference before designing anything.** Run `analysis`; do not
   assume shot rhythm, palette or pacing. Numbers beat intuition.
2. **Write the preproduction first:** logline, script lines, shot list with a
   camera *intent* per shot, character bible, environment bible.
3. **Declare the strategy per element** (`plan`): code, reuse, or external.
   Reuse always beats regeneration; code always beats paid generation.
4. **Direct, don't decorate.** Every camera move must have a narrative reason
   (pressure, reveal, loneliness). No random motion, no zoom-as-animation.
5. **Keep identity persistent.** A wardrobe change is a state, never a new character.
5b. **Look at a still before animating.** `storyboard` prints one key frame per
   shot in seconds; fix the frame there, not after a 26-minute render. A passing
   test does not prove the active manifest is the film you think you are
   rendering: check that the still belongs to the new project.
5c. **Search the asset library before creating.** A new background is a version
   of an existing set when it is a lighting/time-of-day variation; a prop is not
   a new character. `assets generate` returns a renderable, previewed, validated
   version; see `ASSET_SYSTEM.md`.
6. **Let the UI earn its place.** Run `ui`; if a graphic has no free zone, accept
   the mode escalation or drop it. Never ship a card over a face to keep a
   layout.
7. **Never ship an ungraded cut.** `qa` must pass; a black or frozen render fails.
8. **Report limits honestly.** If a capability is unavailable, say so and continue
   with what does work.

## Specialist roles

Reference Analyst · Script Writer · Storyboard Director · Character Designer ·
Environment Designer · Image Specialist · Motion Director · Video Specialist ·
Cinematographer · Voice Director · Sound Designer · Editor · QA Director.

Each role has a concrete artefact in this repo (see `ARCHITECTURE.md`); the
roles describe *responsibilities over files*, not imaginary agents.

## Hard rules

1. No video without preproduction. 2. No character without a bible entry.
3. No arbitrary redesign between shots. 4. No empty generic backgrounds.
5. Zoom is not animation. 6. No unmotivated camera move. 7. No disconnected scenes.
8. Continuity is checked, not assumed. 9. Voice direction is written before audio.
10. No clip ships unreviewed. 11. Never regenerate what already passes.
12. Never invent a tool, endpoint or parameter. 13. Never hide a limitation.
14. Never destroy sources. 15. Never claim an operation that did not run.

## What is verified in this build

| Capability | Status |
|---|---|
| FFmpeg/FFprobe analysis (probe, cuts, palette, motion, loudness) | ✅ executed on 3 references |
| Remotion render (1080×1920, 30 fps, SVG rig + sets + captions + grain) | ✅ executed, see `TEST_REPORT.md` |
| Procedural soundtrack (additive synthesis, deterministic) | ✅ executed |
| FFmpeg assembly + loudnorm + preview | ✅ executed |
| Quality gates (black, freeze, motion, duration, loudness, caption plan) | ✅ executed |
| Asset library: catalogue, search, validation, reuse report | ✅ executed (`assets/catalog.json`, 38 assets) |
| Asset forge: sets, characters, expressions, props, graphics + stills | ✅ executed (`projects/asset_forge/preview/`) |
| Storyboard: key-frame stills + contact sheet | ✅ executed (`storyboard.jpg`) |
| Cast sheet | ✅ executed (`preproduction/cast.png`) |
| Voice: LOCAL word timings | ✅ executed (no speech, no network) |
| Voice: ElevenLabs takes | ⚠️ prepared and disabled (needs Voice ID + key + authorisation) |
| Image/video **generation** | ❌ not implemented (no verified adapter, no keys) |

Full evidence and the exact commands are in `TEST_REPORT.md`; limitations are
in `LIMITATIONS.md`.

## Files

```
SKILL.md                  this contract
VISUAL_STYLE_GUIDE.md     the look, derived from the reference corpus
ASSETS.md                 the asset library: ids, catalogue, reuse rules
ASSET_SYSTEM.md           the shared forge: versions, previews, references, proof
VOICE.md                  narration: LOCAL timings, ElevenLabs setup, costs
REPOSITORY_COMPARISON.md  audit of the external repo and what was integrated
ATTRIBUTION.md            third-party code and licences (MIT)
ARCHITECTURE.md           modules, data flow, extension points
INSTALLATION.md           setup and dependency verification
USER_GUIDE.md             day-to-day usage
RESEARCH_REPORT.md        sources, what was verified, what was not
MODEL_COMPARISON.md       generation models and their trade-offs
LIMITATIONS.md            honest capability boundaries
TEST_REPORT.md            executed tests and results
CHANGELOG.md              version history
references/               style analysis + measured corpus data
scripts/                  Python pipeline (analysis, providers, audio, edit, QA)
studio/                   Remotion + TypeScript render engine
projects/                 per-film project folders (analysis, preproduction, output)
tests/                    unit tests for the deterministic core
```

## Rules for extending

Add a capability by implementing a `Provider` in `scripts/acs/providers/` and
registering it. Never edit the pipeline to special-case a vendor; never add a
provider that reports success without producing a real file.
