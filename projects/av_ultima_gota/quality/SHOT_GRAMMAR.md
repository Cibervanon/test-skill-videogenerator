# Shot grammar / proporciones — `av_ultima_gota`

## Qué se aplicó

La historia es vertical (1080×1920, 9:16). Para no confundir “más encuadre” con
“mejor encuadre”, se usaron cuatro reglas comprobables:

1. **Los ojos mandan.** En planos de persona, la mirada debe caer cerca del
   tercio superior; demasiado headroom hunde al sujeto en el cuadro.
2. **El tamaño del plano cambia el headroom.** Un close-up de reacción puede
   cortar la cabeza por arriba; un medium debe dejar respirar el torso y las
   manos. El detalle de objeto no necesita ojos, pero sí un objeto dominante.
3. **En vertical, dos personas se apilan en profundidad.** Ponerlas una al lado
   de otra sin más las empuja contra los bordes; la segunda debe entrar en un
   plano ligeramente distinto.
4. **El movimiento de cámara debe aportar información.** Un push-in al objeto
   que falta, un tilt del grifo a la cara, un track que acompaña el transporte
   del agua. No se usa cámara para tapar una escena estática.

Fuentes consultadas:

- FIU, *Camera Shots and Storyboards*: close-up para detalle, medium de cintura
  arriba, headroom y ojos en el tercio superior.
  https://web.eng.fiu.edu/arellano/4010/F2007/Camera%20Shots%20and%20Storyboards.pdf
- IAFOR, *Filmmaking Theory for Vertical Video Production*: en vertical la
  regla de tercios puede no bastar; se propone una regla de quintos, menos
  headroom y encuadres que aprovechan la altura.
  https://papers.iafor.org/wp-content/uploads/papers/euromedia2019/EuroMedia2019_52556.pdf
- UNC Media & Design Center, *Video Concepts*: ojos a un tercio de la parte
  superior y headroom controlado.
  https://guides.lib.unc.edu/media-design-center/video-concepts
- OpenMicroDrama, *Vertical Framing and Shot Language for 9:16*: ojos altos,
  menos headroom del habitual y two-shots apilados en profundidad.
  https://openmicrodrama.com/guides/vertical-framing-and-shot-language
- CSU Social, *Vertical Video and Using Composition Rules*: la vertical es
  íntima y concentra la atención en un sujeto; los ojos en intersecciones altas.
  https://social.colostate.edu/best-practices/vertical-video-and-using-composition-rules

No son pruebas de calidad emocional; son criterios de encuadre. La evaluación
de si el plano “funciona” sigue siendo humana.

## Proporciones reales del set

Datos tomados de `studio/src/scenes/Greenhouse.tsx` y del manifiesto, no de una
impresión del storyboard:

- Suelo: empieza en `y=1258`; los actores anclan los pies en `y=1740`, por
  delante de la mesa. La mesa no se usa como tarima.
- Mesa: `x=610…1040`, tablero en `y=1530`. La mesa queda por detrás del cuerpo
  de los actores, no debajo de sus pies.
- Planta: `x=874`, base `y=1530`; el tallo sube hasta aproximadamente `y=1380`
  (seca) y la flor se abre en el estado `bloom`.
- Regadera de mesa: `x=690`, `y=1530`, escala `0.92`; en mano se dibuja como
  prop del brazo y no como un objeto flotante.
- Barril: a la izquierda, con tapa por debajo de la línea de cabecera del
  personaje. El jardinero se coloca delante (`x=300`), no encima.
- Edad relativa: `elder` usa `scale=1.35`; `young` usa `scale=1.24`. La relación
  es `1.24/1.35 = 0.919`, coherente con la identidad `young` ≈ 92 % de `elder`.
  No se igualaron las escalas: el aprendiz sigue siendo más joven y algo más
  bajo.

## Gramática de los siete planos

| Plano | Tamaño declarado | Qué debe leerse | Decisión de cámara | Estado |
|---|---|---|---|---|
| S01 | detail | hoja seca + regadera vacía | push-in con zoom 1.65 y offsets laterales | `table` |
| S02 | medium | grifo que no da agua y reacción del jardinero | tiltUp del grifo a la cara | `table` |
| S03 | medium | aprendiz entra con la regadera vacía | trackRight, mantiene planta en cuadro | `held` |
| S04 | wide | el barril lleno está al fondo | panLeft de la mesa al barril | `held` |
| S05 | medium | el aprendiz cruza con la regadera llena | reframe sobre el recorrido | `held` |
| S06 | close | reacción sin diálogo del jardinero | static, sin movimiento gratuito | `pour` |
| S07 | medium | la flor abierta y la regadera devuelta | dollyOut, cierre del cambio | `bloom` |

## Límites honestos

- El renderer no tiene IK ni contacto físico: la regadera se sostiene mediante
  una pose; no hay simulación de peso, agua ni agarre.
- El riego y la floración son cambios de estado visuales, no botánica ni
  física. La flor no crece fotograma a fotograma desde una simulación.
- El `detail` de S01 sigue siendo un detalle de objeto dentro de un set grande:
  la mesa y la planta se leen, y la pared ya tiene estructura diegética (cestas,
  estante, manguera, enrejado, cajas) en vez de quedar como una placa vacía.
  Es una decisión visual, no un close-up de cara.
- La v1 se midió en 77 % (S01) y 72 % (S07) de teselas planas. La v2 bajó a
  40 % y 38 % en los stills de control; `inspect` ya no marca ninguna de las
  siete escenas. El cambio es de set y encuadre, no de umbral.
- El still de control se toma en el **50 %** del plano, no al 55 %: en S07 el
  55 % caía después del último caption y convertía una banda sin texto en un
  falso fallo de legibilidad. El caption real del still mide 227/5.0.
- La composición se revisó en stills y el vídeo completo se vuelve a medir con
  `qa`, `avqa`, `inspect` y `evaluate` después del render. La valoración de
  acting/ritmo y la escucha humana siguen pendientes.
