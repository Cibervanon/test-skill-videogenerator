# Before / after — av_ultima_medida → av_ultima_gota

| métrica | antes | después | delta |
|---|---|---|---|
| planos | 6 | 7 | +1 |
| duración (s) | 22.4 | 26.3 | +3.9 |
| media por plano (s) | 3.73 | 3.76 | +0.03 |
| escalas distintas | 4 | 4 | +0 |
| racha máxima de escala | 1 | 2 | +1 |
| cámaras distintas | 6 | 7 | +1 |
| proporción en movimiento | 0.833 | 0.857 | +0.024 |
| planos con acción | 4 | 5 | +1 |
| planos con secuencia | 3 | 2 | -1 |
| fases de acción | 6 | 4 | -2 |
| planos de reacción | 1 | 1 | +0 |
| planos con audio | 3 | 4 | +1 |
| eventos de audio | 5 | 6 | +1 |
| planos con dos actores | 4 | 3 | -1 |
| planos estáticos | 1 | 1 | +0 |
| densidad máxima de habla | 3.429 | 2.143 | -1.286 |
| violaciones de eje | 0 | 0 | +0 |
| acción por plano | 0.667 | 0.714 | +0.047 |
| dos actores por plano | 0.667 | 0.429 | -0.238 |
| variedad de cámara por plano | 1.0 | 1.0 | +0 |
| variedad de escala por plano | 0.667 | 0.571 | -0.096 |
| eventos de audio por segundo | 0.223 | 0.228 | +0.005 |

Fallos estructurales: antes `ninguno` · después `ninguno`
Pendiente de juicio humano: `['narrative', 'acting', 'rhythm', 'style_integrity']`

> structural comparison; narrative, acting and taste still require human review.

## Corrección de composición v1 → v2

La primera entrega de `av_ultima_gota` tenía dos planos de pared casi vacía. Se
midió el MP4/board v1, se enriqueció el set y se volvió a medir con el mismo
`inspect`/`evaluate`, sin cambiar los umbrales.

| métrica | v1 | v2 | gate |
|---|---:|---:|---:|
| S01 teselas planas | 77 % | 40 % | < 55 % |
| S07 teselas planas | 72 % | 38 % | < 55 % |
| `empty_ratio_max` | 0.766 | 0.405 | — |
| `worst_edges` de caption | 4.17 | 5.24 | ≥ 5.0 |
| composition | FAIL | PASS | — |
| legibility | FAIL | PASS | — |

The v2 adds a trellis, hanging vine, wall shelf, hose reel and crate stack to
the visible greenhouse wall, and samples the control still at the shot midpoint
so S07 is measured with its real caption. The v1 render is preserved as
`quality/phase2/final_video_v1.mp4`; the new MP4 is the delivery.
