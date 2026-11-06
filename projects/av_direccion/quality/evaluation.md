# Evaluation — av_direccion

**sin fallos medidos** · 10 medidas · 4 pendientes

| dimensión | tipo | estado | valor | evidencia |
|---|---|---|---|---|
| ui_composition | geometry + timing (manifest) | ✅ measured | `A=10` | 0 problema(s), 0 aviso(s) en 0 elemento(s) |
| composition | automatic (pixels) | ✅ measured | `empty_ratio_max=0.603, subject_min=2.828, declared_insert_max=0.603` | 0 plano(s) de escena (A–D) con más del 55% de teselas planas; E/F se evalúan como placa gráfica; 1 insert(s) de detalle declarados no se penalizan |
| legibility | automatic (pixels) | ✅ measured | `worst_spread=30.0, worst_edges=3.32` | 0 plano(s) con texto de riesgo |
| consistency | automatic (pixels) | ✅ measured | `palette_shift_max=0.108` | deriva de paleta respecto al estilo elegido |
| overlays | geometry (manifest) | ✅ measured | `—` | 0 problema(s), 0 aviso(s) |
| montage | structural (edit plan) | ✅ measured | `shots=10, seconds=30.933, average_shot_seconds=3.09, beat_counts={'hook': 1, 'setup': 1, 'development': 2, 'insert': 1, 'reaction': 1, 'reveal': 2, 'escalation': 1, 'close': 1}, scale_counts={'detail': 2, 'close': 3, 'wide': 2, 'medium': 3}, scale_source=['declared'], longest_scale_run=1, camera_counts={'tiltUp': 1, 'pushInSlow': 2, 'panRight': 1, 'static': 1, 'drift': 1, 'dollyIn': 2, 'trackRight': 1, 'dollyOut': 1}, moving_ratio=0.9, camera_motives=9/9, dissolve_motives=2/2, sound_shots=9, sound_cues=15, action_shots=5, reaction_shots=1, two_actor_shots=3, wordless_shots=2, spoken_lines=8, actors_used=['elder', 'young'], scenes=['bellInsert', 'doorway', 'fieldDawn', 'townNight']` | sin fallos estructurales |
| style_integrity | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| narrative | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| acting | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| rhythm | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| motion | automatic (qa) | ✅ measured | `10.246` | min 1.0 — guards against a slideshow of stills |
| technical | automatic (qa) | ✅ measured | `codec=h264, width=1080, height=1920, fps=30.0, fps_avg=30.0, pix_fmt=yuvj420p, frames=927, aspect=0.5625, orientation=vertical` | to spec |
| sound | automatic (qa) | ✅ measured | `-12.7` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| captions | automatic (qa) | ✅ measured | `0.874` | computed from the cue plan (shot lines), not from OCR of the render |

> No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.
