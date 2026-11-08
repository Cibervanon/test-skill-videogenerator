# AI CINEMATIC STUDIO

A code-first cinematic animation studio for Freebuff: analysis of a reference
video, structured preproduction, deterministic Remotion rendering, procedural
sound design, automated edit and quality gates — with paid generation available
only as an opt-in, budget-capped provider.

**LOCAL mode costs nothing and needs no API key.**

```bash
python scripts/studio.py status
python scripts/studio.py produce --project projects/demo_001 --reference "Ejemplos/Video/reference.mp4"
```

Latest story delivery: `projects/av_ultima_medida/output/final_video.mp4`
(1080×1920, 30 fps, 22.4 s, one Spanish narrator, no UI overlays).
The previous films are kept in `projects/demo_001/output/`,
`projects/demo_002/output/`, `projects/av_direccion/output/`,
`projects/av_direccion_demo/output/` and `projects/av_direccion_story/output/`;
`VISUAL_AUDIT.md` compares the earlier set against the reference corpus.

## Generate, inspect, correct (0.6.0)

```bash
python scripts/studio.py direct --title "Tres campanas y una deuda" \
    --idea "Un pueblo que ajusta cuentas cada amanecer" --seconds 22 \
    --project projects/creado_desde_titulo
python scripts/studio.py compose --project projects/sistema_demo --spec projects/sistema_demo/spec.json
python scripts/studio.py storyboard --project projects/sistema_demo --manifest projects/sistema_demo/manifest.json
python scripts/studio.py inspect  --project projects/sistema_demo --manifest projects/sistema_demo/manifest.json
python scripts/studio.py evaluate --project projects/sistema_demo --manifest projects/sistema_demo/manifest.json
python scripts/studio.py feedback add --problem "En esta escena la etiqueta tapa la cara" --scene S02
python scripts/studio.py styles
```

- **Five styles, one engine:** `studio/src/data/styles.json` re-tunes palette,
  type, density, plate and motion; scenes, rig and camera are shared.
- **Motion graphics and UI:** 13 overlay types in `studio/src/motion-graphics/`
  (label, badge, callout, panel, HUD, highlight, arrow, counter, bar, donut,
  line, ranking, process), driven by the manifest, validated geometrically.
- **Feedback memory:** `feedback/records.jsonl` with category, severity and
  scope; `USER_FEEDBACK.md`, `VISUAL_PREFERENCES.md`, `STYLE_RULES.md` and
  `IMPROVEMENT_LOG.md` are generated. It records and scopes — it does not learn
  by itself.
- **Inspection vs evaluation:** `inspect.py` measures pixels and geometry;
  `evaluate.py` never averages them into a score and leaves acting, narrative and
  rhythm `pending` until a human writes a review.
- **Hybrid demo:** `projects/sistema_demo/` — two characters, two sets, Spanish
  Kokoro narration, label, chart, callout, HUD, panel, transitions and
  subtitles in one composition.

## UI como dirección (0.7.0)

```bash
python scripts/studio.py ui --project projects/ui_direccion \
    --manifest projects/ui_direccion/manifest.json --apply --write-active
python scripts/studio.py storyboard --project projects/ui_direccion
python scripts/studio.py inspect    --project projects/ui_direccion
```

- **Seis modos por plano:** A escena sola · B aclaración sobre el fondo · C UI
  integrada con el personaje · D escena atenuada · E composición independiente ·
  F UI como transición. El director los elige por intención y payload, no por
  disponibilidad de componentes.
- **Colocación adaptativa:** anclas semánticas, rechazo de cara/cuerpo/subtítulos/
  solapes, reducción al 85/72 % y **escalado de modo** (B → D → E) cuando no hay
  hueco. Nunca se encoge un texto hasta hacerlo ilegible.
- **Duración de lectura:** la ventana sale de las palabras del propio elemento;
  en B/C la UI se retira antes de 0.90 para que la escena cierre el plano.
