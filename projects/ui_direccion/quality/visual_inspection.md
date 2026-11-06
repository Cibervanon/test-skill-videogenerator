# Visual inspection

Style: **cinematic** · method: pixels + manifest geometry

| shot | vacío | sujeto | texto | paleta | profundidad | estado |
|---|---|---|---|---|---|---|
| S01 | 45% | 3.57 | 175/15 | 0.09 | 3/3 | clean |
| S02 | 38% | 3.65 | 205/17 | 0.10 | 3/3 | clean |
| S03 | 50% | 3.40 | 212/8 | 0.08 | 3/3 | clean |
| S04 | 51% | 5.01 | 204/9 | 0.05 | 3/3 | clean |
| S05 | 85% | 9.06 | 213/8 | 0.03 | 3/3 | clean |
| S06 | 47% | 4.11 | 166/13 | 0.08 | 3/3 | clean |
| S07 | 42% | 4.69 | 197/16 | 0.09 | 3/3 | clean |
| S08 | 87% | 5.59 | 206/8 | 0.03 | 3/3 | clean |

## Overlays

Validación: **OK** — 6 overlays
- ⚠ S04: U4: a data chart in a low-density style — confirm it is the point of the shot

## UI

Resultado: **OK** · 6 elemento(s) · 0 problema(s) · 0 aviso(s)

| plano | modo | intención | UI | ventana / lectura | estado |
|---|---|---|---|---|---|
| S01 | **A** | narracion | — | — | clean |
| S02 | **B** | dato | U2·counter | 2.38s/2.2s | clean |
| S03 | **A** | accion | — | — | clean |
| S04 | **D** | comparacion | U4·bar | 3.15s/3.15s | clean |
| S05 | **E** | proceso | U5·process | 3.52s/3.45s | clean |
| S06 | **B** | aclaracion | U6·callout | 2.45s/2.45s | clean |
| S07 | **C** | accion | U7·label | 2.45s/2.2s | clean |
| S08 | **F** | cierre | U8·counter | 1.98s/1.2s | clean |

### Problemas

- ninguno

### Evidencia del render

| modo | planos | detalle de escena | contraste de UI |
|---|---|---|---|
| A | 2 | 3.0 | — |
| B | 2 | 3.96 | 115.5 |
| C | 1 | 4.07 | — |
| D | 1 | 3.86 | 164.0 |
| E | 1 | 3.93 | 31.0 |
| F | 1 | 1.45 | 24.0 |

> scene_edges es energía de bordes del frame completo; ui_contrast es el rango p95-p5 dentro de la caja, medido en el centro de la ventana del elemento. Confirma que B/C conservan escena y que E/F son placas gráficas; no puntúa gusto. Las etiquetas ancladas al actor no tienen caja declarada y no se miden.

### Límites

- la caja del cuerpo es un sobre aproximado (cabeza, torso, abrigo, arco de brazos): no rastrea dedos
- no hay OCR ni comprensión semántica: el motivo narrativo se audita contra el campo `intent` declarado
- el tiempo de lectura es una estimación de 3.3 palabras/s, no una medición ocular

## Lo que esta inspección no mide

- Actuación, narrativa, ritmo y gusto: quedan **pendientes** de revisión humana.
- No hay OCR: el contraste de texto se mide en la banda de subtítulos, no se lee el texto.
- La profundidad es un proxy de energía de bordes por tercios, no un mapa de profundidad.
