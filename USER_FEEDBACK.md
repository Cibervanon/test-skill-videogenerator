# User feedback

> Registro de observaciones. **El sistema no aprende solo**: cada fila se aplica a mano y solo
> se marca `validated` cuando existe una comprobación (render, medición o still) que lo demuestra.

Registros: **4** · store: `feedback\records.jsonl`

| ID | Fecha | Categoría | Sev. | Ámbito | Escena | Problema | Estado |
|---|---|---|---|---|---|---|---|
| FB-0001 | 2026-11-04 | ui | high | local | S04 | El panel de interfaz invadía la banda de subtítulos en el plano final | validated |
| FB-0002 | 2026-11-04 | composition | medium | local | S03 | La flecha y el gráfico de barras se solapaban en el mismo intervalo | validated |
| FB-0003 | 2026-11-04 | technical_rendering | blocker | global | — | Kokoro fallaba al arrancar el worker: numpy no importaba por la colisión de sys.path con s | validated |
| FB-0004 | 2026-11-04 | technical_rendering | high | global | S01 | El inspector marcaba texto ilegible en planos con subtítulos correctamente legibles | validated |

## Detalle

### FB-0001 · ui · high · local

- **Problema:** El panel de interfaz invadía la banda de subtítulos en el plano final
- **Corrección pedida:** mantener todo panel por encima de 0.855
- **Componente:** `projects/sistema_demo/spec.json`
- **Evidencia:** inspect: S04 P1 overlaps the caption band (0.85-0.94)
- **Solución aplicada:** panel en y=0.58 h=0.22; cajas por defecto recortadas para terminar en 0.84
- **Validación:** PASS — inspect: 0/4 flagged, overlays OK

### FB-0002 · composition · medium · local

- **Problema:** La flecha y el gráfico de barras se solapaban en el mismo intervalo
- **Corrección pedida:** separar anotación y gráfico
- **Componente:** `projects/sistema_demo/spec.json`
- **Evidencia:** inspect warning: G1 and A1 overlap in the same window
- **Solución aplicada:** flecha movida a 0.55/0.36, fuera de la caja del gráfico
- **Validación:** PASS — inspect: sin avisos de solape

### FB-0003 · technical_rendering · blocker · global

- **Problema:** Kokoro fallaba al arrancar el worker: numpy no importaba por la colisión de sys.path con scripts/acs
- **Corrección pedida:** ejecutar el worker sin exponer su carpeta en sys.path
- **Componente:** `scripts/acs/kokoro_tts.py`
- **Evidencia:** Kokoro worker failed: attempted relative import with no known parent package
- **Solución aplicada:** -P en la sonda y en la síntesis del worker
- **Validación:** PASS — voice: provider=kokoro speech=True lines=4 words=32

### FB-0004 · technical_rendering · high · global

- **Problema:** El inspector marcaba texto ilegible en planos con subtítulos correctamente legibles
- **Corrección pedida:** medir contraste local del texto, no el percentil de toda la banda
- **Componente:** `scripts/acs/inspect.py`
- **Evidencia:** spread 35/31/36 en planos con subtítulos de alto contraste
- **Solución aplicada:** contraste local por celdas 12x4 y vacío condicionado al detalle
- **Validación:** PASS — re-inspección 0/4 flagged; tests.test_inspect verde