- **Demo:** `projects/ui_direccion/` — 27,4 s, 8 planos, voz Kokoro, 6 elementos
  que recorren A–F, 20 cues SRT. Medido: 0 cuerpos y 0 caras cubiertas, frente a
  3 y 2 en `sistema_demo` con la misma auditoría.

## Dirección audiovisual (0.9.0)

```bash
python scripts/studio.py av --project projects/av_direccion \
    --spec projects/av_direccion/spec.json --write-active
python scripts/studio.py avqa --project projects/av_direccion \
    --manifest projects/av_direccion/manifest.json \
    --baseline projects/ui_direccion/manifest.json
```

- **El montaje es una decisión, no una lista de planos.** `spec.json` declara el
  beat de cada plano (hook, setup, development, insert, escalation, reaction,
  reveal, close), su escala y el motivo de la cámara y de la transición. El
  planificador escribe el mismo manifest que ya consume Remotion; no hay un
  segundo renderer.
- **Cámara ampliada, no sustituida.** Los 9 movimientos existentes se mantienen
  y se añaden `trackLeft`, `trackRight` y `reframe`; S09 usa `trackRight` para
  descubrir la cuerda que falta.
- **Audio ligado a la acción.** Cada plano puede declarar cues con tiempo
  (`bell`, `footstep`, `dig`); una lista vacía es silencio intencional y no
  dispara los efectos automáticos antiguos.
- **QA creativo separado del técnico.** `avqa` mide estructura, variedad de
  escalas, motivos, acción/reacción, transiciones y cobertura de audio. No pone
  nota de narrativa ni de actuación: esas dimensiones siguen pendientes de
  revisión humana.
- **Demo:** `projects/av_direccion/` — 10 planos, 30,93 s, las mismas 8 líneas de
  `ui_direccion`, 15 eventos de audio y `quality/before_after.md`.

## Historia corregida (0.10.1)

La última entrega narrativa es `projects/av_direccion_story/`: 10 planos,
8 líneas habladas por un solo narrador `ef_dora`, dos planos sin diálogo y cero
elementos de UI. Es una copia corregida; `projects/av_direccion/` se conserva.

```bash
python scripts/studio.py voice --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json --provider kokoro
python scripts/studio.py captions --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json
python scripts/studio.py mixdown --project projects/av_direccion_story --music-gain 0.20
python scripts/studio.py render --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json
# reproducibility slice without overwriting the silent picture:
#   render ... --frames 0-29 --out .tmp/a.mp4
python scripts/studio.py assemble --project projects/av_direccion_story \
    --audio projects/av_direccion_story/generation/audio/mix.wav
python scripts/studio.py qa --project projects/av_direccion_story \
    --manifest projects/av_direccion_story/manifest.json
```

Evidencia: QA 13/13, inspección 0/10, **3 ventanas** de música cercanas a la voz,
**181 tests** y `tsc` sin errores. La voz está medida dentro del MP4
(`voice_in_delivery` **0,9209**), no solo en el WAV; el video se reensambló con
el mix corregido. Los subtítulos quemados ya usan el reloj real de las tomas
(`captions`, 23 cues, 0 ms de error frente al plan); siguen siendo chunks de 2–3
palabras, no énfasis palabra a palabra, y el MP4 conserva los subtítulos del
build anterior porque no se re-renderizó. La narración sigue siendo
signal-verified, no ASR; narrativa, actuación, ritmo y estilo siguen pendientes
de revisión humana.

## Demo de dirección (0.10.5)

`projects/av_direccion_demo/` es un corte de **6 planos / 20,433 s** construido
con el mismo motor: hook en la campana, presentación de los dos hombres, subida
con la cuerda, reacción sin diálogo, señalamiento de la cuerda que falta y cierre
al amanecer. S02 completa caminar→girar y S03 gira→alcanza: **2 secuencias /
4 fases**. El render completo son **613 frames en 500,47 s**; el MP4 muxea 612
frames (el último lo descarta el muxer) y pesa **11,0 MB**.

