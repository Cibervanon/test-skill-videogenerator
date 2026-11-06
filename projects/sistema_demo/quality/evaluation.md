# Evaluation — sistema_demo

**sin fallos medidos** · 8 medidas · 4 pendientes

| dimensión | tipo | estado | valor | evidencia |
|---|---|---|---|---|
| composition | automatic (pixels) | ✅ measured | `empty_ratio_max=0.417, subject_min=3.174` | 0 plano(s) con más del 55% de teselas planas |
| legibility | automatic (pixels) | ✅ measured | `worst_spread=183.0, worst_edges=14.68` | 0 plano(s) con texto de riesgo |
| consistency | automatic (pixels) | ✅ measured | `palette_shift_max=0.12` | deriva de paleta respecto al estilo elegido |
| overlays | geometry (manifest) | ✅ measured | `label=1, hud=1, callout=1, badge=1, bar=1, arrow=1, panel=1` | 0 problema(s), 1 aviso(s) |
| style_integrity | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| narrative | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| acting | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| rhythm | subjective | ⏳ pending | `None` | sin revisión humana: no se puntúa |
| motion | automatic (qa) | ✅ measured | `8.769` | min 1.0 — guards against a slideshow of stills |
| technical | automatic (qa) | ✅ measured | `codec=h264, width=1080, height=1920, fps=30.0, fps_avg=30.0, pix_fmt=yuvj420p, frames=602, aspect=0.5625, orientation=vertical` | to spec |
| sound | automatic (qa) | ✅ measured | `-12.8` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| captions | automatic (qa) | ✅ measured | `1.0` | computed from the cue plan (shot lines), not from OCR of the render |

> No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.
