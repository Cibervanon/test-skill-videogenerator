# Graphify audit — uso opcional, local y no runtime

## Instalación aislada

- Fecha de la comprobación: 2026-11-07.
- Paquete: `graphifyy==0.9.103` (el módulo importable es `graphify`).
- Python del sistema: 3.14; `uv` no está instalado, así que se usó `pip` con
  `--target` en un directorio temporal.
- Comando:
  `python -m pip install --disable-pip-version-check --target /tmp/graphify graphifyy`
- Resultado: `PIP_EXIT=0`; import correcto desde
  `/tmp/graphify/graphify/__init__.py`.
- No se añadió Graphify a `requirements`, `package.json`, `AGENTS.md` ni al
  renderer. No se instalaron hooks ni skills de plataforma.

## Extracción local

Primer intento, sin clave:

`PYTHONPATH=/tmp/graphify python -m graphify .`

Graphify encontró 295 archivos de código, 100 documentos y 200 imágenes. Se
detuvo correctamente porque los documentos/imágenes requieren extracción
semántica y no había clave de un proveedor. No se envió nada a un servicio
externo.

Segundo intento, sólo código y sin clustering/LLM:

```bash
cd /tmp/graphify-run
PYTHONPATH=/tmp/graphify python -m graphify extract \
  "C:/Users/W10/Videos/SKILLS" --code-only --no-cluster
```

Resultado: `GRAPHIFY_EXIT=0`.

- 295 archivos de código procesados con tree-sitter/AST local.
- 300 archivos no-código omitidos explícitamente (`--code-only`).
- 3 archivos sin símbolos: `studio/remotion.config.ts`, `studio/src/index.ts`,
  `studio/src/motion-graphics/index.ts`.
- Grafo: **1.477 nodos, 3.432 aristas**.
- Graphify escribió el resultado bajo el target del escaneo, en
  `C:/Users/W10/Videos/SKILLS/graphify-out/graph.json`; se copió a
  `/tmp/graphify-run/graph.json` para conservar la evidencia y se retiró el
  artefacto del repositorio al terminar la auditoría.

## Hallazgos verificados en fuente

### Nodos centrales (no equivalen a calidad)

`graphify god-nodes --graph ... --top 20` devolvió, entre otros:

| nodo | aristas |
|---|---:|
| `Tools` | 66 |
| `build_parser()` | 34 |
| `react` | 29 |
| `CostGuard` | 27 |
| `_create_one()` | 25 |
| `Provider` | 25 |
| `remotion` | 25 |
| `clamp()` | 25 |
| `useStyle()` | 24 |

Lectura: el grafo está dominado por utilidades, parser y tipos de proveedor.
Eso no demuestra que sean el centro narrativo; sólo que son hubs de imports.
No se usó para decidir blocking, acciones ni montaje.

### Ruta de continuidad

`explain "av_director"` devolvió el archivo `scripts/acs/av_director.py`, 16
conexiones, e identificó:

- `plan()`
- `_resolve_actor_continuity()`
- `_actor_sequence()`
- `_actor_exit()`
- `_has_directional_preset()`
- `_sound()`
- `_transition()`

También mostró que `scripts/studio.py` importa `av_director`. Esto se verificó
en el fuente: `studio.py` importa el módulo y `av_director.py` contiene esas
funciones. Es una relación de código real, no una inferencia de comportamiento.

La consulta `actor continuity carry hold planner` encontró `Actors.tsx`
(`ActorHold`, `performSequence`, `phaseSpec`), el campo `continuity` dentro del
manifiesto y una nota de `cmd_captions()` sobre “word timings”. Es un buen mapa
para localizar archivos, pero **mezcla** continuidad de actores con continuidad
de subtítulos; no se usó como prueba de que el estado esté bien resuelto.

## Lo que Graphify no demuestra

- No prueba que una acción tenga causa o consecuencia.
- No distingue una pose de contacto físico.
- No ve el vídeo, no mide motion, freeze, audio ni composición.
- No sabe si un plano se entiende.
- No sustituye `avqa`, `qa`, `inspect`, `evaluate` ni la revisión humana.

## Recomendación

Conservar Graphify **sólo como herramienta opcional de desarrollo**, instalada
fuera del proyecto, para localizar dependencias y rutas de estado. No incluirlo
en producción ni en el pipeline de render. Si se quiere repetir la auditoría,
usar el comando `extract --code-only --no-cluster` y borrar `graphify-out`
después; el grafo es un artefacto de análisis, no una dependencia.

## Limitaciones de esta ejecución

- No se usó un LLM ni un backend semántico; por tanto no hay análisis de
  documentos, papers ni imágenes.
- No se ejecutó clustering, comunidades ni etiquetas semánticas.
- No se instalaron hooks ni instrucciones de agente.
- El grafo incluye el manifiesto JSON como fuente y puede mostrar campos
  llamados `continuity` que pertenecen a subtítulos, no a actores.
