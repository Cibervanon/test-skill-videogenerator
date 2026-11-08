# TEST REPORT

Everything below was executed on this machine on 2026-11-03 (Windows 11,
FFmpeg 9.0.2, Python 3.14.7, Node 24.21.0, Remotion 4.0.540). Nothing is
reported as passing that was not run.

---

## 1. Delivered artefact

```
projects/demo_002/output/final_video.mp4          18.2 MB · 35.133 s · 1080×1920 · 30 fps · H.264/AAC
projects/demo_002/output/final_video_preview.mp4   1.6 MB · 540×960
projects/demo_002/output/picture_silent.mp4       23.9 MB · render without audio (1054 frames)
projects/demo_002/generation/audio/score.wav       6.2 MB · 35.133 s · 44.1 kHz stereo
projects/demo_002/preproduction/storyboard.jpg    contact sheet, one key frame per shot
projects/demo_002/preproduction/cast.png          cast sheet (identity check)
projects/demo_002/generation/voice/voice_plan.json  LOCAL word timings (no speech)
projects/demo_001/output/                         previous delivery, kept for comparison
projects/demo_001/output/v1/                      the first delivery, also kept
```

`ffprobe` on the delivery: video `h264` 1080×1920 @ 30.000 fps, 1053 frames;
audio `aac` 48 kHz stereo 191 kb/s; container `mp4`. The last rendered frame is
dropped by the muxer, hence 1054 in the silent render and 1053 in the delivery.

---

## 2. Unit tests

```
$ python -m unittest discover -s tests -v
Ran 35 tests in 31.4 s    # at 0.3.0; the 0.4.0 suite is 44 tests, see §8
OK
```

| Area | Tests | Result |
|---|---|---|
| shot building (micro-shot merge, contiguity, out-of-range cuts) | 3 | pass |
| selector (local never escalates, reuse wins, hybrid authorisation) | 5 | pass |
| cost guard (no spend without authorisation, ceiling, local free) | 3 | pass |
| registry (mode gating, provider selection, ranking) | 4 | pass |
| audio (timeline match, deterministic synthesis) | 2 | pass |
| preproduction (documents written, continuity ok) | 1 | pass |
| QA (caption coverage, missing output fails, delivery passes) | 3 | pass |

The render itself is covered by the delivery test (`test_delivery_passes_when_present`),
which skips if no MP4 exists — it did **not** skip in the final run.

---

## 3. Reference analysis (executed on the provided corpus)

```
$ python scripts/analyze_reference.py --input "Ejemplos/Video/*.mp4" \
      --out projects/demo_001/analysis --summary references/measurements.json
[analysis] … -> projects/demo_001/analysis/…
[analysis] summary -> references/measurements.json      (exit 0)
```

| file | duration | shots | soft cuts | mean shot | longest | mean motion | pan ratio |
|---|---|---|---|---|---|---|---|
| Ancient Jar | 64.90 s | 7 | 9 | 9.27 s | 20.63 s | 24.3 | 0.397 |
| Job Nobody Wants | 60.56 s | 6 | 9 | 10.09 s | 30.89 s | 29.6 | 0.663 |
| Perfect Railroads | 65.22 s | 8 | 12 | 8.15 s | 20.53 s | 30.4 | 0.677 |

Each analysis folder contains `video_metadata.json`, `scene_breakdown.json`,
`reference_style.md`, `frames/` (3 per shot) and `contact_sheet.jpg`.

---

## 4. Pipeline stages

| Stage | Command | Result |
|---|---|---|
| status | `python scripts/studio.py status` | provider matrix printed; LOCAL, `spent_usd 0.0` |
| analysis | see §3 | exit 0, 3 references |
| preproduction | `… preproduction --project projects/demo_001` | exit 0, 5 shots / 35.13 s, continuity ok |
| plan | `… plan --project projects/demo_001` | `production_plan.json`, 100 % `code` strategy |
| audio | `… audio --project projects/demo_001` | 35.133 s WAV, 44.1 kHz stereo, deterministic |
| assets | `… assets validate` | 30 assets, ids unique, files present, dependencies valid |
| storyboard | `… storyboard --project projects/demo_002` | 5 stills + `storyboard.jpg` (1448×1300) |
| cast | `… cast --project projects/demo_002` | cast sheet rendered |
| voice | `… voice --project projects/demo_002` | 5 lines / 47 words of timings, **no speech, no network** |
| mix | `… mix --project projects/demo_002` | not applicable (no speech stem) — reported, not passed |
| render | `… render` (and a direct `remotion render`) | 1054/1054 frames, 23.9 MB, ~24 min |
| assemble | `… assemble --project projects/demo_002` | 18.2 MB delivery + 1.6 MB preview, two-pass loudnorm |
| qa | `… qa --project projects/demo_001` | **PASS**, 10/10 gates |

---

## 5. Quality gates on the delivery

| gate | value | threshold | result |
|---|---|---|---|
| readable | mp4 parsed | — | PASS |
| has_video | h264 1080×1920 | required | PASS |
| has_audio | aac 48 kHz stereo | required | PASS |
| duration | 35.133 s (Δ 0.003 s) | ±0.25 s | PASS |
| format | 1080×1920 @ 30 fps | exact | PASS |
| motion | 7.068 mean luma diff | ≥ 1.0 | PASS |
| black_frames | 0.000 | ≤ 0.02 | PASS |
| freeze | 0.1186 | ≤ 0.55 | PASS |
| loudness | −12.7 dB mean (−14 LUFS target, two-pass) | −22…−11 dB | PASS |
| audio_activity | 0.229 | > 0.05 | PASS |
| caption_plan | 1.000 | ≥ 0.55 | PASS |

Full report: `projects/demo_001/quality/final_quality_report.md`.

---

## 6. Visual review (frames decoded from the delivered MP4)

Frames at 1.5 s / 12.5 s / 21.5 s / 27 s were extracted from the new delivery and
inspected, and the storyboard sheet plus the cast sheet were reviewed:

- captions are present, changing every 2–3 words, in the lower third;
- the two characters keep identical proportions, palette and props across
  shots (persistent identity);
- the close-up (16 s) shows the same face/hat/coat at 5.15x scale, no redesign;
- the dawn field (21.5 s) holds three depth planes (treeline, fence/headstones,
  grave + figure) with a foreground snow plane, and the eleven headstones read as
  stone with carved crosses, obelisks and slabs;
- the doorway shot shows a furnished interior (wallpaper, rug, shelf, coat,
  lamp) under the new contrast veil: the room's mid-tones sink, the lamp pool and
  the door stay bright, and the character keeps full brightness;
- no black strip on either edge of the doorway shot (the pan overscan bug);
- grain, vignette and warm/cool grade are visible on every frame;
- no black frame, no frozen frame, no missing character, no duplicated prop.

Defects found in the first v2 render and fixed before this delivery: the timeline
overlap bug, the black edge strip, lollipop-shaped headstones and a duplicate
shovel at the grave (see CHANGELOG 0.2.1).

Two defects were found and fixed **before** delivery, both caused by the same
class of bug (see CHANGELOG): actors rendered outside any `<svg>` (invisible),
and the film-finish overlay covering the frame (black render).

---

## 7. What this test run does NOT prove

- No image/video **generation** was tested, because no adapter exists.
- No **ElevenLabs** call was made: the adapter is present but gated behind a Voice
  ID, a key and `--authorize-spend`; the tests assert it refuses before any
  network access.
- **No lip-sync** exists, so none is claimed.
- No transcription: the build exposes no whisper filter and no ASR package.
- Photorealism, lip-sync and cloth simulation are out of scope (LIMITATIONS.md).
- The QA gates are calibrated on this engine's renders; they catch regressions
  (black, freeze, silence, wrong duration) and are not an aesthetic score.
- Long-form behaviour (> 2 min) was not tested; only 34 s and 29 s films were
  rendered.

---

## 8. demo_003 (0.4.0) — the visual pass

Built through the catalogue, not by hand-editing `project.json`:

```
$ python scripts/studio.py compose --spec projects/demo_003/spec.json \
      --project projects/demo_003 --write-active
[compose] … 6 shots, every asset resolved
$ python scripts/studio.py voice --project projects/demo_003
[voice] provider=local speech=False lines=6 words=39
$ python scripts/studio.py edit --project projects/demo_003
[edit] ok S02..S06, total shift +0.30s, tolerance ±0.45s
```

| gate | demo_003 | demo_002 |
|---|---|---|
| duration | 29.233 s (876 frames) | 35.133 s (1054 frames) |
| size | 16.8 MB | 18.2 MB |
| motion | 9.062 | 7.068 |
| freeze | 0.0194 | 0.1186 |
| black_frames | 0.0 | 0.0 |
| loudness | −13.1 dB | −12.7 dB |
| audio_activity | 0.19 | 0.229 |
| caption_plan | 1.0 | 1.0 |
| QA overall | **PASS 10/10** | PASS 10/10 |

`python -m unittest discover -s tests` → **44 tests, OK** (9 new: catalogue
composition, refusal of unknown scene/character, a new project built only from
library ids, cues/alignment/tolerance/duration/caption windows).
`npx tsc --noEmit` → 0 errors. `studio.py assets validate` → 30 assets, 0 new
needed for demo_003.

### Inspection, not automation