```bash
python scripts/studio.py av --project projects/av_direccion_demo \
    --spec projects/av_direccion_demo/spec.json
python scripts/studio.py audio --project projects/av_direccion_demo \
    --manifest projects/av_direccion_demo/manifest.json
python scripts/studio.py voice --project projects/av_direccion_demo \
    --manifest projects/av_direccion_demo/manifest.json --provider kokoro
python scripts/studio.py captions --project projects/av_direccion_demo \
    --manifest projects/av_direccion_demo/manifest.json
python scripts/studio.py mixdown --project projects/av_direccion_demo --music-gain 0.14
python scripts/studio.py render --project projects/av_direccion_demo \
    --manifest projects/av_direccion_demo/manifest.json
python scripts/studio.py assemble --project projects/av_direccion_demo
python scripts/studio.py qa --project projects/av_direccion_demo \
    --manifest projects/av_direccion_demo/manifest.json
```

Evidencia: QA **13/13**, `voice_in_delivery` **0,9273**, loudness −17,2 dB,
motion **8,858**, inspección **0/6**, QA creativo **20/20**, evaluación **10
dimensiones medidas / 4 humanas pendientes**, 1 ventana de música dentro de 3 dB
y `voicecheck` OK (5 líneas, 36 palabras, 15,15 s). Movimiento por plano: mínimo
**2,438**, media **4,249**, **0 planos low-motion**. Frente al relato de 10 planos,
la comparación normalizada sube acción por plano **0,50 → 0,833**, dos actores
**0,30 → 0,667**, variedad de cámara **0,80 → 1,00** y variedad de escala
**0,40 → 0,667**. La comparación es estructural: narrativa, actuación, ritmo y
estilo siguen sin puntuación automática.

## Continuidad de personajes y nueva historia (0.10.6)

`carry` hereda `x`, `facing` y `hold` del estado de salida del actor; un salto
mayor de 260 px en la misma escena exige `continuityMotive`, y `carry` se rechaza
al cambiar de escenario. El estado resuelto queda en `manifest.continuity` y
`avqa` lo audita; el renderer sigue recibiendo campos de actor normales.

- **Nueva historia:** `projects/av_ultima_medida/` — *La última medida*, en un
taller de sastrería al amanecer. Seis planos, 22,4 s, hook → setup → escalation
→ reaction → reveal → close; sin campana, pueblo nevado ni cementerio.
- **Nuevo set:** `Workshop.tsx` — ventana al amanecer, mesa, maniquí, cinta rota
y costura saltada.
- **Evidencia:** 5 estados heredados, 3 secuencias / 6 fases, 4/6 planos con
acción, `continuity_issues: []`, inspección **0/6**, QA técnico **13/13**.
- **Render:** 672 frames, 1080×1920, 30 fps, H.264/AAC, 11.989.156 bytes.
- **Tests:** `python -m pytest tests -q` → **184 passed**; `tsc --noEmit` → 0.

See `CONTINUITY.md` and `projects/av_ultima_medida/quality/comparison.md`.

## Identidad y narración (0.8.0)

```bash
python scripts/studio.py identity --project projects/ui_direccion
python scripts/studio.py voice --project projects/ui_direccion \
    --provider kokoro --allow-model-download
python scripts/studio.py voicecheck --project projects/ui_direccion
```

- **La identidad es dato, no un redibujo por plano.** `cast.json` define altura,
  cabeza, gorro, ropa, paleta y estados de vestuario; el rig aplica la altura
  antes de la escala del plano y las anclas de UI usan el mismo factor. La banda
  del gorro pasa por encima de las cejas, no por los ojos.
- **Auditoría estructural + hoja visual.** `identity` comprueba ids canónicos,
  campos obligatorios, vestuario registrado y que ningún plano sobrescriba la
  identidad; genera `identity_audit.md`, `identity_sheet.png` (siete poses) y
  `identity_shots.png` (el mismo personaje recortado en cada plano).
- **Narración real, cacheada y medida.** Kokoro en español genera las tomas;
  `voicecheck` mide RMS y pico de cada toma, del stem y del mix, y detecta
  silencios, desorden, frases duplicadas y colas recortadas. El stem ya no suma
  dos tomas en los fundidos.
