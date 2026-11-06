# COMPARISON REPORT — v1 vs. v2 vs. reference

> Estado: cerrado. La v2 se renderizó, se montó con audio, pasó QA y se revisó
> fotograma a fotograma. Nada de lo que aparece aquí se declara superado sin
> haberlo visto en fotogramas del MP4 entregado.

---

## 1. Verificación independiente del estado inicial

Repetida en esta sesión, sin reutilizar el informe anterior como evidencia:

| Comprobación | Comando | Resultado real |
|---|---|---|
| Tests | `python -m unittest discover -s tests` | 21 tests, OK (43,2 s) |
| TypeScript | `npx tsc --noEmit` | 0 errores |
| Entrega | `ffprobe final_video.mp4` | h264 1080×1920, 30/1 fps, aac 48 kHz, 34,133 s, 18,4 MB |
| Decodificación completa | `ffmpeg -v error -i … -f null -` | exit 0, sin errores de decode |
| Modo | `config/studio.config.json` | `mode: local`, `authorize_spend: false`, `budget_usd: 0.0` |
| Red externa | grep de `requests|urllib|https://api` en `scripts/` | sin llamadas de red (solo `xmlns` de SVG) |
| Claves en entorno | `env | grep -c` | 0 |
| Documentación | `ls *.md references/*.md` | 11 documentos + análisis de estilo |

La skill existe, el pipeline se ejecuta, Remotion compila y el vídeo se abre y
decodifica. Esa parte del informe anterior se confirma.

---

## 2. Revisión visual de la v1 (fotogramas 1,5 / 7,4 / 12,5 / 19,5 / 26 / 31,5 s)

Lo que **sí** funciona en la v1:

- vertical 9:16, 30 fps, grano y viñeta coherentes;
- personajes consistentes entre planos (identidad persistente real, no un
  rediseño por plano);
- subtítulos presentes y troceados en 2–3 palabras;
- cámara con un movimiento por plano y sin tirones;
- movimiento ambiental continuo (nieve, bokeh, parpadeo).

Lo que **no** alcanza la referencia (comparado con `refjar_8` y `refjar_25`,
interiores tallados con piedra, pan de oro, alfombra y trono):

1. Los fondos son geometría plana: casas = caja + triángulo, sin materiales.
2. No hay sombras proyectadas ni oclusión: los objetos no se apoyan en el suelo.
3. Un solo plano de profundidad real; el «primer término» es un banco de nieve plano.
4. El personaje es un recorte: sin volumen, brazos de una pieza, sin cejas.
5. Composición centrada y escala pequeña: el sujeto no compite con el set.

---

## 3. Las cinco diferencias, por impacto

### D1 — Materiales y arquitectura (impacto: máximo)

- **Referencia:** muros de sillería con juntas, arcos de medio punto, columnas con
  capitel, trono con capitoné, alfombra con cenefa y motivos, pan de oro en los
  dragones. Cada superficie tiene un material legible.
- **v1:** rellenos planos de un solo color; sin juntas, vetas, tejas ni patrones.
- **Por qué:** el motor no tenía capa de materiales; el SVG solo dibujaba formas.
- **Solución:** patrones SVG procedurales (`<pattern>`): sillería, tablazón, teja,
  nieve moteada, alfombra, papel pintado, escarcha, rayado de pincel.
- **Archivos:** `studio/src/engine/texture.tsx` (nuevo), `scenes/TownNight.tsx`,
  `scenes/Doorway.tsx`, `scenes/BellInsert.tsx`, `scenes/FieldDawn.tsx`.
- **¿Programático?** Sí, al 100 %.
- **Mejora esperada:** el set deja de leerse como diagrama y pasa a leerse como
  ilustración; es la diferencia que más pesa en la primera impresión.

### D2 — Luz volumétrica, sombras y oclusión (impacto: alto)

- **Referencia:** sombras arrojadas bajo el trono y los personajes, luz de ventana
  con caída, oscurecimiento en esquinas y bajo objetos.
- **v1:** luz plana; ningún objeto proyecta sombra; el suelo no recibe luz.
- **Por qué:** no existía una capa de atmósfera; el vignette global no sustituye
  la oclusión local.
- **Solución:** `CastShadow` (elipse desenfocada), `LightShaft` (gradiente
  recortado con blur y `screen`), `FogBand`, `DustMotes`, `Glow`.
