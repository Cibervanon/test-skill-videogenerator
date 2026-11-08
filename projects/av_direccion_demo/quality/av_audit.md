# Creative QA — av_direccion_demo

**sin fallos estructurales** · 6 planos · 20.433s · media 3.41s

| comprobación | valor | estado | evidencia |
|---|---|---|---|
| hook, setup, escalation, reaction and close are declared | `{'missing': []}` | ✅ measured | beats present in the manifest |
| the hook stays short | `3.5` | ✅ measured | the premise must arrive before the first explanation |
| there is at least one reaction shot | `1` | ✅ measured | reaction is a separate edit decision, not an actor idle |
| the hook opens and the close ends the cut | `{'hook_first': True, 'close_last': True}` | ✅ measured | the order is a narrative decision, not just a set of labels |
| every beat has a framing that can carry it | `[]` | ✅ measured | hook/reaction/close are checked against a framing range |
| shot scales vary | `{'unique': 4, 'counts': {'detail': 1, 'wide': 2, 'medium': 2, 'close': 1}}` | ✅ measured | at least three scales; source: declared |
| no more than two consecutive shots of the same scale | `1` | ✅ measured | repetition is allowed, a run is not |
| camera intents vary | `{'unique': 6, 'counts': {'tiltUp': 1, 'panRight': 1, 'trackRight': 1, 'static': 1, 'reframe': 1, 'dollyOut': 1}}` | ✅ measured | static shots are allowed; an entire film of one move is not |
| every non-static camera move has a narrative motive | `5/5` | ✅ measured | motive fields in the manifest |
| movement is neither absent nor constant | `0.833` | ✅ measured | share of moving shots; quiet shots are not penalised by themselves |
| every dissolve is motivated | `2/2` | ✅ measured | cuts need no overlap; a dissolve must explain why |
| sound follows action in at least half the shots | `5/6` | ✅ measured | declared cues or the existing scene-derived effects |
| characters perform actions, not only poses | `5/6` | ✅ measured | walkIn/dig/reach/turn/call presets, including phases |
| declared compound actions are ordered and finish on a terminal preset | `{'sequences': 2, 'unfinished': []}` | ✅ measured | a sequence ending mid-walk or with an invalid window is a performance error |
| no narration line is repeated | `[]` | ✅ measured | duplicate spoken lines would repeat information |
| no line is delivered faster than the ear can follow | `2.286` | ✅ measured | worst word/second rate; wordless shots are skipped |
| every shot carries a line, an action or a declared insert/reaction | `[]` | ✅ measured | a shot with no information is a candidate for removal |
| two-shots in the same scene keep screen direction | `0` | ✅ measured | only a reversed actor order between the same two actors is flagged |
| static shots are deliberate and bounded | `{'shots': 1, 'ratio': 0.167, 'unmotivated': []}` | ✅ measured | a held frame must have a motive; a film of tripods is not variety |
| declared camera intensity stays inside the authored range | `[]` | ✅ measured | 0.35..1.35; static shots use 0 |
| the cut is a short vertical piece, not a fragment | `20.433` | ✅ measured | measured after transition overlaps |

## Lectura

- Escalas: {'detail': 1, 'wide': 2, 'medium': 2, 'close': 1} · racha máxima 1
- Cámara: {'tiltUp': 1, 'panRight': 1, 'trackRight': 1, 'static': 1, 'reframe': 1, 'dollyOut': 1} · motivos 5/5
- Montaje: 5 planos con acción, 1 de reacción, 4 con dos personajes
- Audio: cues en 5/6 planos (10 eventos)

> structural audit of the edit plan; narrative, performance and taste remain human review. Lo pendiente no se puntúa.
