# Creative QA — ui_direccion

**fallos estructurales: scale_run, camera_motivation, action_coverage** · 8 planos · 27.4s · media 3.42s

| comprobación | valor | estado | evidencia |
|---|---|---|---|
| beat structure | `None` | ⏳ pending | legacy manifest: no beat fields |
| hook | `None` | ⏳ pending | legacy manifest: no hook decision recorded |
| reaction shot | `None` | ⏳ pending | legacy manifest: no reaction beat recorded |
| shot scales vary | `{'unique': 4, 'counts': {'full': 5, 'close': 1, 'detail': 1, 'wide': 1}}` | ✅ measured | at least three scales; source: derived from actor scale, derived from scene |
| no more than two consecutive shots of the same scale | `3` | ❌ measured | repetition is allowed, a run is not |
| camera intents vary | `{'unique': 7, 'counts': {'pushInSlow': 1, 'dollyIn': 1, 'tiltUp': 1, 'drift': 2, 'static': 1, 'panLeft': 1, 'dollyOut': 1}}` | ✅ measured | static shots are allowed; an entire film of one move is not |
| every non-static camera move has a narrative motive | `0/7` | ❌ measured | motive fields in the manifest |
| movement is neither absent nor constant | `0.875` | ✅ measured | share of moving shots; quiet shots are not penalised by themselves |
| every dissolve is motivated | `0/0` | ⏳ measured | cuts need no overlap; a dissolve must explain why |
| sound follows action in at least half the shots | `7/8` | ✅ measured | declared cues or the existing scene-derived effects |
| characters perform actions, not only poses | `2/8` | ❌ measured | walkIn/dig/reach/turn/call presets |
| no narration line is repeated | `[]` | ✅ measured | duplicate spoken lines would repeat information |
| the cut is a short vertical piece, not a fragment | `27.4` | ✅ measured | measured after transition overlaps |

## Lectura

- Escalas: {'full': 5, 'close': 1, 'detail': 1, 'wide': 1} · racha máxima 3
- Cámara: {'pushInSlow': 1, 'dollyIn': 1, 'tiltUp': 1, 'drift': 2, 'static': 1, 'panLeft': 1, 'dollyOut': 1} · motivos 0/7
- Montaje: 2 planos con acción, 0 de reacción, 2 con dos personajes
- Audio: cues en 7/8 planos (7 eventos)

> structural audit of the edit plan; narrative, performance and taste remain human review. Lo pendiente no se puntúa.
