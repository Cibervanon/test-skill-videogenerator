# UI como dirección (0.7.0)

La UI no es una capa de tarjetas encima del vídeo. Es una **decisión por plano**:
si la frase necesita apoyo visual, en qué modo, en qué zona libre, durante
cuánto tiempo y cómo se retira para que la escena vuelva a mandar.

El renderer dibuja; el director decide. `scripts/acs/ui_director.py` resuelve la
decisión, la escribe en el manifiesto (`presentation`, `placement.box`, `ui`) y
el renderer obedece. Una sola autoridad de geometría, auditable antes de
renderizar.

---

## 1. Los seis modos

| Modo | Qué hace | Cuándo | Qué se ve en el demo |
|---|---|---|---|
| **A** | solo escena | la frase ya está contada por la imagen o hay una acción/emoción | S01, S03 |
| **B** | aclaración breve sobre el fondo | un dato o una aclaración secundaria, con hueco real | S02 (contador), S06 (callout) |
| **C** | escena + UI integrada | una etiqueta/flecha identifica algo del personaje y la acción sigue visible | S07 (etiqueta anclada al cuerpo) |
| **D** | escena atenuada | una comparación necesita foco pero el lugar importa | S04 (barras, scrim) |
| **E** | composición independiente | el diagrama sería ilegible sobre el escenario | S05 (tres pasos) |
| **F** | UI como transición | un dato cierra el plano y conduce al corte | S08 (tarjeta a sangre) |

El modo no se elige por gusto: sale de la intención declarada (o clasificada) y
del tipo de payload. Un gráfico pesado sobre una acción se **descarta**, no se
reubica.

```
intención → modo → payload → caja → ventana → salida
```

## 2. Clasificación de la intención

`classify(text)` reconoce familias por vocabulario: comparación, proceso,
aclaración, cierre, acción, emoción, dato y narración. Es una heurística
declarada, no un modelo de lenguaje: el spec puede fijar `intent` y el director
lo respeta. Cada decisión guarda su `reason` y el QA la audita.

## 3. Colocación adaptativa

Ya no hay posiciones fijas. Para cada elemento:

1. **Tamaño presupuestado** según tipo y modo: compacto en B/C (0.34–0.48 de
   ancho), amplio en D, y el encuadre completo en E.
2. **Anchors semánticos**: `top-left`, `top-right`, `top-center`, `mid-left`,
   `mid-right`, `center`, `bottom-left`, `bottom-right`, `bottom-center`,
   `above-character`, `beside-character`.
3. **Candidatos** ordenados por la escena: si el personaje está a la izquierda,
   primero la columna derecha; si está centrado, los extremos.
4. **Rechazo duro** de cualquier caja que:
   - salga del área segura del 6 %;
   - pise la banda de subtítulos (0.855–0.945);
   - toque el círculo de la cara (con 5 % de margen);
   - en B/C, cubra más del 0.1 % del cuerpo del actor;
   - se solape con otro elemento del mismo plano.
5. **Degradación**: si nada cabe, se reintenta al 85 % y al 72 % del tamaño. Si
   sigue sin caber, el plano **escala de modo** (B → D → E) y la decisión queda
   registrada (`escalated_from`). No se encoge un texto hasta hacerlo ilegible.

La caja del cuerpo es un sobre (cabeza, torso, abrigo, arco de brazos), no un
detector de manos. Está documentado como límite, no disimulado.

## 4. Duración y retirada

La ventana no es un timestamp arbitrario. Sale del **tiempo de lectura** del
propio elemento:

```
lectura = 0.7 s + palabras / 4.0 + (0.3 + 0.2 × series si es gráfico)
```

- En **B/C** la UI debe haber desaparecido antes de 0.90 del plano: la escena
  cierra el plano sola.
- En **D/E** puede llegar a 0.94.
- En **F** llega a 1.0 por definición: el puente existe para alcanzar el corte.

Si la ventana pedida es más corta que la lectura, el director la extiende hasta
el límite del modo; si aun así no cabe, lo avisa y el QA lo marca.

## 5. Continuidad y cámara

- La UI informativa es **screen-space**: un movimiento de cámara no debe
  deformar el dato que el espectador está leyendo.
- Las etiquetas de personaje viven **dentro** del rig de cámara: siguen al
  cuerpo.
- La escena no se reinicia entre planos: actores, luz, vestuario y cámara son
  funciones del reloj del plano. Al retirarse la UI, el mismo plano continúa.
- El modo F sustituye el fotograma por una tarjeta opaca a sangre y el dissolve
  del siguiente plano la revela: la transición la motiva la información, no un
  wipe decorativo.

## 6. QA específico

`scripts/acs/uiqa.py` comprueba, desde el manifiesto:

- modo declarado vs contenido (A sin UI, B–F con UI);
- D con scrim, E marcada independiente, F marcada puente;
- área segura, banda de subtítulos, cara y cuerpo;
- solapes entre elementos en la misma ventana;
- duración frente a lectura;
- retirada antes del corte en B/C;
- cifras con fuente o marca `ilustrativo`;
- intención de acción/emoción sin gráfico pesado;
- repetición del mismo tipo en planos consecutivos;
- densidad frente al presupuesto del estilo.

