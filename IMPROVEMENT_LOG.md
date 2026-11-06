# Improvement log

> Qué se cambió, por qué y qué se midió. Un cambio sin validación se marca como pendiente.

## FB-0001 — ui (validated)

- Observación: El panel de interfaz invadía la banda de subtítulos en el plano final
- Cambio: panel en y=0.58 h=0.22; cajas por defecto recortadas para terminar en 0.84
- Componente: `projects/sistema_demo/spec.json`
- Validación: PASS — inspect: 0/4 flagged, overlays OK

## FB-0002 — composition (validated)

- Observación: La flecha y el gráfico de barras se solapaban en el mismo intervalo
- Cambio: flecha movida a 0.55/0.36, fuera de la caja del gráfico
- Componente: `projects/sistema_demo/spec.json`
- Validación: PASS — inspect: sin avisos de solape

## FB-0003 — technical_rendering (validated)

- Observación: Kokoro fallaba al arrancar el worker: numpy no importaba por la colisión de sys.path con scripts/acs
- Cambio: -P en la sonda y en la síntesis del worker
- Componente: `scripts/acs/kokoro_tts.py`
- Validación: PASS — voice: provider=kokoro speech=True lines=4 words=32

## FB-0004 — technical_rendering (validated)

- Observación: El inspector marcaba texto ilegible en planos con subtítulos correctamente legibles
- Cambio: contraste local por celdas 12x4 y vacío condicionado al detalle
- Componente: `scripts/acs/inspect.py`
- Validación: PASS — re-inspección 0/4 flagged; tests.test_inspect verde
