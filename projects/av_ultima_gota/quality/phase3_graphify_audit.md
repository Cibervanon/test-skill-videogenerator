# Fase 3 — Auditoría Graphify

## Decisión

Graphify se evaluó como **herramienta opcional de lectura del repositorio**. No se ha añadido a `requirements`, no se ejecuta durante el render, no bloquea tests y no es una dependencia del pipeline audiovisual.

## Instalación y modo de uso

- Paquete probado: `graphifyy==0.9.103`.
- Entorno aislado: `/tmp/graphify`.
- Extracción usada: **code-only**.
- Corpus: 295 archivos del repositorio.
- Resultado: 1.477 nodos y 3.432 aristas.
- La extracción no requiere un modelo externo para producir el grafo code-only; las funciones de resumen semántico o explicación sí pueden requerir un proveedor. Esas funciones no se usaron para el render ni para los tests.

## Qué se investigó en el grafo

1. Dependencias entre `scripts/acs/*.py` y el renderer `studio/`.
2. Puntos de entrada del pipeline (`studio.py av`, `voice`, `render`, `assemble`, `qa`).
3. Responsabilidades duplicadas entre director, QA y evaluación.
4. Código muerto y helpers no alcanzados.
5. Puentes Python → JSON → Remotion (`studio/src/data/project.json`, `manifest.json`).
6. Lugares donde se pierde información entre el beat sheet y el render.

## Hallazgos que el código confirma

- El pipeline tiene una separación real: Python genera/valida el manifiesto; Remotion consume el manifiesto y renderiza. No hay un segundo renderer oculto.
- `av_director.py` concentra la planificación de beats, cámara, secuencias y ledger de continuidad. Es un punto de acoplamiento alto, pero es el punto de entrada correcto para las reglas narrativas.
- `qa.py`, `inspect.py` y `evaluate.py` tienen responsabilidades distintas; no son duplicados exactos. `qa` mide el MP4, `inspect` mide stills y `evaluate` mide assets/composición.
- El renderer recibe `state`, `actors`, `camera`, `zoom`, `offsetX`, `offsetY` y `sequence` a través del manifiesto. El estado de set no se resuelve en Python; se resuelve en React. Esto explica que un prop “dejado” sea un cambio de estado, no una simulación física.
- No hay IK ni física en el grafo de dependencias porque no existen en el código. No se puede atribuir a Graphify una capacidad que el rig no tiene.

## Uso práctico

Graphify sirvió para confirmar la arquitectura y localizar los puntos de pérdida de información:

- el beat sheet no describe el punto físico que debe alcanzar una mano;
- el manifiesto describe un `hold` y un `state` por separado;
- el renderer dibuja props, pero no conserva un prop como entidad física;
- el QA no tiene una consulta de “objeto alcanzado” ni de “prop transferido”.

No se integró como gate. Un grafo de código no sustituye una inspección audiovisual ni una evaluación humana.

## Limitaciones

- El grafo es code-only y no infiere la semántica de una escena.
- No se ejecutó un análisis semántico con modelo externo; no era necesario y habría añadido una dependencia.
- No se conserva el grafo como artefacto de runtime; sólo como evidencia de auditoría.
- La instalación en `/tmp` es efímera; no forma parte de los requisitos del proyecto.

## Conclusión

Graphify aporta valor como **mapa de dependencias y detector de acoplamientos**, no como componente del render. La decisión correcta es mantenerlo fuera del runtime y usar sus hallazgos para mejorar el director, el rig y el QA de forma local.
