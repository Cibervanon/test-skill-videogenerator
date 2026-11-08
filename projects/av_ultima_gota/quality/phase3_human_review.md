# Fase 3 — Revisión humana

## Estado

**No se ha realizado revisión humana.**

No hay espectadores externos, ni revisores que hayan visto el vídeo completo con audio, ni puntuaciones 1–5. Por tanto no hay ninguna valoración subjetiva que pueda presentarse como resultado.

La ausencia de esta revisión impide cerrar cinematográficamente la fase. Un QA PASS no la sustituye.

## Protocolo reproducible

### Material

- Baseline: `projects/av_ultima_gota/quality/phase3/baseline_v2.mp4`
- Referencia nueva: `projects/av_ultima_gota/output/final_video.mp4` (v3, cuando exista)
- Historia nueva: `projects/av_ultima_luz/output/final_video.mp4`
- Segunda historia adicional: `projects/av_ultima_medida/output/final_video.mp4`

### Condiciones

- Reproducir cada pieza completa, de principio a fin, con audio.
- No pausar para leer informes ni mirar métricas durante la primera pasada.
- Anotar timestamps aproximados.
- No conocer la hipótesis del desarrollador antes de puntuar.
- Si se compara, ver el baseline antes que la versión nueva; no al revés.

### Escala

1. Deficiente: no se entiende o no se sostiene.
2. Débil: se entiende a duras penas; hay fallos visibles.
3. Aceptable: se entiende, pero no destaca.
4. Bueno: claro, intencionado y consistente.
5. Excelente: funciona en todos los niveles y resiste una segunda mirada.

Cada puntuación debe incluir **qué se vio y en qué timestamp**. No se acepta un 5 sin evidencia concreta.

### Formulario

| Dimensión | Pregunta | Puntuación 1–5 | Evidencia / timestamp |
|---|---|---:|---|
| Historia | ¿Entendí qué quería el protagonista y qué se lo impedía? | | |
| Claridad | ¿Entendí qué ocurrió sin depender de los captions? | | |
| Acciones | ¿Las acciones fueron visualmente comprensibles? | | |
| Acting | ¿El personaje transmitió una emoción reconocible? | | |
| Ritmo | ¿Los planos duraron lo que pedía la historia? | | |
| Dirección | ¿La cámara ayudó a entender o a sentir? | | |
| Continuidad | ¿Los personajes, objetos y espacios se mantuvieron? | | |
| Composición | ¿La mirada sabía dónde ir? | | |
| Audio | ¿Voz, música y efectos funcionaron juntos? | | |
| Global | ¿Volvería a ver otra historia de este sistema? | | |

### Preguntas de espectador

1. ¿Entendiste qué quería el protagonista?
2. ¿Entendiste qué ocurrió?
3. ¿Las acciones fueron claras?
4. ¿El personaje transmitió alguna emoción?
5. ¿El ritmo resultó natural?
6. ¿El final tuvo sentido?
7. ¿Qué momento recuerdas?
8. ¿Qué momento te resultó aburrido?
9. ¿Volverías a ver otra historia de este sistema?

### Evidencia que debe adjuntarse

- Timestamps de los momentos recordados y de los momentos flojos.
- Una frase literal del revisor, no un resumen del desarrollador.
- Versión exacta del vídeo y hash.
- Si el revisor vio el vídeo con o sin audio.

## Lo que no se puede declarar

- No se puede decir “la voz transmite emoción” sin escucharla.
- No se puede decir “el ritmo funciona” porque la duración media sea razonable.
- No se puede decir “el acting es bueno” porque exista un preset `react`.
- No se puede convertir una opinión del desarrollador en una evaluación de espectador.

## Cierre pendiente

La fase queda en:

**TÉCNICAMENTE VALIDADA, PERO CINEMATOGRÁFICAMENTE PENDIENTE.**

Para cambiarla haría falta, como mínimo:

1. reproducción completa de los vídeos;
2. escucha del audio;
3. al menos una revisión externa por pieza;
4. puntuaciones con evidencia;
5. comparación antes/después con timestamps.
