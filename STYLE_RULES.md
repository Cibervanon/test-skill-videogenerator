# Style rules

> Solo aparecen reglas con estado `validated` **y** ámbito global, de estilo, de personaje o de
> proyecto. Una corrección puntual de una escena nunca se escribe aquí.

| ID | Ámbito | Categoría | Regla | Validación |
|---|---|---|---|---|
| FB-0003 | global | technical_rendering | ejecutar el worker sin exponer su carpeta en sys.path | PASS — voice: provider=kokoro speech=True lines=4 words=32 |
| FB-0004 | global | technical_rendering | medir contraste local del texto, no el percentil de toda la banda | PASS — re-inspección 0/4 flagged; tests.test_inspect verde |
