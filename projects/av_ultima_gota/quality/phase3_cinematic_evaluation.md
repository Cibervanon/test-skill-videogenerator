# Fase 3 — Evaluación cinematográfica

## Método y límites

He inspeccionado:

- el baseline completo mediante `ffprobe`, waveform, espectro y contact sheet a 2 fps;
- stills por plano del baseline y de los storyboards nuevos;
- el manifiesto, el plan AV y el código de cámara/rig.

**No he reproducido el MP4 completo con audio ni he escuchado la voz, la música o los efectos.** La evaluación de ritmo percibido, actuación vocal, mezcla y sincronización queda pendiente. Tampoco hay revisores humanos.

## Baseline v2

Fortalezas:

- Continuidad básica de espacio: invernadero, barril, mesa, planta y regadera.
- S06 es el plano más claro emocionalmente: un close-up con una reacción.
- La historia se entiende con la narración: sequedad, aire, agua, flor.
- El montaje tiene variedad de escalas y motivos de cámara.

Debilidades:

- S01 y S07 están dominados por pared verde; el sujeto y la planta no tienen peso visual suficiente.
- S02 dependía del texto para entender el grifo; el grifo no era visible.
- S03/S05 mantienen actores pequeños en un escenario amplio; la entrada y el gesto no llenan el cuadro.
- La continuidad del agua/regadera es correcta, pero la acción se lee más por caption que por puesta en escena.
- La identidad visual es consistente, pero plana: los sets son paredes decoradas con objetos, sin profundidad real.

## Historia nueva: mediciones verificadas

- MP4: 21.3 s, 639 frames, 1080×1920, H.264/AAC, 10.5 MB.
- `qa`: PASS 13/13; motion 5.912; freeze 0.1596; black 0; loudness −13.6 dB; voz en entrega 0.7179; actividad de audio 0.282; caption plan 0.873.
- `avqa`: PASS; hook 3.6 s; 3 escalas; 6 movimientos de cámara; 5/5 motivos; 3/6 shots con cues; 4/6 con acción; sin problemas de orden, eje o continuidad.
- `inspect`: S04 marcado con 54% de teselas planas; el rostro sigue siendo legible. No se baja el umbral.
- `evaluate`: PASS en composición, legibilidad, consistencia, overlays, montaje, motion, técnico, sonido y captions; narrativa, acting, ritmo y estilo siguen subjetivos y sin puntuar.

Estas métricas no son una evaluación de acting ni de emoción. La `qa` sólo confirma que el MP4 y el audio son válidos y que hay señal de voz.

## Referencia v3: mediciones verificadas

MP4 de 26.3 s, 789 frames, 1080×1920, H.264/AAC, 14.5 MB. `qa` PASS 13/13; motion 5.226; freeze 0.0152; black 0; loudness −14.1 dB; voz 0.7188; audio_activity 0.19; caption_plan 0.897. `avqa` PASS; hook 3.8 s; 4 escalas; 7 movimientos de cámara; 6/6 motivos; 4/7 cobertura de sonido; 5/7 cobertura de acción. `inspect` 0/7 flags; `evaluate` PASS con 4 dimensiones subjetivas pendientes.

Cambios aplicados:

- `Faucet` visible en el barril; el trazo de agua se eliminó porque la línea dice “salió aire”.
- S02 con más presencia del actor y del grifo; S03/S05 con actores completos.
- S01/S07 vueltos a un encuadre que no recorta la planta y no dispara “escena vacía”.
- La referencia sigue siendo la misma historia; no se ha convertido en otra pieza.

Riesgo: los encuadres siguen dependiendo de offsets manuales. No hay una regla automática que garantice pies/manos dentro de cuadro.

## Historia nueva: La última luz

Premisa: una mujer espera en un umbral nevado a alguien que no vuelve; un farolero viene a apagar la lámpara y acaba dejando su propia luz.

Protagonista: la mujer. Objetivo: conservar la luz de la espera. Obstáculo: el farolero tiene la obligación de apagarla. Conflicto: la luz es deber para él y memoria para ella. Cambio: él no apaga la esperanza; deja otra luz. Resolución: la mujer se queda con el farol en la nieve.

Lo que cambia respecto a `av_ultima_gota`:

- no hay planta, agua ni invernadero;
- el conflicto es memoria vs obligación, no sequedad vs agua;
- el objeto central es la luz, no la regadera;
- la resolución es una renuncia, no una restauración;
- el set es un umbral nocturno, no un invernadero diurno;
- la cámara usa un close-up de reacción y un plano de salida, no un ciclo de riego.

Lo que se ve en los stills:

- S01: umbral, luz colgante y nieve; no hay actor. El objeto de la espera es visible.
- S02: la mujer y el joven comparten cuadro; el farol se reconoce mejor tras corregir su silueta.
- S03: el joven extiende el brazo con el farol; la acción se lee como gesto, no como contacto con la lámpara.
- S04: close-up de la mujer; el inspector marca 54% de teselas planas, pero el rostro y la reacción son legibles.
- S05: el joven se aleja; el farol queda en la nieve como cambio de estado del set.
- S06: la mujer y el farol left; el cierre conserva la traza.

## Acciones y continuidad

- `walkIn`, `turn`, `reach`, `react` e `idle` están implementados y se usan.
- El alcance no tiene IK: el brazo se extiende, pero no toca la lámpara. No se declara “apagado físico”.
- La entrega del farol no es una simulación: S05 cambia `hold` y el set cambia a `state:"left"` en el corte. `av` emite un warning por el cambio de prop sin fase explícita; es honesto y está documentado.
- La mujer mantiene x=300 entre S02, S03, S05 y S06; S04 usa un close-up motivado. El joven mantiene x=720 y cambia orientación sólo con `turn` en S03.
- Persisten cambios de escala y cortes que el espectador debe completar; no hay continuidad 3D.

## Cámara y composición

La cámara tiene motivos narrativos declarados y no se mueve por llenar métricas. Sin embargo:

- los movimientos son transformaciones 2.5D, no óptica real;
- el zoom puede recortar extremidades;
- los offsets manuales son la principal fuente de error de composición;
- S04 demuestra que el inspector de “escena vacía” no distingue un rostro de una pared.

## Audio

- La historia nueva tiene 5 líneas de Kokoro; todas caben en su plano.
- La mezcla ducking existe (`mix.wav`, 21.55 s).
- **No se ha escuchado.** No puedo afirmar naturalidad, emoción, inteligibilidad ni balance.
- La referencia conserva su mezcla anterior; tampoco fue escuchada en esta fase: sólo se inspeccionaron forma de onda y espectro.

## Generalización

La nueva historia usa el mismo renderer, el mismo rig y otro set (`doorway`), otro conflicto y otro prop. No es un cambio de nombres: cambia el objetivo, el obstáculo, la emoción y la resolución.

Existe una segunda pieza adicional en el repositorio, `av_ultima_medida` (sastrería, cinta de medir, 6 planos, 22.4 s). Es una historia preexistente, no reescrita en esta fase; sirve como evidencia de variedad, no como prueba de que el sistema escriba autónomamente dos historias nuevas.

## Veredicto

La fase mejora la **legibilidad de acciones** y añade una historia con conflicto distinto. No demuestra todavía calidad cinematográfica completa:

- falta ver el movimiento completo;
- falta escuchar el audio;
- falta revisión humana;
- el contacto físico y la transferencia de props no existen;
- la composición sigue dependiendo de ajustes manuales.

**TÉCNICAMENTE VALIDADA, PERO CINEMATOGRÁFICAMENTE PENDIENTE.**