- **Archivos:** `studio/src/engine/atmosphere.tsx` (nuevo) + los cuatro sets.
- **¿Programático?** Sí.
- **Mejora esperada:** los objetos se «apoyan»; el interior gana profundidad sin
  añadir un solo polígono nuevo de decorado.

### D3 — Profundidad y oclusores de primer término (impacto: alto)

- **Referencia:** ramas, arcos y mobiliario desenfocado en primer plano; tres o
  cuatro planos con velocidades distintas.
- **v1:** tres planos pobres; primer término = banda de nieve uniforme.
- **Por qué:** el parallax existía, pero no había nada que ocluyera.
- **Solución:** rama desenfocada (filtro de blur) en la esquina, banco de nieve
  con textura y borde iluminado, celosía/arco en el campanario, banco de piedra.
- **Archivos:** los cuatro sets + `CameraRig.tsx` (grupos con profundidad).
- **¿Programático?** Sí.
- **Mejora esperada:** sensación de cámara dentro de un espacio, no frente a un
  decorado plano.

### D4 — Volumen y naturalidad del personaje (impacto: medio-alto)

- **Referencia:** figuras simples pero con sombreado suave, cuello integrado y
  ropa con volumen; el movimiento es de recorte articulado, no de maniquí.
- **v1:** abrigo plano de un color, brazos de un solo segmento, sin cejas, sin
  botas; el caminar se leía mecánico.
- **Por qué:** el rig priorizaba la silueta y no tenía articulaciones ni sombreado.
- **Solución:** gradiente de abrigo + oclusión bajo el mentón y en el bajo,
  brazo en dos segmentos con codo, botas, cejas con inclinación emocional,
  patillas bajo el gorro, cabeza con adelanto/lag en la marcha y balanceo del
  abrigo.
- **Archivos:** `studio/src/characters/Character.tsx`,
  `studio/src/composition/Actors.tsx`.
- **¿Programático?** Sí.
- **Mejora esperada:** deja de parecer un muñeco rígido sin añadir física.

### D5 — Composición y tamaño de plano (impacto: medio)

- **Referencia:** sujeto descentrado, tamaño de plano muy variable (general,
  medio, primer plano, inserto) y aire negativo compuesto.
- **v1:** sujeto centrado, escala pequeña, sin variación de tamaño de plano.
- **Por qué:** las posiciones se eligieron para «que se viera todo», no para
  componer.
- **Solución:** actores a tercios (izquierda en S01, centro-derecha en S02,
  derecha en S03), escalas 1,4 / 2,05 / 5,15 / 1,85, inserto sin actores, y
  oclusor de primer término que enmarca.
- **Archivos:** `studio/src/data/project.json`.
- **¿Programático?** Sí.
- **Mejora esperada:** el plano se lee como decisión de dirección.

### Lo que NO se ha tocado (y por qué)

- Grano, viñeta y halación: ya estaban; subirlos no arregla nada.
- Número de partículas: no es el problema.
- Postproceso con filtros: enmascararía la falta de material, no la resolvería.

---

## 4. Resultados

### 4.1 Verificación de la nueva entrega (repetida, no heredada)

| Comprobación | Comando | Resultado real |
|---|---|---|
| Tests | `python -m unittest discover -s tests` | 21 tests, OK |
| TypeScript | `npx tsc --noEmit` | 0 errores |
| Render | `npx remotion render …` | 1054/1054 fotogramas, 24,7 MB |
| Entrega | `ffprobe final_video.mp4` | h264 1080×1920, 30/1 fps, aac 48 kHz, 35,133 s, 18,7 MB, 1053 fotogramas |
| Decodificación completa | `ffmpeg -v error -i … -f null -` | exit 0, sin errores |
| QA | `python scripts/studio.py qa` | **PASS 10/10** (motion 6,976; black 0,0; freeze 0,0968; −15,0 dB; caption_plan 1,0) |
| Modo | `config/studio.config.json` | `local`, `authorize_spend: false` |

Cero llamadas de red y cero claves durante todo el proceso: el vídeo se generó
únicamente con código.

### 4.2 Qué se ve ahora en el MP4 (fotogramas 1,5 / 12,5 / 21,5 / 27 / 33,5 s)

- **S01 plaza (8 s):** casas entramadas con teja, juntas y nieve en los aleros;
  campana con tejadillo, yugo y cuerdas; farol encendido; pozo, trineo y troncos;
  personajes a la izquierda (tercios) con sombra proyectada.
