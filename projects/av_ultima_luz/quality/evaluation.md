# Evaluation — av_ultima_luz

**sin fallos medidos** · 10 medidas · 4 pendientes

| dimensión | tipo | estado | valor | evidencia |
|---|---|---|---|---|
| ui_composition | geometry + timing (manifest) | ✅ measured | `A=6` | 0 problema(s), 0 aviso(s) en 0 elemento(s) |
| composition | automatic (pixels) | ✅ measured | `empty_ratio_max=0.536, subject_min=3.393` | 0 plano(s) de escena (A–D) con más del 55% de teselas planas; E/F se evalúan como placa gráfica; 0 insert(s) de detalle declarados no se penalizan |
| legibility | automatic (pixels) | ✅ measured | `worst_spread=186.0, worst_edges=6.92` | 0 plano(s) con texto de riesgo |
| consistency | automatic (pixels) | ✅ measured | `palette_shift_max=0.116` | deriva de paleta respecto al estilo elegido |
| overlays | geometry (manifest) | ✅ measured | `—` | 0 problema(s), 0 aviso(s) |
| montage | structural (edit plan) | ✅ measured | `shots=6, seconds=21.3, average_shot_seconds=3.55, beat_counts={'hook': 1, 'setup': 1, 'escalation': 1, 'reaction': 1, 'reveal': 1, 'close': 1}, scale_counts={'detail': 1, 'medium': 4, 'close': 1}, scale_source=['declared'], longest_scale_run=2, camera_counts={'pushInSlow': 1, 'dollyIn': 1, 'trackRight': 1, 'static': 1, 'panRight': 1, 'dollyOut': 1}, moving_ratio=0.833, camera_motives=5/5, dissolve_motives=0/0, sound_shots=3, sound_cues=3, action_shots=4, phased_shots=2, action_phases=6, action_sequences=3, unfinished_sequences=[], sequence_issues=[], reaction_shots=1, two_actor_shots=3, axis_violations=[], carried_actors=0, continuity_issues=[], static_shots=1, static_ratio=0.167, framing_mismatches=[], purpose_missing=[], max_words_per_second=2.105, camera_intensity_invalid=[], wordless_shots=1, spoken_lines=5, actors_used=['elder', 'young'], scenes=['doorway']` | sin fallos estructurales |
| style_integrity | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| narrative | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| acting | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| rhythm | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| motion | automatic (qa) | ✅ measured | `5.912` | min 1.0 — guards against a slideshow of stills |
| technical | automatic (qa) | ✅ measured | `codec=h264, width=1080, height=1920, fps=30.0, fps_avg=30.0, pix_fmt=yuvj420p, frames=639, aspect=0.5625, orientation=vertical` | to spec |
| sound | automatic (qa) | ✅ measured | `-13.6` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| captions | automatic (qa) | ✅ measured | `0.873` | computed from the cue plan (shot lines), not from OCR of the render |

> No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.
