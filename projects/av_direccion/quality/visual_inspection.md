# Visual inspection

Style: **cinematic** · method: pixels + manifest geometry

| shot | vacío | sujeto | texto | paleta | profundidad | estado |
|---|---|---|---|---|---|---|
| S01 | 50% | 3.40 | 212/8 | 0.08 | 3/3 | clean |
| S02 | 42% | 3.87 | 191/16 | 0.10 | 3/3 | clean |
| S03 | 48% | 4.29 | 169/17 | 0.09 | 3/3 | clean |
| S04 | 60% | 3.26 | 30/3 | 0.09 | 3/3 | clean |
| S05 | 44% | 4.17 | 173/15 | 0.09 | 3/3 | clean |
| S06 | 43% | 3.72 | 203/12 | 0.10 | 3/3 | clean |
| S07 | 40% | 4.11 | 204/17 | 0.09 | 3/3 | clean |
| S08 | 48% | 3.39 | 199/13 | 0.09 | 3/3 | clean |
| S09 | 48% | 3.98 | 206/17 | 0.09 | 3/3 | clean |
| S10 | 38% | 2.83 | 195/20 | 0.11 | 3/3 | clean |

## Overlays

Validación: **OK** — 0 overlays

## UI

Resultado: **OK** · 0 elemento(s) · 0 problema(s) · 0 aviso(s)

| plano | modo | intención | UI | ventana / lectura | estado |
|---|---|---|---|---|---|
| S01 | **A** | hook | — | — | clean |
| S02 | **A** | setup | — | — | clean |
| S03 | **A** | development | — | — | clean |
| S04 | **A** | insert | — | — | clean |
| S05 | **A** | development | — | — | clean |
| S06 | **A** | reaction | — | — | clean |
| S07 | **A** | reveal | — | — | clean |
| S08 | **A** | reveal | — | — | clean |
| S09 | **A** | escalation | — | — | clean |
| S10 | **A** | close | — | — | clean |

### Problemas

- ninguno

### Evidencia del render

| modo | planos | detalle de escena | contraste de UI |
|---|---|---|---|
| A | 10 | 3.62 | — |

> scene_edges es energía de bordes del frame completo; ui_contrast es el rango p95-p5 dentro de la caja, medido en el centro de la ventana del elemento. Confirma que B/C conservan escena y que E/F son placas gráficas; no puntúa gusto. Las etiquetas ancladas al actor no tienen caja declarada y no se miden.

### Límites

- la caja del cuerpo es un sobre aproximado (cabeza, torso, abrigo, arco de brazos): no rastrea dedos
- no hay OCR ni comprensión semántica: el motivo narrativo se audita contra el campo `intent` declarado
- el tiempo de lectura es una estimación de 3.3 palabras/s, no una medición ocular

## Lo que esta inspección no mide

- Actuación, narrativa, ritmo y gusto: quedan **pendientes** de revisión humana.
- No hay OCR: el contraste de texto se mide en la banda de subtítulos, no se lee el texto.
- La profundidad es un proxy de energía de bordes por tercios, no un mapa de profundidad.