- **S02 umbral (8–15 s):** interior cálido a través de la puerta: papel pintado,
  alfombra con cenefa, estante con tarros, abrigo colgado, cuadro, lámpara con
  derrame de luz sobre la nieve.
- **S03 campo (15–23 s):** once lápidas de cuatro tipos (redonda, cruz tallada,
  obelisco, losa) con nieve y musgo, capilla con ventana iluminada, muro de
  sillería, tumba abierta con sombra interior y luz de borde.
- **S04 campanario (23–29 s):** celosías, arco de piedra, polea y bronce con
  reflejo lateral.
- **S05 vuelta a la plaza (29–35 s):** corte seco desde el inserto, mismo set y
  mismo encuadre que S01.

### 4.3 v1 frente a v2, criterio por criterio

| Criterio | v1 (conservada en `output/v1/`) | v2 (entregada) | Referencia |
|---|---|---|---|
| Superficies | relleno plano de un color | patrones procedurales (tabla, teja, sillería, papel, alfombra, nieve) | textura pictórica real |
| Luz | plana, viñeta global | sombras proyectadas, haces recortados, niebla por bandas, motas | oclusión con caída gradual |
| Profundidad | 2 planos | 3–4 planos con rama desenfocada y setos que ocluyen | 4 planos con foco óptico |
| Personaje | recorte plano, brazo de una pieza | volumen, codo, botas, cejas, patillas, balanceo | figura con pliegues y manos |
| Composición | sujeto centrado, escala pequeña | tercios + escalas 1,50 / 1,40 / 2,05 / 5,15 / 1,85 | tamaños de plano muy variados |
| Duración | 34,1 s | 35,1 s | 60,6–65,2 s |

### 4.4 Defectos encontrados en esta revisión y corregidos

1. **Transición mal restada en la línea de tiempo.** El renderer descontaba el
   `transitionIn` del plano actual en vez del siguiente: la película duraba 0,47 s
   más que el audio y los dissolves se comportaban como fundidos desde negro.
   Corregido en `shotTimeline` (`composition/Demo.tsx`), con la misma aritmética
   en `audio_gen.py`, `qa.py` y el test de audio.
2. **Doble exposición del personaje** entre S02 y S03 (el mismo abrigo a 2,05× y
   5,15×): ahora ese límite es un corte seco; el dissolve queda solo entre sets
   distintos (S03→S04, S04→S05).
3. **Banda negra en el borde izquierdo** del plano del umbral: el paneo movía el
   lienzo 7 % con un zoom de 1,10× que solo cubría 5 % por lado. `panLeft` y
   `panRight` pasan a 1,16× con 5,5 % de desplazamiento.
4. **Lápidas que leían como cucharas:** la cruz era un mástil fino con un brazo
   ancho arriba. Ahora es una losa con la cruz tallada en la cara.
5. **Palín duplicado y hoyo plano:** el set tenía una pala plantada además de la
   del personaje; se eliminó, y el hoyo recibió sombra interior.
6. **`qa.py` con `del fade` dentro del bucle** (NameError a partir del segundo
   plano) y **test de audio desactualizado** tras el cambio de transiciones.

### 4.5 Lo que sigue lejos de la referencia (sin adornos)

- El motor es **vector plano**: la referencia tiene pincelada, textura pictórica
  y luz con oclusión progresiva; aquí la luz son gradientes y elipses.
- Los personajes **no tienen manos, ni pliegues, ni modelado facial**: son un
  recorte articulado con volumen simulado.
- No hay **profundidad de campo óptica** ni parallax 3D real: solo desenfoques
  fijos y grupos desplazados.
- La referencia dura **60–65 s** con 0–1 cortes duros por minuto; esta pieza dura
  35 s con 2 cortes duros y 2 dissolves, así que el ritmo es más denso.
- `motion` de QA da **6,976** frente a 24–30 medidos en las referencias, pero la
  métrica no es comparable (distinta escala de diferencia de luminancia): sirve
  como guarda contra congelados, no como nota estética.

### 4.6 Artefactos

```
projects/demo_001/output/v1/                 render anterior, intacto
projects/demo_001/output/final_video.mp4     v2 entregada (35,133 s, 18,7 MB)
projects/demo_001/output/final_video_preview.mp4
projects/demo_001/output/picture_silent.mp4  render sin audio (24,7 MB)
```