- **Demo:** `projects/ui_direccion/` — 27,4 s, 8 planos, 8 líneas / 58 palabras
  (23,34 s de habla), voz Kokoro audible en el MP4.

See `AV_DIRECTION.md`, `CAPABILITY_MATRIX.md`, `ROADMAP.md`, `UI_DIRECTION.md`,
`MOTION_GRAPHICS.md`, `FEEDBACK_SYSTEM.md`, `INSPECTION_AND_EVALUATION.md` and
`EXTERNAL_REPOS_AUDIT.md`.

## What is real

- `scripts/analyze_reference.py` — FFmpeg/FFprobe measurements (cuts, palette,
  motion by SAD search, loudness, activity), run on the 3 reference shorts.
- `scripts/acs/audio_gen.py` — additive-synthesis score, deterministic.
- `studio/` — Remotion engine: SVG character rig, six hand-built sets, camera
  vocabulary, captions, grain/vignette, procedural particles.
- `scripts/acs/assemble.py` + `qa.py` — FFmpeg mux, two-pass loudnorm to −14 LUFS, quality gates.
- `scripts/acs/library.py` + `assets/catalog.json` — the single asset library:
  stable ids, search, validation, versions, previews, reuse report.
- `scripts/acs/asset_forge.py` + `registry.json` — creates renderable sets,
  characters, expressions, props, motion graphics and UI from a request, without
  a second catalogue or a second renderer. Proof stills and the contact sheet are
  in `projects/asset_forge/preview/`; see `ASSET_SYSTEM.md`.
- `scripts/acs/storyboard.py` + `storyboard.mjs` — one still per shot and a
  captioned contact sheet, before any animation is paid for.
- `scripts/acs/voice.py` — LOCAL word timings by default; ElevenLabs only behind
  an explicit Voice ID, key and `--authorize-spend` (see `VOICE.md`).
- **Kokoro TTS, local and free** (`scripts/acs/kokoro_worker.py` + `kokoro_tts.py`):
  Spanish speech on CPU in `.venv-kokoro` (Python 3.12), word timings from the
  model's `pred_dur`, cache shared across projects, SRT from the same clock, and
  a deterministic NumPy mix (`mixdown.py`) that ducks the score from a measured
  voice envelope. No key, no credits, no network at synthesis time. See
  `KOKORO_INTEGRATION.md`.
- `scripts/acs/edit.py` — word-guided edit: aligns shot boundaries to word
  timings, reports drift beyond tolerance, derives caption windows from the same
  clock (`studio.py edit`).
- `studio.py compose` — builds a manifest *through* the catalogue: a spec names
  scenes, cameras and characters by asset id and an unknown id aborts before a
  manifest exists. `projects/demo_003/spec.json` is a worked example.
- `tests/` — **184** unit tests over the deterministic core, including compound
  action phases, per-shot motion reporting and carried character state, plus the
  asset forge, versions,
  references, narration coverage, audio integrity and composition (the Kokoro
  tests use fixtures, never the model).

## What is not

Image and video generation: no adapter is verified, so every external provider
refuses to run instead of faking output. Narration is real and local through
Kokoro (`KOKORO_INTEGRATION.md`); there is no lip-sync, no second voice provider
and no external media generation. See `LIMITATIONS.md`.

## Documentation

`SKILL.md` (contract) · `KOKORO_INTEGRATION.md` (local Spanish voice) ·
`VISUAL_STYLE_GUIDE.md` (the look) · `VISUAL_AUDIT.md`
(demo 001/002/003 vs the references) · `ASSETS.md`
(library and reuse) · `ASSET_SYSTEM.md` (forge, versions, previews, references) ·
`VOICE.md` (narration, ElevenLabs setup) ·
`ARCHITECTURE.md` · `INSTALLATION.md` · `USER_GUIDE.md` · `RESEARCH_REPORT.md` ·
`MODEL_COMPARISON.md` · `REPOSITORY_COMPARISON.md` (external repo audit) ·
`ATTRIBUTION.md` (third-party licences) · `TEST_REPORT.md` · `LIMITATIONS.md` ·
`CHANGELOG.md`
