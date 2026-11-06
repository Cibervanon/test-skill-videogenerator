# Evaluation — ui_direccion

**sin fallos medidos** · 9 medidas · 4 pendientes

| dimensión | tipo | estado | valor | evidencia |
|---|---|---|---|---|
| ui_composition | geometry + timing (manifest) | ✅ measured | `A=2, B=2, D=1, E=1, C=1, F=1` | 0 problema(s), 0 aviso(s) en 6 elemento(s) |
| composition | automatic (pixels) | ✅ measured | `empty_ratio_max=0.512, subject_min=3.402` | 0 plano(s) de escena (A–D) con más del 55% de teselas planas; E/F se evalúan como placa gráfica |
| legibility | automatic (pixels) | ✅ measured | `worst_spread=166.0, worst_edges=7.83` | 0 plano(s) con texto de riesgo |
| consistency | automatic (pixels) | ✅ measured | `palette_shift_max=0.096` | deriva de paleta respecto al estilo elegido |
| overlays | geometry (manifest) | ✅ measured | `counter=2, bar=1, process=1, callout=1, label=1` | 0 problema(s), 1 aviso(s) |
| style_integrity | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| narrative | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| acting | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| rhythm | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| motion | automatic (qa) | ✅ measured | `9.923` | min 1.0 — guards against a slideshow of stills |
| technical | automatic (qa) | ✅ measured | `codec=h264, width=1080, height=1920, fps=30.0, fps_avg=30.0, pix_fmt=yuvj420p, frames=822, aspect=0.5625, orientation=vertical` | to spec |
| sound | automatic (qa) | ✅ measured | `-13.5` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| captions | automatic (qa) | ✅ measured | `1.0` | computed from the cue plan (shot lines), not from OCR of the render |

> No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.
