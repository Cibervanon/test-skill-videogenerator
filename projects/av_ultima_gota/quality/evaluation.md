# Evaluation — av_ultima_gota

**sin fallos medidos** · 10 medidas · 4 pendientes

| dimensión | tipo | estado | valor | evidencia |
|---|---|---|---|---|
| ui_composition | geometry + timing (manifest) | ✅ measured | `A=7` | 0 problema(s), 0 aviso(s) en 0 elemento(s) |
| composition | automatic (pixels) | ✅ measured | `empty_ratio_max=0.405, subject_min=2.457` | 0 plano(s) de escena (A–D) con más del 55% de teselas planas; E/F se evalúan como placa gráfica; 0 insert(s) de detalle declarados no se penalizan |
| legibility | automatic (pixels) | ✅ measured | `worst_spread=79.0, worst_edges=5.28` | 0 plano(s) con texto de riesgo |
| consistency | automatic (pixels) | ✅ measured | `palette_shift_max=0.102` | deriva de paleta respecto al estilo elegido |
| overlays | geometry (manifest) | ✅ measured | `—` | 0 problema(s), 0 aviso(s) |
| montage | structural (edit plan) | ✅ measured | `shots=7, seconds=26.3, average_shot_seconds=3.76, beat_counts={'hook': 1, 'setup': 1, 'escalation': 1, 'development': 2, 'reaction': 1, 'close': 1}, scale_counts={'detail': 1, 'medium': 4, 'wide': 1, 'close': 1}, scale_source=['declared'], longest_scale_run=2, camera_counts={'pushInSlow': 1, 'tiltUp': 1, 'trackRight': 1, 'panLeft': 1, 'reframe': 1, 'static': 1, 'dollyOut': 1}, moving_ratio=0.857, camera_motives=6/6, dissolve_motives=0/0, sound_shots=4, sound_cues=6, action_shots=5, phased_shots=2, action_phases=4, action_sequences=2, unfinished_sequences=[], sequence_issues=[], reaction_shots=1, two_actor_shots=3, axis_violations=[], carried_actors=1, continuity_issues=[], static_shots=1, static_ratio=0.143, framing_mismatches=[], purpose_missing=[], max_words_per_second=2.143, camera_intensity_invalid=[], wordless_shots=1, spoken_lines=6, actors_used=['elder', 'young'], scenes=['greenhouse']` | sin fallos estructurales |
| style_integrity | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| narrative | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| acting | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| rhythm | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| motion | automatic (qa) | ✅ measured | `5.226` | min 1.0 — guards against a slideshow of stills |
| technical | automatic (qa) | ✅ measured | `codec=h264, width=1080, height=1920, fps=30.0, fps_avg=30.0, pix_fmt=yuvj420p, frames=789, aspect=0.5625, orientation=vertical` | to spec |
| sound | automatic (qa) | ✅ measured | `-14.1` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| captions | automatic (qa) | ✅ measured | `0.897` | computed from the cue plan (shot lines), not from OCR of the render |

> No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.
