# Fase 3 — Auditoría de acciones y props

## Sistema real encontrado

La gramática de acciones no es un lenguaje separado: vive en `studio/src/composition/Actors.tsx` como presets y secuencias.

Presets existentes:

- `idle`
- `walkIn`
- `closeup`
- `dig`
- `reach`
- `turn`
- `call`
- `point`
- `react`

Una secuencia puede encadenar presets con ventanas normalizadas (`start`/`end`), posición (`x`, `y`), escala, orientación, `hold`, `armR` y `phase`. `performSequence()` evalúa cada fase en su propio reloj y hace cross-fade en los bordes.

## Lo que sí está implementado

| Capacidad | Evidencia | Nivel real |
|---|---|---|
| Anticipación y recuperación | `reach` calcula travel, overshoot y settle; `call` y `point` tienen fases | Implementado |
| Movimiento secundario | respiración, blink, head lead, sway, lean | Implementado, procedural |
| Giro de atención | `turn` mueve hombros/cabeza antes que la mirada | Implementado |
| Reacción | `react` tiene recoil, brow y respiración | Implementado |
| Prop sostenido | `hold` dibuja `shovel`, `lantern`, `rope`, `bell`, `can` | Implementado como SVG pegado a la mano |
| Secuencia compuesta | `walkIn -> turn -> reach` en `av_ultima_gota`, `walkIn -> turn -> reach` en `av_ultima_luz` | Implementado |
| Estado de set | `Greenhouse` acepta `table/held/pour/bloom`; `Doorway` acepta `left` | Implementado |

## Lo que no está implementado

- **No hay IK.** El brazo rota alrededor del hombro; no se resuelve una cadena hasta un objetivo del set.
- **No hay contacto físico.** Una mano puede dibujarse cerca de un objeto, pero no hay colisión ni agarre.
- **No hay transferencia de props.** Pasar un objeto de una mano a otra o dejarlo en el suelo no es una simulación; es un cambio de `hold` y/o `state` en el corte.
- **No hay física.** No hay peso, telas, inercia de objetos ni colisión.
- **No hay labial/fonemas.** La boca es una curva; no sincroniza visemas con Kokoro.
- **No hay mirada dirigida a un prop concreto.** `yaw` y `headTilt` son aproximados; no hay target 3D.

## Auditoría por acción de la historia nueva

| Plano | Acción declarada | Lo que se ve | Continuidad | Veredicto |
|---|---|---|---|---|
| S02 | El joven entra con el farol | `walkIn` desde la derecha, farol en mano | Entra desde fuera; la mujer ya está en el umbral | Acción legible; distancia y escala medias |
| S03 | El farolero extiende el farol hacia la lámpara | Brazo derecho extendido, farol reconocible | Conserva x=720, gira a cámara; no hay contacto con la lámpara de pared | Acción legible como gesto, **no como apagado físico** |
| S04 | La mujer reacciona | Close-up, `react`, sin línea | Corte motivado; mismo umbral | Reacción legible; el inspector marca teselas planas |
| S05 | El joven se va y deja su farol | `walkIn` hacia la derecha, `hold:"none"`, set `state:"left"` | El farol aparece en la nieve; no hay handoff simulado | **Corte de estado**, no transferencia física |
| S06 | La mujer se queda | `idle`, farol en el suelo | Mismo set y posición | Cierre comprensible |

## El grifo de `av_ultima_gota`

Se añadió `Faucet` al grupo del barril en `Greenhouse.tsx`. El primer dibujo incluía un trazo de agua con opacidad 0.55, que contradecía la línea “salió aire”. Ese trazo se retiró. El grifo queda como objeto visible, sin agua.

Esto no convierte el gesto en una acción física completa: el actor sigue haciendo un gesto de abrir el grifo sin IK ni contacto; el objeto ahora existe y la línea no se contradice.

## Problemas de continuidad que quedan

1. S05 de `av_ultima_luz`: `av_director` avisa “held prop changes without an explicit phase”. Es correcto: el cambio de farol en mano a farol en el suelo ocurre en el corte, no en una animación de entrega.
2. S03: el brazo no alcanza la lámpara de pared. Es una limitación de targeting/IK, no un error de render.
3. Los actores no miran siempre al prop que manipulan; `yaw` es una aproximación.
4. El estado del set no tiene una máquina de estados formal; `left` es un booleano de escena.

## Cambios mínimos recomendados (no implementados en esta fase)

- Añadir un campo `target` a una acción (`{x,y,prop}`) y validar su alcance contra el rig.
- Añadir una transición de prop con `fromHold`, `toHold`, `at` y `stateAfter`, aunque sea un corte explícito.
- Añadir al inspector una comprobación de bounding box del actor contra el cuadro (pies/manos).
- No simular IK: si no se implementa, mantener la limitación visible y no llamar “agarre” a una pose.

## Conclusión

El sistema ya tiene **acciones con estructura temporal**, no sólo poses. Lo que no tiene es **contacto físico**. La historia nueva usa un corte de estado para el farol y lo declara; no finge una entrega. Esa es la representación honesta con el rig actual.
