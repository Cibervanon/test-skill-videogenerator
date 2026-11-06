# Capability matrix

Measured against the code, not against the documentation. Every row names the
file that proves the claim. Status vocabulary:

- **implemented** — works today, exercised by a test or a render;
- **partial** — works with a documented limit;
- **adapter only** — the interface exists, the provider/feature does not;
- **missing** — no code.

Updated: 2026-11-05.

## Engine and composition

| Capability | Status | Evidence | Limit |
|---|---|---|---|
| Remotion composition, 1080×1920 @30 | implemented | `studio/src/Root.tsx`, `composition/Demo.tsx` | one vertical format; other aspect ratios need a format pass |
| Shot timeline with per-boundary transitions | implemented | `composition/Demo.tsx` (`shotTimeline`, `transitionIn`) | cut + dissolve only |
| Camera vocabulary (12 moves) | implemented | `engine/CameraRig.tsx` | transform-based, no true 3D parallax or lens model |
| Parallax layers | implemented | `CameraRig.ParallaxGroup`, used by every set | 2.5D shift, depth is authored per set |
| Procedural character rig | implemented | `characters/Character.tsx`, `geometry.ts` | one body plan, 3 wardrobe identities |
| Acting presets (idle/walkIn/closeup/dig/reach/turn/call) | implemented | `composition/Actors.tsx` | keyframed intent curves, not physics or mocap |
| Mouth/eyes/brows | partial | `Character.tsx` | mouth is a shape, not visemes: **no lip-sync** |
| Sets | implemented | `scenes/*.tsx` (5) | all drawn in one illustrative language |
| Atmosphere, materials, grain/vignette | implemented | `engine/atmosphere.tsx`, `texture.tsx`, `FilmFinish.tsx` | no volumetric lighting |
| Burned-in captions | implemented | `engine/Subtitles.tsx` | chunked by words, not timed to audio in the render (SRT is the timed artefact) |
| Presentation modes A–F | implemented | `composition/Demo.tsx`, `motion-graphics/modes.tsx` | per shot, not per element; cut/dissolve between modes |
| **Style token system (5 styles)** | implemented | `engine/styles.tsx`, `data/styles.json` | tokens only: shapes do not change per style |
| **Motion graphics (13 overlay types)** | implemented | `motion-graphics/*` | 2D SVG/DOM only; no 3D charts |
| **Audiovisual beat planner** | implemented | `scripts/acs/av_director.py`, `studio.py av` | authored beat sheet → manifest; it does not write prose or invent shots |
| **Declared shot scale + camera/transition motives** | implemented | `av_director.plan`, manifest fields | scale is a directorial unit, not a lens model |
| **Structural creative QA** | implemented | `scripts/acs/avqa.py`, `studio.py avqa` | structure only; narrative, acting and taste remain human |
| **Before/after edit comparison** | implemented | `avqa.compare`, `quality/before_after.md` | structural metrics, not a quality score |
| **Contextual UI director (modes A–F)** | implemented | `scripts/acs/ui_director.py`, `studio.py ui` | rule-based intents; the director chooses the mode, it does not write copy |
| **Adaptive placement with escalation** | implemented | `overlays.resolve_ui_box`, `uiqa.py` | resolved once per shot: **no per-frame reflow** under camera motion |
| **UI timing from reading load** | implemented | `ui_director._window` | 4 words/s estimate, not eye tracking |
| **UI QA + render evidence** | implemented | `uiqa.inspect_ui`, `uiqa.measure_render` | geometry + sampled pixels; no OCR, no taste |
| **Character labels that follow the body** | implemented | `motion-graphics/layout.ts`, `annotations.tsx` | one label per actor per shot |
| **Safe-area / face / caption-band rules** | implemented | `motion-graphics/layout.ts`, `scripts/acs/overlays.py` | geometric, from the manifest |
| HUD / panels / badges / callouts / arrows / highlights | implemented | `motion-graphics/annotations.tsx` | screen-space primitives |
| **Visual inspection (pixels)** | implemented | `scripts/acs/inspect.py` | no OCR, no semantics, no taste |
| **Evaluation with evidence kinds** | implemented | `scripts/acs/evaluate.py` | subjective dimensions stay `pending` without a human review |
| **Feedback memory with scopes** | implemented | `scripts/acs/feedback.py` + `feedback/records.jsonl` | records and scopes; **does not learn automatically** |
| **Creative direction from a title/script** | implemented | `scripts/acs/director.py` | rule-based, template narration must be approved |
| **Generation from a title, end to end** | implemented | `projects/creado_desde_titulo/` | plan + manifest + storyboard; narration is a flagged template |

## Audio and voice

