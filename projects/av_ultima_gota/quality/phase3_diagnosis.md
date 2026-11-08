# Fase 3 — Diagnóstico de cuellos de botella

Proyecto de referencia: `projects/av_ultima_gota`  
Baseline congelado: `quality/phase3/baseline_v2.mp4`  
Fecha de esta auditoría: 2026-11-08

## 0. Alcance real de la inspección

He conservado el MP4 v2 y lo he inspeccionado mediante:

- `ffprobe` (contenedor, códecs, duración, frames, resolución);
- extracción de fotogramas y contact sheet a 2 fps;
- stills por plano del storyboard;
- forma de onda y espectro del audio;
- lectura cruzada del manifiesto, el plan AV y el código del renderer.

**No he reproducido el MP4 completo en un reproductor con audio y no he escuchado la voz, la música ni los efectos.** Por tanto no puedo afirmar naturalidad de la voz, inteligibilidad real, balance subjetivo, actuación vocal ni sincronización percibida. La inspección visual tampoco sustituye una revisión humana del movimiento completo.

## 1. Línea base v2 verificada

| Dato | Valor observado |
|---|---|
| Archivo | `output/final_video.mp4`, copia en `quality/phase3/baseline_v2.mp4` |
| SHA-256 del original | `4e034275978795584d77b580582cb2c163e64a239f5fccf3dbaa3c9a5d9791a3` |
| Duración | 26.3 s |
| Resolución / FPS | 1080 × 1920 / 30 |
| Frames | 789 |
| Vídeo | H.264 |
| Audio | AAC, 48 kHz, estéreo |
| Tamaño | 14.674.525 bytes |
| `qa` | PASS 13/13 |
| `motion` | 5.081 |
| `freeze` | 0.0165 |
| `black` | 0 |
| Loudness medido | −14.1 dB |
| `voice_in_delivery` | 0.7188 |
| `avqa` | PASS |
| `inspect` (stills) | 0/7 flagged |
| `evaluate` | PASS; `empty_ratio_max=0.405`, `worst_edges=5.24` |
| Tests | 187 OK |
| `tsc` | 0 errores |

El PASS técnico es real, pero no demuestra que el vídeo sea cinematográficamente bueno.

### Referencia v3 (misma historia)

El render de referencia v3 también está cerrado: 26.3 s, 789 frames, 1080×1920, H.264/AAC, 14.5 MB. `qa` PASS 13/13; motion 5.226; freeze 0.0152; black 0; loudness −14.1 dB; voz 0.7188; audio_activity 0.19; caption_plan 0.897. `avqa` PASS; `inspect` 0/7 flags; `evaluate` PASS con 4 dimensiones subjetivas pendientes. El baseline v2 sigue intacto con el hash indicado arriba.

## 2. Observaciones visuales del baseline

Estas observaciones vienen de la contact sheet y de los stills, no de una reproducción completa:

| Plano | Tiempo aproximado | Observación | Severidad | Causa probable |
|---|---:|---|---|---|
| S01 | 0.0–3.8 s | El sujeto/planta ocupa poco cuadro; gran pared verde y mesa al borde. El problema tarda en leerse. | Alta | Encuadre demasiado abierto para un hook de detalle |
| S02 | 3.8–7.6 s | El grifo no era visible; la línea “salió aire” dependía del texto y del gesto. | Alta | El set no tenía un grifo legible |
| S03 | 7.6–11.4 s | Dos actores pequeños en un escenario amplio; la regadera se lee, pero la entrada no domina el cuadro. | Media | Escala media sin reencuadre suficiente |
| S04 | 11.4–14.9 s | El barrido revela el barril, pero el espacio sigue leyéndose como escenario. | Media | Set ancho y cámara de exploración |
| S05 | 14.9–18.8 s | Los actores siguen pequeños; el agua y la planta no siempre comparten protagonismo. | Media | Composición de conjunto |
| S06 | 18.8–21.3 s | Close-up correcto; es el plano que mejor comunica reacción. | Baja | Ninguna nueva |
| S07 | 21.3–26.3 s | Flor abierta y regadera sobre la mesa; mucho muro alrededor. | Media | Encuadre de cierre poco cerrado |

La historia se sigue, sobre todo, por la narración y los captions. La puesta en escena no siempre permite entender la acción sin ellos.

## 3. Clasificación de cuellos de botella

### A. Modelo de IA

El pipeline actual de esta historia no depende de un modelo generativo para el guion: el beat sheet está escrito en `spec.json` y `scripts/acs/av_director.py` lo normaliza. Por tanto no atribuyo al modelo los defectos de encuadre ni de continuidad. No hay comparación controlada de modelos en esta fase; sería necesaria para decidir si un modelo mejor escribe mejores conflictos o acciones. La limitación real es de **dirección y representación**, no de “calidad del LLM” demostrada.

### B. Director y planificador

Archivo principal: `scripts/acs/av_director.py`.

- Valida beats, escalas, cámara, motivos, continuidad de actores, secuencias y cues.
- No planifica el **objetivo físico** de una acción (por ejemplo, qué punto del set debe alcanzar una mano).
- No comprueba que una acción de alcance esté a distancia reachable.
- No decide por sí mismo el encuadre exacto: `zoom`, `offsetX` y `offsetY` son ajustes manuales del spec.
- El ledger de continuidad resuelve posición/orientación, pero no la identidad de un prop transferido.

### C. Renderer

Archivos: `studio/src/composition/Demo.tsx`, `studio/src/composition/CameraRig.tsx`, escenas.

- Es un renderer 2.5D de SVG/React, no un motor 3D con física ni IK.
- `CameraRig` aplica zoom y offsets; un zoom agresivo puede recortar pies, manos o props. Los gates de `inspect` no conocen la geometría del rig.
- No hay iluminación volumétrica real; las luces son capas y gradientes.
- El render es determinista y local; esa parte sí está implementada.

