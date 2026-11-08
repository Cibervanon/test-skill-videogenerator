# Visual inspection

Style: **cinematic** · method: pixels + manifest geometry

| shot | vacío | sujeto | texto | paleta | profundidad | estado |
|---|---|---|---|---|---|---|
| S01 | 52% | 4.26 | 193/8 | 0.12 | 3/3 | clean |
| S02 | 48% | 4.59 | 194/14 | 0.12 | 3/3 | clean |
| S03 | 48% | 5.69 | 200/15 | 0.12 | 3/3 | clean |
| S04 | 52% | 4.43 | 110/6 | 0.12 | 3/3 | clean |
| S05 | 48% | 4.67 | 196/14 | 0.12 | 3/3 | clean |
| S06 | 47% | 5.01 | 191/15 | 0.12 | 3/3 | clean |

## Overlays

Validación: **OK** — 0 overlays

## UI

Resultado: **OK** · 0 elemento(s) · 0 problema(s) · 0 aviso(s)

| plano | modo | intención | UI | ventana / lectura | estado |
|---|---|---|---|---|---|
| S01 | **A** | hook | — | — | clean |
| S02 | **A** | setup | — | — | clean |
| S03 | **A** | escalation | — | — | clean |
| S04 | **A** | reaction | — | — | clean |
| S05 | **A** | reveal | — | — | clean |
| S06 | **A** | close | — | — | clean |

### Problemas

- ninguno

### Evidencia del render

| modo | planos | detalle de escena | contraste de UI |
|---|---|---|---|
| A | 6 | 3.33 | — |

> scene_edges es energía de bordes del frame completo; ui_contrast es el rango p95-p5 dentro de la caja, medido en el centro de la ventana del elemento. Confirma que B/C conservan escena y que E/F son placas gráficas; no puntúa gusto. Las etiquetas ancladas al actor no tienen caja declarada y no se miden.

### Límites

- la caja del cuerpo es un sobre aproximado (cabeza, torso, abrigo, arco de brazos): no rastrea dedos
- no hay OCR ni comprensión semántica: el motivo narrativo se audita contra el campo `intent` declarado
- el tiempo de lectura es una estimación de 3.3 palabras/s, no una medición ocular

## Lo que esta inspección no mide

- Actuación, narrativa, ritmo y gusto: quedan **pendientes** de revisión humana.
- No hay OCR: el contraste de texto se mide en la banda de subtítulos, no se lee el texto.
- La profundidad es un proxy de energía de bordes por tercios, no un mapa de profundidad.
