# Creative QA — av_direccion

**sin fallos estructurales** · 10 planos · 30.933s · media 3.09s

| comprobación | valor | estado | evidencia |
|---|---|---|---|
| hook, setup, escalation, reaction and close are declared | `{'missing': []}` | ✅ measured | beats present in the manifest |
| the hook stays short | `3.4` | ✅ measured | the premise must arrive before the first explanation |
| there is at least one reaction shot | `1` | ✅ measured | reaction is a separate edit decision, not an actor idle |
| shot scales vary | `{'unique': 4, 'counts': {'detail': 2, 'close': 3, 'wide': 2, 'medium': 3}}` | ✅ measured | at least three scales; source: declared |
| no more than two consecutive shots of the same scale | `1` | ✅ measured | repetition is allowed, a run is not |
| camera intents vary | `{'unique': 8, 'counts': {'tiltUp': 1, 'pushInSlow': 2, 'panRight': 1, 'static': 1, 'drift': 1, 'dollyIn': 2, 'trackRight': 1, 'dollyOut': 1}}` | ✅ measured | static shots are allowed; an entire film of one move is not |
| every non-static camera move has a narrative motive | `9/9` | ✅ measured | motive fields in the manifest |
| movement is neither absent nor constant | `0.9` | ✅ measured | share of moving shots; quiet shots are not penalised by themselves |
| every dissolve is motivated | `2/2` | ✅ measured | cuts need no overlap; a dissolve must explain why |
| sound follows action in at least half the shots | `9/10` | ✅ measured | declared cues or the existing scene-derived effects |
| characters perform actions, not only poses | `5/10` | ✅ measured | walkIn/dig/reach/turn/call presets |
| no narration line is repeated | `[]` | ✅ measured | duplicate spoken lines would repeat information |
| the cut is a short vertical piece, not a fragment | `30.933` | ✅ measured | measured after transition overlaps |

## Lectura

- Escalas: {'detail': 2, 'close': 3, 'wide': 2, 'medium': 3} · racha máxima 1
- Cámara: {'tiltUp': 1, 'pushInSlow': 2, 'panRight': 1, 'static': 1, 'drift': 1, 'dollyIn': 2, 'trackRight': 1, 'dollyOut': 1} · motivos 9/9
- Montaje: 5 planos con acción, 1 de reacción, 3 con dos personajes
- Audio: cues en 9/10 planos (15 eventos)

> structural audit of the edit plan; narrative, performance and taste remain human review. Lo pendiente no se puntúa.