| Capability | Status | Evidence | Limit |
|---|---|---|---|
| Procedural score + foley | implemented | `scripts/acs/audio_gen.py` | synthesised, not licensed music |
| Explicit per-shot sound cues | implemented | `audio_gen.spec_from_project`, manifest `sound` | three synthesis types; unknown cues are rejected |
| Kokoro local Spanish TTS | implemented | `scripts/acs/kokoro_tts.py`, `kokoro_worker.py` | 3 voices, CPU, `pred_dur` timings |
| ElevenLabs provider | adapter only | `acs/providers/`, `voice.py` | gated by `authorize_spend`; not exercised in this session |
| Word timings | partial | `kokoro_worker.words_from_pred` | model duration predictor, not forced alignment |
| SRT subtitles from the real take | implemented | `scripts/acs/subtitles.py` | Spanish line breaking is word-count based |
| Ducking + mix check | implemented | `scripts/acs/mixdown.py`, `mixcheck.py` | sidechain compressor, fixed attack/release |
| Voice-driven shot fitting | implemented | `kokoro_tts.fit_shots` | stretches shots only when `--fit-shots` is passed |
| Narration validation over take/stem/mix | implemented | `scripts/acs/narration.py`, `studio.py voicecheck` | signal, not intelligibility; no ASR |
| One narrator in narration mode | implemented | `voice.speaker_of`, `narration.validate`, tests | explicit `dialogue: true` opt-out; no automatic dialogue detection |
| Audio coverage through the last spoken line | implemented | `narration.validate`, `assemble.assemble`, `qa.audio_duration` | speech coverage, not a subjective mix judgment |
| Render progress log + manifest restoration | implemented | `providers/local.py`, `studio.py render` | two consecutive provider renders still pending |

## Character identity

| Capability | Status | Evidence | Limit |
|---|---|---|---|
| Canonical cast (id, proportions, palette, wardrobe) | implemented | `studio/src/data/cast.json` | one body rig; silhouette is descriptive |
| Identity height applied to rig and UI anchors | implemented | `Character.tsx`, `overlays.actor_anchor` | proportional scale, not custom geometry |
| Identity audit (no per-shot variants) | implemented | `scripts/acs/identity.py`, `studio.py identity` | structural, not perceptual |
| Seven-pose identity sheet + per-shot crops | implemented | `IdentitySheet`, `quality/identity_shots.png` | human review; no face embedding |
| Head/body proportion audit | implemented | `identity.audit` (`head_to_body`) | structural ratio, not a pixel measurement |

## Asset forge and shared library

| Capability | Status | Evidence | Limit |
|---|---|---|---|
| One catalogue with schema-2 metadata | implemented | `scripts/acs/library.py`, `assets/catalog.json` | derived file; edit sources/registry, not the catalogue |
| Local asset creation from a request | implemented | `scripts/acs/asset_forge.py`, `studio.py assets generate` | deterministic SVG primitives, not image generation |
| Layered / flat backgrounds | implemented | `Studio/src/generated/GeneratedScene.tsx`, set specs | laboratory-led set grammar |
| Generated characters and expressions | implemented | `characters/cast.ts`, `composition/Actors.tsx` | one existing body rig |
| Generated props and graphics | implemented | `generated/PropLayer.tsx`, `motion-graphics/OverlayLayer.tsx` | primitive props; 13 existing overlay types |
| Append-only versions + previews | implemented | `assets/registry.json`, `assets/generated/**/preview.svg` | SVG previews, not pixel renders per asset |
| Search by style/scene/usage/similarity | implemented | `library.search`, `library.similar` | token/tag scoring, not embeddings |
| Persistent references | implemented | `scripts/acs/references.py`, `assets/references.json` | metadata-only; selection by purpose/tags |
| Provenance/licence gate | implemented | `library.validate`, `references.validate` | provenance quality is only as good as the supplied record |
| Other resolutions/aspects | missing | — | forged assets reject non-1080×1920/9:16 |
| Image/diffusion generation | missing | — | no external provider, no credits |

## Production

| Capability | Status | Evidence |
|---|---|---|
| Asset catalogue + compose by id | implemented | `scripts/acs/library.py`, `studio.py compose` |
| Storyboard stills + contact sheet | implemented | `scripts/acs/storyboard.py` |
| Render → mux → QA | implemented | `studio.py render/assemble/qa` |
| Regression references | implemented | `evaluate.snapshot/compare`, `references/regression/` |
| Multiple aspect ratios | missing | — |
| Lip-sync / visemes | missing | — |
| Real footage / photoreal humans | missing (LOCAL mode) | documented in `LIMITATIONS.md` |
| OCR of burned-in text | missing | contrast is measured, text is not read |
| Automatic style *assets* per style | missing | styles are tokens over one drawing language |
| Lottie / Rive / D3 adoption | missing (deliberate) | see `EXTERNAL_REPOS_AUDIT.md` |

## What this matrix refuses to claim

- The system does not learn by itself. It records feedback, scopes it, and only
  promotes a rule when a human validates it with evidence.
- A style is not a new rendering engine: it re-tunes tokens over the same rig,
  sets and camera.
- The inspector measures pixels and geometry; it does not judge acting,
  narrative or taste.
- Data graphics only exist when a fact carries a source, or when the value is
  explicitly marked `ilustrativo` in the render.