### D. Rig

Archivos: `studio/src/characters/Character.tsx`, `studio/src/composition/Actors.tsx`.

- Tiene torso, brazos en dos segmentos, manos, mirada aproximada, cejas, boca, parpadeo y presets.
- No tiene IK, colisión, dedos articulados, contacto físico real ni voz labial.
- El prop `lantern` existía, pero su dibujo era un trapecio amarillo que podía leerse como bolso. Se ha corregido la silueta con asa, marco, cristal y halo.

### E. Assets y sets

Archivos: `studio/src/scenes/Greenhouse.tsx`, `studio/src/scenes/Doorway.tsx`.

- Los sets son SVG dibujados a mano; no hay generación de ilustraciones complejas ni vídeo original.
- `Greenhouse` no tenía grifo; por eso la línea “salió aire” no tenía un objeto visible.
- Se añadió `Faucet`, pero el primer trazo de agua contradecía la línea; se eliminó el trazo.
- `Doorway` tenía lámpara colgante y lámpara de pared; se añadió un estado `left` para dejar un farol en la nieve.

### F. Cámara y composición

- La cámara está declarada por plano, con motivo narrativo, pero la composición final depende de offsets manuales.
- Los stills de S01/S07 con zoom 1.8–2.0 recortaban la planta; el inspector marcaba S01 como “escena vacía” al 50% de teselas planas.
- Se revirtió S01/S07 a un encuadre más limpio y se mantuvieron S02/S03/S05 con actores completos.
- El close-up de S04 de la historia nueva sigue marcando 54% de teselas planas; es una limitación del medidor, no una prueba de que el plano no comunique.

### G. Animación y acting

- `Actors.tsx` sí implementa secuencias (`walkIn -> turn -> reach -> react`) con anticipación, overshoot y settle. No es sólo una pose estática.
- El preset `reach` eleva el brazo, pero no apunta a una coordenada del set. En S03 de `av_ultima_luz` el brazo se extiende con el farol; no hay contacto físico con la lámpara de pared.
- No hay física de telas, peso, colisión ni transferencia real de objetos.
- El movimiento secundario es procedural (respiración, inclinación, parpadeo), no una simulación completa.

### H. Audio

- `voice` con Kokoro generó 5 líneas de la historia nueva; todas caben en su plano.
- `mixdown` aplica ducking por envolvente de RMS; no es una mezcla artística validada por escucha.
- El score es procedural; los cues son escasos.
- **No se ha escuchado el resultado.** La forma de onda y el espectro no permiten juzgar naturalidad, interpretación ni mezcla.

### I. QA

- `qa`: valida el MP4 y el audio técnico.
- `avqa`: valida estructura del manifiesto.
- `inspect`: mide composición y legibilidad sobre stills; no entiende narrativa ni acting.
- `evaluate`: evalúa assets y composición con umbrales.
- El inspector puede marcar un close-up como “vacío” por superficies planas; no distingue un rostro de una pared.
- No existe un gate automático de “la mano alcanza el objeto” ni de “el prop transferido sigue una trayectoria”.

### J. Evaluación humana

No se ha realizado. No hay espectadores externos, ni puntuaciones 1–5, ni aceptación de “5” sin evidencia. El documento `phase3_human_review.md` queda como protocolo y estado pendiente, no como evaluación completada.

## 4. Cambios implementados en esta fase

| Archivo | Cambio | Problema que ataca | Estado |
|---|---|---|---|
| `studio/src/scenes/Greenhouse.tsx` | `Faucet` visible; se retiró el trazo de agua | La línea “salió aire” no tenía objeto visible y el agua contradecía el aire | Código; referencia v3 con QA PASS e inspect 0/7 |
| `studio/src/characters/Character.tsx` | Farol con asa, marco, cristal y halo | El prop se leía como bolso | Código; MP4 de la historia nueva validado por QA |
| `studio/src/scenes/Doorway.tsx` | Estado `left` con farol en la nieve | El final necesitaba una traza física del farol dejado | Código; MP4 de la historia nueva validado por QA |
| `studio/src/composition/Demo.tsx` | Unión de estado `left` | Contrato de tipos del set | `tsc` 0 |
| `projects/av_ultima_gota/spec.json` | Encuadres S01/S02/S03/S05/S07 | Actores/planta pequeños o recortados | v3 de 26.3 s; QA PASS; inspect 0/7 |
| `projects/av_ultima_luz/spec.json` | Historia nueva en `doorway` | Falta de generalización | MP4 21.3 s; QA PASS; AVQA PASS; inspect S04 |

No se ha creado otro renderer, no se ha sustituido Remotion y no se ha añadido una API remota obligatoria.

## 5. Lo que sigue siendo limitación estructural

1. No hay IK ni contacto real: un brazo puede extenderse, pero no “agarrar” una lámpara.
2. No hay transferencia física de props; el farol en la nieve es un cambio de estado de set, no una simulación de entrega.
3. El renderer 2.5D no tiene profundidad real; los sets siguen siendo capas decoradas.
4. El audio no ha sido escuchado; no puedo declarar que la voz y la música funcionen juntas.
5. No hay revisión humana; las dimensiones subjetivas siguen pendientes.
6. El inspector de composición no distingue un rostro de una pared plana y puede marcar close-ups legibles.

## 6. Estado

**TÉCNICAMENTE VALIDADA, PERO CINEMATOGRÁFICAMENTE PENDIENTE.**

El baseline es técnicamente válido. Las mejoras de encuadre, grifo, farol e historia nueva están implementadas y la referencia v3 está validada técnicamente, pero no pueden cerrar la fase sin reproducción completa, escucha del audio y revisión humana.