The first demo_003 render was decoded and inspected before this delivery. Four
composition defects were found and fixed (overlapping actors in S01, a flat
interior in S02, lamp overlaying the picture frame, the reaching hand next to the
apprentice's head); each fix was checked with `remotion still` before the second
full render. Two defects remain and are documented in `VISUAL_AUDIT.md` and
`LIMITATIONS.md`: the shovel never plants in the grave (no IK), and the sets are
still far thinner than the references.

### Still not proven

- Word-cued editing is implemented and exercised on synthetic timings, but no
  real take exists in LOCAL mode, so nothing is cut to actual speech.
- The comparison against the references is a human inspection of frames, not a
  metric; no aesthetic score is claimed.

---

## 9. Kokoro local voice (0.5.0) — audio, not video

The request for this round was explicitly **no new render**: prove the voice path
with real audio. Everything below was executed on 2026-11-04.

### Suite

```
$ python -m unittest discover -s tests
Ran 55 tests in 52.8 s
OK
```

11 new tests cover Kokoro (config, unknown speaker, cache-key sensitivity,
missing interpreter, weight detection, `pred_dur` grouping, syllable fallback,
shot fitting) and 3 cover SRT building. None of them load the model or touch the
network.

### Real generation (CPU, no GPU present)

| Line | Shot | Voice | Audio | Fits? |
|---|---|---|---|---|
| S01 narrator | 5.00 s | `ef_dora` | 4.00 s | yes |
| S02 elder | 5.00 s | `em_alex` | 3.60 s | yes |
| S03 young | 5.00 s | `em_santa` | 3.18 s | yes |
| S04 narrator | 4.00 s | `ef_dora` | 1.85 s | yes |

- 34 words, **100 % timed from `pred_dur`** (no syllable fallback), 24 kHz mono
  PCM_16, peak-normalised stem at −1.5 dBFS.
- Second run reported all four lines as **cached** — no re-synthesis.
- Speed: 4.0 s of audio in 6.5 s of synthesis (1.6× realtime) + ~3 s model load.
- `narracion_es.m4a`: 18.2 s, 440 KB, AAC 192 kb/s; mix mean −11.9 dB.
- Mix check: **53 → 8** windows within 3 dB of the voice after sidechain ducking.

### What this does not prove

- No ElevenLabs comparison (would spend credits) and no subjective quality score.
- No video was rendered for this demo, so voice-to-picture sync is proven on the
  manifest clock and the SRT, not on muxed frames.
- No ASR alignment: the timings are the model's duration prediction.

---

## 10. Hybrid system (0.6.0) — 2026-11-04

Everything here was executed after the changes described in `CHANGELOG.md`
0.6.0. Nothing is marked passing that was not run.

### 10.1 Tests

```
python -m unittest discover -s tests
Ran 93 tests in 55.152s — OK
```

55 existing + 38 new (`test_feedback` 8, `test_overlays` 13, `test_director` 7,
`test_inspect` 5, `test_evaluate` 5). `tsc --noEmit` on `studio/` passes with the
overlay and style types compiled against the real composition.

The overlay tests include an anti-drift check: they parse `SAFE` and `RIG` out of
`layout.ts`/`geometry.ts` and fail if the Python mirror differs.

### 10.2 Hybrid demo — `projects/sistema_demo`

```
final_video.mp4          12.0 MB · 20.067 s · 1080×1920 · 30 fps · H.264/AAC
final_video_preview.mp4   1.1 MB · 540×960
picture_silent.mp4       16.2 MB · 624 frames rendered
score.wav / voice.wav / mix.wav   procedural bed · Kokoro Spanish · ducked mix
subtitles.srt            11 cues from the real take
storyboard.jpg           one key frame per shot
```

QA — 11/11 PASS:

| check | value |
|---|---|
| duration | 20.067 s (Δ 0.003 s) |
| format | 1080×1920 @ 30.000 fps, 602 frames |
| motion | 8.769 (min 1.0) |
| black frames / freeze | 0.0 / 0.0 |
| loudness | −12.8 dB mean, in band |
| audio activity | 0.275 |
| caption plan | 1.0 coverage |

Voice: 4 lines, 32 words, **100 % `pred_dur`**; `em_alex` for the keeper,
`em_santa` for the apprentice; 3.15 / 3.15 / 2.73 / 3.13 s, all inside their
shots. Mix: `sidechaincompress` threshold 0.04, ratio 10, 12 ms attack, 300 ms
release; `mixcheck` reports **19 windows within 3 dB of the voice** — the score
is tonal and quiet, so this is a warning to listen, not a pass.

Inspection — stills: **0 of 4 shots flagged**, overlays `OK` after the two fixes
below. Frames pulled from the delivered MP4 at 2/7/12/18 s: empty ratio
0.409–0.429, subject score 3.37–4.34, caption spread **205–220**, palette shift
0.093–0.138. Evaluation: **8 measured dimensions pass, 4 pending** (narrative,
acting, rhythm, style integrity — no human review file exists).

Reference registered: `sistema_demo_v1`, sha256 prefix `0109dc1ac90c`.

### 10.3 Generation from a title — `projects/creado_desde_titulo`

```
python scripts/studio.py direct --title "Tres campanas y una deuda" --seconds 22
→ 4 shots · 22.0 s · style cinematic (historia con personajes y duración media)
→ narration=template approval_required=True
→ overlays=2 numeric=0 sources=0
```

The spec, manifest, brief and board plan were written and four stills rendered.
The narration is flagged as a template: the pipeline generated a plan, not prose.

### 10.4 Defects found and fixed in this cycle

1. **Panel over the caption band.** The Python validator used default boxes and
   ignored `placement.box`; several defaults (panel, bar, line, donut, ranking,
   process) also reached past 0.855. Both fixed; re-inspection: 0/4 flags.
2. **Chart and arrow overlapped** in S03. The arrow moved out of the chart box;
   the overlap warning is gone.
3. **Kokoro worker would not start** (`attempted relative import with no known
   parent package`): `scripts/acs` on `sys.path` shadowed numpy's bootstrap. Both
   the probe and the synthesis now pass `-P`. Voice then ran: 4/4 lines.
4. **Inspector false positive on captions.** It measured a percentile of the
   whole band; it now measures local contrast in 12×4 cells. Verified on the
   test images and on the render (spread 205–220 vs 35 before the fix).

All four are recorded in `feedback/records.jsonl` as FB-0001…FB-0004 with
validation evidence, and the documents were regenerated from the store.

### 10.5 What this does not prove

- **No human aesthetic review.** Composition is measured as emptiness/detail/
  depth proxies; acting and narrative are explicitly `pending`.
- **Render speed is a real cost:** ~16 minutes for 624 frames at 1080×1920 with
  concurrency 6 on this machine. I suspected the panel `backdrop-filter` and
  removed it, but the render had already completed, so **the difference was not
  measured**; the filter is back in the source and the cost is reported as-is.
- No comparison against ElevenLabs, no lip-sync, no style-specific asset packs.
- The demo uses `illustrative: true` on its bar chart: those numbers are the
  character's count, not a statistic about a real place.

---

## 11. 0.7.0 — Dirección de UI (`projects/ui_direccion`)

Ejecutado en esta máquina el 2026-11-04. La entrega no se declara por tests: se
renderizó, se mezcló, se midió el MP4 y se miraron los fotogramas.

### Entrega

```
projects/ui_direccion/output/final_video.mp4   27.4 s · 1080×1920 · 30 fps · 822 frames · 14.2 MB
projects/ui_direccion/output/final_video_preview.mp4   540×960 · 1.3 MB
projects/ui_direccion/output/picture_silent.mp4        18.4 MB · render 609.87 s
projects/ui_direccion/generation/audio/score.wav       27.4 s · RMS −17.31 dBFS
projects/ui_direccion/generation/audio/mix.wav         27.4 s · 5.3 MB · sidechain 0.04 / 10 / 12 ms / 300 ms
projects/ui_direccion/quality/{visual_inspection.md,evaluation.md}
```

### Pruebas

```
python -m pytest tests -q          119 passed in 50.83 s
cd studio && npx tsc --noEmit      exit 0
python scripts/studio.py qa        PASS · 12/12 checks
python scripts/studio.py inspect   0/8 planos marcados · UI 0 problemas / 0 avisos · exit 0
python scripts/studio.py evaluate  9 medidas PASS · 4 pending · exit 0
```

QA: 822 frames, H.264 1080×1920 @ 30, AAC 48 kHz estéreo, duración 27.4 s
(delta 0.000 s), motion 9.905, black 0.0, freeze 0.1606, loudness −13.5 dB
(media, no LUFS), audio activity 0.275.

### Evidencia del render (muestreo del MP4)

| modo | planos | detalle de escena | contraste de UI |
|---|---|---|---|
| A | 2 | 3.00 | — |
| B | 2 | 3.96 | 115.5 |
| C | 1 | 4.04 | — (sin caja declarada) |
| D | 1 | 3.86 | 164.0 |
| E | 1 | 3.93 | 31.0 |
| F | 1 | 1.44 | 24.0 |

### Antes / después

| Métrica | `sistema_demo` (0.6) | `ui_direccion` (0.7) |
|---|---|---|
| Elementos de UI | 7 | 6 |
| Sobre el cuerpo (B/C) | 3 (máx. 4.7 % del encuadre) | 0 |
| Sobre una cara | 2 | 0 |
| Sobre subtítulos | 0 | 0 |
| Sigue tras 0.90 en B/C | 1 | 0 |

### Lo que sigue fallando

- E y F son placas deliberadamente planas; `composition` no las puntúa como
  escena, pero su equilibrio es una decisión estética sin revisión humana.
- La caja se resuelve una vez por plano: un paneo largo puede acercar un cuerpo
  a la UI a mitad de plano.
- Las etiquetas ancladas al actor no tienen caja declarada, así que su contraste
  no se mide (la inspección geométrica sí comprueba que no tapen la cara).
- 4 dimensiones (narrativa, actuación, ritmo, integridad de estilo) siguen
  `pending`: no se inventó una nota.

---

## 12. 0.8.0 — Identidad y narración (2026-11-05)

La entrega se midió sobre el MP4, no sobre los tests. El primer intento de render
por el proveedor quedó bloqueado sin escribir log ni actualizar la salida; se
detuvo y se renderizó la misma composición con el CLI directo
(`npx remotion render`), sin cambiar manifest ni pipeline.

### Entrega

```
projects/ui_direccion/output/final_video.mp4         27.4 s · 822 frames · 14.1 MB · 1080×1920 · 30 fps
projects/ui_direccion/output/final_video_preview.mp4 540×960 · 1.3 MB
projects/ui_direccion/output/picture_silent.mp4      18.2 MB · RENDER_EXIT=0
projects/ui_direccion/generation/voice/voice.wav     23.34 s de habla · 8 líneas
projects/ui_direccion/generation/audio/mix.wav       27.4 s · sidechain duck
projects/ui_direccion/preproduction/identity_sheet.png
projects/ui_direccion/quality/identity_shots.png
projects/ui_direccion/quality/identity_audit.md
projects/ui_direccion/quality/narration_validation.md
```

QA (`studio.py qa`): **PASS 12/12** — H.264 1080×1920 @ 30, AAC 48 kHz estéreo
191 kb/s, 822 frames, duración 27.4 s (delta 0.000), motion 9.923, black 0.0,
freeze 0.1606, loudness −13.5 dB, audio_activity 0.202, caption_plan 1.0.

`inspect`: **0/8 planos marcados**, UI 0 problemas / 0 avisos.
`evaluate`: **9 dimensiones medidas PASS, 4 pendientes** (narrativa, actuación,
ritmo, integridad de estilo); sin nota global.

### Identidad

Causa: `cast.json` declaraba `height` y silueta, pero el rig no usaba ninguno de
los dos; además la banda del gorro se dibujaba en `-0.36H..-0.10H`, sobre la
línea de los ojos. El resultado no era «otro asset»: era un cuerpo compartido y
una cara sin ojos a poca distancia.

Corrección: la altura de identidad se aplica antes de la escala del plano, y las
anclas de UI (Python y TypeScript) usan el mismo factor; la banda pasa al borde
del gorro (`-0.52H..-0.27H`).

| Comprobación | Antes | Después |
|---|---|---|
| Altura del aprendiz | 0.92 declarada, no aplicada | 8 % más bajo que el guardián |
| Ojos en S01/S02/S04/S07 | tapados por la banda | visibles y alineados |
| Identidad canónica | no auditada | 3 personajes, 0 problemas, 1 aviso (widow sin uso) |
| Overrides de identidad por plano | no comprobados | 0; el test falla si aparecen |

Evidencia visual: `identity_sheet.png` (siete poses) y `identity_shots.png`
(el mismo personaje recortado en S01/S02/S04/S06 y S04/S07; S08 se excluye
porque la tarjeta F lo tapa a propósito).

### Narración

Voz: Kokoro local, español. Narrador `ef_dora` (0.98), guardián `em_alex` (0.92),
aprendiz `em_santa` (1.05). Texto exacto, en orden:

1. Aquella noche, el guardián no tocó la campana.
2. El pueblo llevaba tres inviernos sin oírla.
3. El aprendiz subió al campanario con una cuerda.
4. Comparó lo que el pueblo creía con lo que vio.
5. El mecanismo tenía tres pasos.
6. El tercero era el que nadie miraba.
7. El aprendiz señaló la cuerda que faltaba.
8. Desde entonces, el silencio tuvo fecha.

`voicecheck`: **OK** — 8 líneas, 58 palabras, 23.34 s de habla, 0 problemas.
En el MP4 final, cada ventana de voz está 11.5–19.3 dB por encima del lecho
duckado, salvo S08 (5.4 dB, el cierre bajo la tarjeta). S01 y S03 recortan 0.16 s
de cola en el stem (fundido de 20 ms) para no sumar dos tomas en el corte.

### Pruebas

```
python -m pytest tests -q       128 passed in 48.55 s
cd studio && npx tsc --noEmit   exit 0
python scripts/studio.py identity   OK
python scripts/studio.py voicecheck OK
python scripts/studio.py qa         PASS 12/12
python scripts/studio.py inspect    0/8
python scripts/studio.py evaluate   9 PASS · 4 pending
```

### Lo que sigue pendiente

- Captions quemados: sincronizados por plano, no palabra a palabra; el renderer
  no lee `words.json` (item abierto del roadmap).
- Perfil y tres cuartos son desplazamiento 2D de rasgos, no otra cabeza; el
  cuerpo sigue siendo un solo rig (altura sí, silueta no).
- `voicecheck` mide señal, no inteligibilidad: no hay ASR; escuchar sigue siendo
  necesario.
- El mix intermedio llega a 0.0 dBFS en S04; el MP4 se limita con loudnorm.
- Renders futuros: usar el CLI directo si el proveedor vuelve a bloquearse.

## 13. 0.9.0 — Dirección audiovisual (2026-11-05)

La entrega se midió sobre el MP4 final, no sobre el plan. Hubo dos renders
intermedios: el primero se detuvo al detectar que la demo había reescrito cuatro
líneas del guion original; el segundo se descartó porque S06/S08 usaban la placa
`faceCloseup` y la inspección las marcó como escenas vacías. El render entregado
usa las ocho líneas originales y las escenas corregidas.

### Entrega

```
projects/av_direccion/output/final_video.mp4          30.933 s · 927 frames · 17.5 MB · 1080×1920 · 30 fps
projects/av_direccion/output/final_video_preview.mp4  540×960 · 1.6 MB
projects/av_direccion/output/picture_silent.mp4       23.3 MB · 928 frames renderizados
projects/av_direccion/generation/audio/mix.wav        30.93 s · sidechain duck · music_gain 0.20
projects/av_direccion/preproduction/av_plan.md        10 planos · beats · escalas · motivos
projects/av_direccion/quality/before_after.md         comparación estructural con ui_direccion
projects/av_direccion/quality/before_contact.jpg      fotogramas reales del baseline
projects/av_direccion/quality/after_contact.jpg       fotogramas reales de la demo
```

### QA técnico

`studio.py qa`: **PASS 11/11** — H.264 1080×1920 @ 30, AAC 48 kHz estéreo
190,8 kb/s, 927 frames, duración 30.933 s (delta 0.003), motion 10.246, black 0.0,
freeze 0.069, loudness −12.7 dB, audio_activity 0.195, caption_plan 0.874.

`inspect`: **0/10 planos marcados**, 0 problemas / 0 avisos de UI.
`evaluate`: **10 dimensiones medidas PASS, 4 pendientes** (narrativa, actuación,
ritmo, integridad de estilo); sin nota global. `montage` entra como dimensión
medida desde `quality/av_audit.json`.

### QA creativo estructural

`studio.py avqa`: **sin fallos estructurales**, 13 comprobaciones medidas. La
demo tiene hook, setup, desarrollo, insert, escalada, reacción, dos revelaciones
y cierre; 4 escalas, racha máxima 1, 8 cámaras distintas, 9/9 movimientos
motivados, 2/2 disolvencias motivadas, 9/10 planos con audio y 5/10 con acción.
Narrativa, actuación, ritmo y gusto siguen pendientes de revisión humana.

### Antes / después

| Métrica | `ui_direccion` | `av_direccion` |
|---|---|---|
| planos | 8 | 10 |
| duración | 27.4 s | 30.933 s |
| media por plano | 3.42 s | 3.09 s |
| escalas distintas | 4 | 4 |
| racha máxima de escala | 3 | 1 |
| cámaras distintas | 7 | 8 |
| planos con acción | 2 | 5 |
| planos de reacción | 0 | 1 |
| eventos de audio | 7 | 15 |
| motivos de cámara | 0/7 | 9/9 |
| fallos estructurales | 3 | 0 |

La métrica de motion sube de 9.923 a 10.246 y freeze baja de 0.1606 a 0.069,
pero no se usa como prueba de calidad cinematográfica: el modelo es
SAD/traslación, no entiende acting ni composición.

### Revisión visual

Los contact sheets de ambos MP4 muestran la diferencia real: la nueva demo añade
un plano de reacción en el umbral, una pausa sobre la campana, un dos-planos para
el mecanismo, un close-up del aprendiz en el pueblo y un cierre en el campo.
S06/S08 ya no son placas bokeh vacías. Persisten el estilo vectorial plano, la
falta de detalle de props y la actuación por presets; el insert S04 es quieto a
propósito y se mide aparte (`declared_insert_max`).

### Pruebas

```
python -m pytest tests -q       136 passed in 38.41 s
cd studio && npx tsc --noEmit   exit 0
python scripts/studio.py avqa   sin fallos estructurales
python scripts/studio.py qa     PASS 11/11
python scripts/studio.py inspect 0/10
python scripts/studio.py evaluate 10 PASS · 4 pending
```

### Lo que sigue pendiente

- Revisión humana de narrativa, actuación y ritmo. El QA estructural no la sustituye.
- S04 conserva 60,3 % de teselas planas; es un insert declarado y se reporta aparte,
  no se usa para bajar el umbral global.
- La escala sigue siendo una etiqueta directorial sobre un rig 2.5D, sin lente ni
  profundidad de campo real.
- El aprendiz “señala la cuerda” con un preset de brazo; no hay IK ni mano anclada
  al prop.
- Captions quemados siguen sincronizados por plano, no palabra a palabra.

---

## 14. 0.10.0 — Shared asset system (`projects/asset_forge`)

Ejecutado en esta máquina el 2026-11-05. No se generó vídeo para este prompt.

### Entregado

```
assets/registry.json                                  schema 2, versiones y procedencia
assets/references.json                                biblioteca persistente de referencias
assets/generated/set/laboratorio/v1|v2/               fondo diurno + variación nocturna
assets/generated/character/cientifico/v1/             personaje nuevo
assets/generated/expression/surprise_cientifico/v1/   expresión reutilizable
assets/generated/prop/lampara_laboratorio/v1/         prop nuevo
assets/generated/motion_graphic/comparacion/v1|v2/    gráfico animado
projects/asset_forge/spec.json + manifest.json        proyecto de prueba compuesto por catálogo
projects/asset_forge/preview/A01_generated.png        still: set + personaje + expresión + prop + gráfico
projects/asset_forge/preview/A02_existing.png         still: doorway + elder existentes
projects/asset_forge/preview/contact_sheet.jpg        hoja de contacto revisada visualmente
```

### Pruebas

```
python -m pytest tests -q       148 passed in 44.00 s
cd studio && npx tsc --noEmit   exit 0
python scripts/studio.py assets validate
                                38 assets checked, OK
node scripts/acs/storyboard.mjs ...
                                A01_generated A02_existing, exit 0
```

### Evidencia

La inspección visual de los stills confirma: fondo nocturno generado, personaje
nuevo con expresión de sorpresa, lámpara en primer plano, gráfico de comparación
en la zona superior segura, y el plano A02 con `set:doorway` +
`character:elder` reutilizados. La primera pasada visual detectó dos defectos
reales (la variación nocturna no aplicaba la paleta y el gráfico tapaba la cara);
se corrigieron, se regeneraron las versiones afectadas y se volvió a renderizar.

### Límites que siguen abiertos

- El forge es un compositor vectorial local, no un generador de imágenes.
- La gramática de sets es laboratorio-céntrica; otras localizaciones necesitan
  una gramática nueva en el mismo renderer.
- Los personajes usan el rig existente; no hay anatomía nueva.
- Los previews de assets son SVG; la evidencia pixelada son los stills.
- No se generó MP4 en este prompt.

---

## 15. 0.10.1 — Recuperación de historia y narración (2026-11-05)

Ejecutado sobre `projects/av_direccion_story`, sin UI y sin un segundo pipeline.
La entrega se midió sobre el MP4 ensamblado, no sobre el manifiesto.

### Entrega

```
projects/av_direccion_story/output/final_video.mp4          30.933 s · 927 frames · 17.3 MB
projects/av_direccion_story/output/final_video_preview.mp4   1.6 MB · 540×960
projects/av_direccion_story/output/picture_silent.mp4       23.3 MB · 928 frames renderizados
projects/av_direccion_story/generation/voice/voice.wav      31.183 s · 8 líneas · 23.09 s de habla
projects/av_direccion_story/generation/audio/mix.wav        30.933 s · music_gain 0.20
projects/av_direccion_story/quality/final_contact.jpg       hoja de 10 fotogramas revisada
```

`ffprobe`: H.264 1080×1920 @ 30 fps, 927 frames; AAC 48 kHz estéreo, 190.8 kb/s,
30.933 s. El render silencioso tiene 928 frames; el mux descarta el último.
El render por `studio.py render --manifest` tardó **1464.45 s** (24 min 24 s).

### Pruebas

```
python -m pytest tests -q          159 passed in 37.35 s
cd studio && npx tsc --noEmit      exit 0
python scripts/studio.py qa        PASS 12/12
python scripts/studio.py voicecheck OK · 8 líneas · 58 palabras · 23.09 s
python scripts/studio.py avqa      13 comprobaciones, sin fallos estructurales
python scripts/studio.py inspect   0/10 planos marcados · UI A · 0 overlays
python scripts/studio.py evaluate  10 dimensiones medidas PASS · 4 pendientes
python scripts/studio.py identity  OK · 4 personajes · 0 problemas
```

La única advertencia de `voicecheck` es S01: la toma corre 0.04 s más que el
siguiente inicio y el stem la recorta. No hay voz de personaje, no hay frases
duplicadas y no hay audio truncado.

### Audio

- Una sola voz: `ef_dora` en las 8 líneas.
- `voice.wav` 31.183 s; última línea termina en 30.188 s; `mix.wav` 30.933 s.
- El WAV de 18.45 s que se citó en el encargo **no es el stem de este MP4**:
  el archivo de 18.45 s presente en el workspace pertenece a `projects/kokoro_demo`.
  La duración de este vídeo se explica por 8 líneas de narración, no por un
  recorte de audio; el `audio_duration` de QA lo comprueba.
- `mix` a `music_gain=0.20`: **5** ventanas dentro de 3 dB de la voz, frente a
  47 con la ganancia por defecto 0.45. El mix no está silenciado; el MP4 tiene
  stream AAC y `audio_activity=0.195`.

### Identidad y proporciones

La auditoría estructural pasa con `head/body`: elder 0.541, young 0.518, widow
0.529, dentro de la banda 0.35–0.65. La hoja de identidad de siete poses y la
hoja de recortes por plano se revisaron; el contact sheet final muestra el mismo
abrigo, gorro, cara y silueta en los 10 planos. La diferencia de tamaño entre
personajes en un plano se explica por la escala/posición declaradas, no por un
redibujo. No se añadió una métrica de píxeles ni un face embedding.

### Revisión visual del MP4

`quality/final_contact.jpg` y fotogramas en `quality/frames/` fueron revisados:
no hay tarjetas, gráficos ni UI explicativa; solo subtítulos de historia. Los
personajes mantienen proporciones, vestuario y props; la campana, el pueblo, la
puerta y el campo son continuos. Los subtítulos del contact sheet aparecen
partidos porque cada muestra cae dentro de un chunk de 2–3 palabras, no porque
falte texto.

### Lo que no prueba

- No hay ASR ni escucha humana registrada: la inteligibilidad sigue siendo una
  comprobación manual.
- No hay lip-sync; la boca es una forma paramétrica.
- Las 4 dimensiones subjetivas (narrativa, actuación, ritmo, integridad de
  estilo) siguen pendientes.
- La auditoría de identidad es estructural y de proporción, no perceptiva.
- La puerta de dos renders consecutivos con log streaming sigue abierta: este
  pase completó uno.

---

## 0.10.2 — auditoría y subtítulos con reloj real (2026-11-06)

Ejecutado en esta máquina sobre el árbol de trabajo posterior a `5eaec1e`.

| Comprobación | Comando | Resultado |
|---|---|---|
| Suite Python | `python -m pytest tests -q` | **167 passed**, 288 warnings de Pillow, 73.47 s |
| TypeScript | `cd studio && npx tsc --noEmit` | exit 0 |
| Tests nuevos | `python -m pytest tests/test_captions.py -q` | **8 passed**, 0.33 s |
| Subtítulos | `studio.py captions --dry-run` | 8 planos, 23 cues, **0 ms** de error (gate 120 ms) |
| Storyboard real | `studio.py storyboard --scale 0.35` | 10 stills + contact sheet, **54 s** |
| Restauración de manifest | SHA-256 antes/después | `2af5cfb4a38a5915` sin cambios |
| Narración | `studio.py voicecheck` | **OK**, 8 líneas, 58 palabras, 23.09 s |
| QA de entrega | `studio.py qa` | **PASS 12/12** |

### Lo que este pase no prueba

- El MP4 entregado no se re-renderizó: sus subtítulos quemados son del build
  anterior. La evidencia de render del camino nuevo es el storyboard.
- El error de 0 ms es contra `voice_plan.json` (`pred_dur`), no contra la señal
  acústica; no hay ASR ni alineación forzada.
- No hay OCR ni frame-diff que confirme qué chunk se ve en qué fotograma.
- La puerta de dos renders completos sigue abierta (24 min por render).

### Rendimiento medido

927 frames en 1464.45 s = **38 frames/min (0.63 fps)**, no los ~500 frames/min
que afirmaba `LIMITATIONS.md`. La cifra está corregida y el perfilado queda como
siguiente paso en `quality/repository_audit/performance.md`.

---

## 0.10.3 — Reparación de audio, lock y determinismo (2026-11-06)

### Qué se probó

| Comprobación | Comando | Resultado |
|---|---|---|
| Suite completa | `python -m pytest tests -q` | **174 passed**, 288 warnings de Pillow, 68.06 s |
| TypeScript | `cd studio && npx tsc --noEmit` | exit 0 |
| Tests de audio/lock | `python -m pytest tests/test_audio_integrity.py -q` | **7 passed**, 2.10 s |
| Narración | `studio.py voicecheck` | **OK**, 8 líneas, 58 palabras, 23.09 s; mix-voz **0.8985** |
| Voz en la entrega | `qa.voice_in_delivery` | **0.9209** (gate 0.35) |
| QA de entrega | `studio.py qa` | **PASS 13/13** |
| Mix | `studio.py mix --margin 3` | **3 ventanas** dentro de 3 dB; `mix_check.md` regenerado |
| MP4 | `ffprobe` | 30.933 s, 1080×1920, 30 fps, AAC 48 kHz estéreo, 17.279.149 bytes |
| Determinismo del mix | SHA-256 de dos regeneraciones | `6fb129fa9384dd4aed6f18dc` idéntico |
| Determinismo corto | dos renders de 30 frames por el mismo camino | PSNR **53.12 dB**, SSIM **0.99696**, diferencia media **0.39/255** |
| Lock de manifest | segundo render concurrente | `ManifestBusy` en 5 s; manifest activo intacto |

### Defecto de audio corregido

El MP4 anterior correlacionaba **0.987** con su mix pero **0.0002** con
`voice.wav`: sonaba la música, no la narración. El grafo FFmpeg reutilizaba la
voz como sidechain y como entrada de `amix`, y referenciaba `[ducked]` dos
veces. `mixdown.py` se reescribió como mezclador NumPy determinista; `assemble`
prefiere `mix.wav`; QA mide la voz dentro del MP4. El video se reensambló y la
narración está presente.

### Lo que este pase no prueba

- No se re-renderizaron los 927 frames: el MP4 conserva los subtítulos quemados
  del build anterior. La evidencia del camino nuevo sigue siendo el storyboard.
- La puerta de dos renders **completos** sigue abierta; la de 30 frames pasa con
  diferencia sub-píxel de rasterizado (Chrome re-rasteriza el grano SVG), no con
  MD5 exacto.
- No hay OCR/ASR: los 0 ms de subtítulos son contra el plan `pred_dur`, y la
  correlación de voz prueba señal, no inteligibilidad.

---

## 0.10.4 — Dirección, continuidad y demo renderizada (2026-11-06)

### Qué se añadió

- `cameraIntensity` por plano y movimiento `handheld`; presets de actuación
  `point` y `react`.
- Checks creativos nuevos: orden de beats, encuadre por beat, eje entre dos
  actores, intención de planos estáticos, propósito de cada plano, densidad de
  habla e intensidad de cámara.
- Comparación antes/después normalizada por plano, no por duración.
- Fades de 80/120 ms en la mezcla.

### Demo `projects/av_direccion_demo/`

| Comprobación | Comando | Resultado |
|---|---|---|
| Plan | `studio.py av` | 6 planos, **20,433 s**, 10 cues, QA creativo sin fallos |
| Voz | `studio.py voicecheck` | **OK**, 5 líneas, 36 palabras, 15,15 s |
| Subtítulos | `studio.py captions` | 5 planos, 14 cues, **0 ms** de error (gate 120 ms) |
| Mezcla | `studio.py mix --margin 3` | **1 ventana** dentro de 3 dB a `music_gain=0.14` |
| Render | `studio.py render` | **613 frames en 751,16 s** |
| Entrega | `ffprobe` | 20,433 s, 1080×1920, 30 fps, AAC 48 kHz, 11.021.347 bytes |
| QA técnico | `studio.py qa` | **PASS 13/13**; voz en entrega **0,9273**; motion **8,853** |
| Inspección | `studio.py inspect` | **0/6** planos marcados; overlays OK; UI A |
| Evaluación | `studio.py evaluate` | **10 medidas / 4 humanas pendientes**, sin fallos medidos |
| Suite | `python -m pytest tests -q` | **178 passed**, 46,71 s |
| TypeScript | `npx tsc --noEmit` | exit 0 |

### Antes / después (normalizado)

| Métrica | Relato 10 planos | Demo 6 planos |
|---|---|---|
| Acción por plano | 0,50 | **0,833** |
| Dos actores por plano | 0,30 | **0,667** |
| Variedad de cámara por plano | 0,80 | **1,00** |
| Variedad de escala por plano | 0,40 | **0,667** |
| Densidad máxima de habla | 2,778 palabras/s | **2,286** |
| Violaciones de eje | 0 | **0** |

### Lo que no prueba

- La demo es más corta que el relato: la comparación normalizada evita premiar
  o castigar por duración, pero no convierte 6 planos en una película de 10.
- No hay revisión humana de narrativa, actuación, ritmo o estilo; `evaluate` las
  deja pendientes.
- No hay OCR/ASR, lip-sync, geometría over-the-shoulder/POV ni IK de contacto.
- El render es una sola pasada; la puerta de dos renders completos sigue abierta.

---

## 0.10.5 — Acción compuesta y movimiento por plano (2026-11-07)

### Cambios verificados

- `ActorSpec.sequence` ordena presets existentes en una acción compuesta; S02 es
  `walkIn → turn` y S03 es `turn → reach`.
- El planificador rechaza ventanas inválidas y solapamientos; `avqa` añade
  `action_completion` y falla si la secuencia termina en `walkIn`.
- `motion.analyze_shots` mide cada plano visible y `qa` escribe `shot_motion` con
  energía, proporción en movimiento, pan/tilt y `low_motion`.

### Evidencia de la demo

| Comprobación | Comando | Resultado |
|---|---|---|
| Plan | `studio.py av` | 6 planos, 20,433 s, **2 secuencias / 4 fases**, QA sin fallos |
| Render | `studio.py render` | **613 frames en 500,47 s** |
| Entrega | `ffprobe` | 20,433 s, 1080×1920, 30 fps, 11.024.558 bytes, 612 frames |
| QA técnico | `studio.py qa` | **PASS 13/13**; voz **0,9273**; motion **8,858** |
| Movimiento por plano | `qa.shot_motion` | mínimo **2,438**, media **4,249**, **0 low-motion** |
| Inspección | `studio.py inspect` | **0/6** planos marcados; overlays OK |
| QA creativo | `studio.py avqa` | **20/20**, sin fallos; acción compuesta completa |
| Evaluación | `studio.py evaluate` | **10 medidas / 4 humanas pendientes** |
| Suite | `python -m pytest tests -q` | **181 passed**, 73,97 s |
| TypeScript | `npx tsc --noEmit` | exit 0 |

La tira de frames `quality/action_sequence.jpg` muestra S02/S03 en el MP4 final.
La revisión visual confirma la continuidad de las fases; no sustituye una
revisión humana de actuación.

### Lo que no prueba

- Las fases interpolan parámetros de presets; no hay IK, contacto de props ni
  visemas.
- La secuencia es intra-plano; el estado entre planos sigue declarado en el
  manifiesto.
- El movimiento por plano es un modelo de traslación; `low_motion` es un
  diagnóstico, y S04 (reacción sostenida) es intencionalmente tranquilo.

---

## 0.10.6 — Continuidad de personajes y nueva historia (2026-11-07)

### Cambios verificados

- `av_director` mantiene un ledger por actor y baja `entry`/`exit` a
  `manifest.continuity.states`; `carry` hereda `x`, `facing` y `hold`.
- `carry` se rechaza al cambiar de escena; un salto de más de 260 px en la misma
  escena exige `continuityMotive`.
- `avqa.character_continuity` audita estados heredados, saltos sin motivo y
  ledger ausente; los tests cubren herencia, rechazo entre escenas y teleport.
- `Workshop.tsx` añade un set no invernal; `projects/av_ultima_medida/` usa
  únicamente ese set y una estructura narrativa distinta.

### Evidencia de la demo

| Comprobación | Comando | Resultado |
|---|---|---|
| Plan | `studio.py av` | 6 planos, 22,4 s, **5 estados heredados**, 3 secuencias / 6 fases |
| Render | `studio.py render` | **672 frames**, 1080×1920, 30 fps |
| Entrega | `ffprobe` | 22,4 s, H.264/AAC, **11.989.156 bytes** |
| QA técnico | `studio.py qa` | **PASS 13/13**; voz **0,9267**; motion **4,034**; freeze **0,1042**; loudness **−17,0 dB** |
| Continuidad | `studio.py avqa` | `carried: 5`, `continuity_issues: []`, 3 secuencias / 6 fases |
| Inspección | `studio.py inspect` | **0/6** planos marcados; overlays OK |
| Evaluación | `studio.py evaluate` | **10 medidas / 0 fallos / 4 humanas pendientes** |
| Storyboard | `studio.py storyboard` | 6 key frames; empty ratio 0,472–0,524 |
| Suite | `python -m pytest tests -q` | **184 passed**, 110,92 s |
| TypeScript | `npx tsc --noEmit` (desde `studio/`) | exit 0 |

La tira `projects/av_ultima_medida/quality/continuity_strip.jpg` se abrió y
revisó: S01–S03 mantienen el taller y el bloqueo del sastre/aprendiz; S04 es un
close-up del mismo taller; S05–S06 conservan la posición y no reaparecen nieve ni
campana. La revisión visual no sustituye la evaluación humana de narrativa,
actuación, ritmo y estilo.

### Lo que no prueba

- `carry` es estado de planificación; el renderer no conserva un cuerpo entre
  `<Sequence>` y no hay IK, contacto físico de props ni comprobación de píxeles.
- El guard de 260 px está calibrado para este escenario; no es una regla universal.
- La comparación con el vídeo anterior es estructural y visual, no una prueba a
  ciegas ni una puntuación de entretenimiento: `quality/comparison.md`.
- `evaluate` deja 4 dimensiones subjetivas pendientes.