Además, `uiqa.measure_render` muestrea el MP4 real en el fotograma clave de cada
plano y mide contraste dentro de la caja y detalle de escena alrededor: confirma
que B/C conservan escena y que E/F son placas gráficas. No puntúa gusto.

## 7. Demo `projects/ui_direccion`

27,4 s · 1080×1920 · 30 fps · 8 planos · voz Kokoro en español · 20 cues SRT.

| Plano | Intención | Modo | UI | Ventana | Lectura | Motivo |
|---|---|---|---|---|---|---|
| S01 | narración | A | — | — | — | la escena ya explica la frase |
| S02 | dato | B | contador «3 inviernos» | 0.18–0.84 | 2.2 s | una cifra redonda no necesita escena nueva |
| S03 | acción | A | — | — | — | la acción manda: el insert es la información |
| S04 | comparación | D | barras creído/visto | 0.14–0.89 | 3.15 s | comparar dos estados pide foco |
| S05 | proceso | E | tres pasos | 0.06–0.94 | 3.45 s | el diagrama sería ilegible sobre el set |
| S06 | aclaración | B | callout «el tercer paso» | 0.22–0.90 | 2.45 s | entra, se lee y se retira |
| S07 | acción | C | etiqueta del aprendiz | 0.14–0.82 | 2.2 s | identifica sin tapar el gesto |
| S08 | cierre | F | tarjeta «1 vez» | 0.45–1.0 | 1.2 s | el número conduce al corte |

## 8. Antes / después, medido

La misma auditoría geométrica aplicada a los dos manifiestos:

| Métrica | `sistema_demo` (0.6) | `ui_direccion` (0.7) |
|---|---|---|
| Planos | 4 | 8 |
| Elementos de UI | 7 | 6 |
| Elementos que cubren el cuerpo del actor | **3** | **0** (en B/C) |
| Cobertura máxima del cuerpo | 4.7 % del encuadre | 0 % |
| Elementos que cubren una cara | **2** | **0** |
| Elementos que pisan subtítulos | 0 | 0 |
| UI que sigue en pantalla tras 0.90 en B/C | **1** | **0** |
| Duración media de UI | 3.48 s | 2.65 s |

El demo anterior se conserva sin cambios; el defecto se midió, no se reescribió
la historia. La corrección de fondo fue un bug de unidades en
`circle_hits_box`: mezclaba cajas normalizadas con centros de cara en píxeles, y
por eso una gráfica sobre una cabeza podía pasar como «limpia».

### Evidencia del render

Muestreo del MP4 entregado en el **centro de la ventana de cada elemento**, no en
el keyframe del storyboard (que puede caer a mitad del fundido de entrada):

| modo | planos | detalle de escena | contraste de UI |
|---|---|---|---|
| A | 2 | 3.00 | — (sin UI) |
| B | 2 | 3.96 | 115.5 |
| C | 1 | 4.04 | — (etiqueta anclada: sin caja declarada) |
| D | 1 | 3.86 | 164.0 |
| E | 1 | 3.93 | 31.0 |
| F | 1 | 1.44 | 24.0 |

B conserva más detalle de escena que A (3.96 vs 3.00) porque el contador vive
sobre el cielo nocturno y el set sigue detrás; F cae a 1.44 porque la tarjeta
sustituye el encuadre. El fotograma de S08 a 26,85 s confirma que la tarjeta es
opaca una vez asentada: el aspecto translúcido del primer muestreo era el
fundido de entrada, no una fuga.

La evaluación coincide con la inspección: `composition` excluye E/F (placa
gráfica por diseño) y mide los planos de escena A–D; `ui_composition` sigue
juzgando los seis elementos. 9 dimensiones medidas en verde, 4 pendientes de
revisión humana.

## 9. Comandos

```bash
python scripts/studio.py ui --project projects/ui_direccion \
    --manifest projects/ui_direccion/manifest.json --apply --write-active
python scripts/studio.py storyboard --project projects/ui_direccion
python scripts/studio.py inspect --project projects/ui_direccion
```

`ui` escribe `preproduction/ui_plan.json` + `ui_plan.md` y, con `--apply`, el
manifiesto planificado. El render sigue usando el mismo motor y la misma
composición: no hay un segundo pipeline.

## 10. Lo que este sistema no hace

- **No reajusta la caja por fotograma** mientras la cámara se mueve: la resuelve
  sobre la pose del plano y el QA la valida ahí. Un paneo largo puede acercar al
  actor a la UI a mitad de plano.
- **No rastrea manos.** La zona de acción es el sobre del cuerpo.
- **No lee el guion con un modelo.** La intención es una heurística declarada o
  un campo del spec.
- **No mide el ojo del espectador.** El tiempo de lectura es una estimación de
  4 palabras/s, no eye-tracking.
- **No hay morph entre modos.** D atenúa, E sustituye, F cubre; cada transición
  es un corte o un dissolve intencional, no una metamorfosis.
- **No decide estética.** Elige entre opciones y registra el motivo; el gusto
  sigue pendiente de revisión humana.
