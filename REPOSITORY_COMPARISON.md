# REPOSITORY COMPARISON — what-if-animation → AI CINEMATIC STUDIO

Auditoría del repositorio externo <https://github.com/kelano86/what-if-animation>
(clonado en `.tmp/research/what-if-animation`, commit de la rama `main` del
2026-11-03) frente a esta skill. **Licencia del repositorio: MIT, © 2026
FreshStack** (ver `ATTRIBUTION.md`).

Lo inspeccionado se leyó del código, no de la documentación. Lo que no se pudo
ejecutar se dice explícitamente.

## 0. Qué se ejecutó y qué no

| Acción | Estado |
|---|---|
| `git clone` del repositorio | hecho (7,0 MB, 40 archivos de motor + 40 MP3 de sonido) |
| Lectura de `SKILL.md`, `README.md`, `references/*.md` (801 líneas) | hecho |
| Lectura del motor (`rig.tsx` 480, `props.tsx` 462, `kit.tsx` 223, `light.tsx` 167, `episode.tsx` 164, `room.tsx` 61, `sets/*` 1.526) | hecho |
| Lectura de scripts (`voice.py`, `plan.py`, `stills.mjs`, `board.py`, `sfx.py`, `mixcheck.py`, `master.py`, `motiongrid.py`, `wi.py`) | hecho |
| `npm install` / render de sus dos episodios | **no ejecutado**: su studio es un proyecto aparte y su audio exige clave de ElevenLabs |
| Llamadas a ElevenLabs | **no ejecutadas** (Fase 12: cero créditos) |
| Copia de sus MP3 de `studio/library/sfx` | **no copiados**: fueron generados con su cuenta (ver Licencias) |

## 1. Tabla de comparación

| Componente | Mi implementación actual | Implementación del repositorio | Diferencias | Ventajas del repo | Riesgos | Decisión | Plan de integración |
|---|---|---|---|---|---|---|---|
| **Rig de personajes** | `characters/Character.tsx`: un solo rig, identidad en `cast.json` | `engine/rig.tsx`: un rig, `LOOKS` por personaje, poses interpoladas, manos, yaw, squash, expresiones | El suyo tiene poses con keyframes, manos con pulgar, giro 3D simulado y 9 expresiones | Actuación mucho más rica; `poseAt`/`faceAt` separan cuerpo y cara | Sustituir mi rig rompería los 5 planos ya compuestos | **Parcial**: adoptar el vocabulario de acting (anticipación, overshoot, settle) sin cambiar el dibujo | `Actors.tsx`: rampa de marcha, rebote al aterrizar, overshoot del palín |
| **Identidad persistente** | `cast.json` → `characters/cast.ts` | `LOOKS` + `CastSheet.tsx` renderizado como comprobación | El repo convierte la identidad en una prueba visual | Detecta deriva antes de animar | Ninguno | **Adoptado** | `composition/CastSheet.tsx` + `studio.py cast` |
| **Escenarios** | 4 sets SVG en 2D con texturas procedurales | Sets en perspectiva de un punto (`room.tsx`), 20-40 objetos, luz propia | El suyo tiene perspectiva real y más mobiliario | Profundidad real, luz motivada | Reescribir 4 sets = días y riesgo alto | **Descartado por ahora** | Documentado como siguiente paso; no se toca la geometría actual |
| **Luz / atmósfera** | `atmosphere.tsx`: cast shadows, shafts, fog, dust, glow | `light.tsx`: añade `LightVeil` (velo con agujeros), `Cone`, AO de esquinas | El velo de contraste es lo que hace que su sala "esté encendida" | Barato, invisible como truco, muy visible como resultado | Un velo demasiado fuerte apaga el suelo | **Adoptado** | `LightVeil` + `Cone` en `atmosphere.tsx`, aplicados en `Doorway` |
| **Cámara** | `CameraRig.tsx`: 9 movimientos con curvas | `camT` + `kf` + `shake` dentro de cada plano | El suyo permite reencuadrar por keyframes | Control fino por plano | Duplicaría mi sistema | **Parcial** | `kf`, `settle`, `backOut`, `easeInCubic` añadidos a `engine/math.ts` |
| **Timeline / edición** | `shotTimeline` con `transitionIn` por límite | Segmentos con reloj propio, `reverse`, `look`, `fx` | El suyo permite reproducir un plano al revés y "poderes" | Reutilización de metraje; ritmo por palabras | Rehacer el motor de composición | **Descartado** (no hay caso de uso aún) | Anotado en próximas mejoras |
| **Storyboard** | No existía: se renderizaba directo | `stills.mjs` (un still por plano) + `board.py` (hoja con pies) | Faltaba por completo en mi pipeline | Itera en segundos en vez de 26 minutos | Ninguno | **Adoptado** | `scripts/acs/storyboard.mjs` + `storyboard.py` + `studio.py storyboard` |
| **Voz** | No existía (solo score procedural) | `voice.py`: ElevenLabs `with-timestamps`, pausas recortadas, caché por hash, coste registrado | El suyo sincroniza por palabra | Timings reales, caché, control de gasto | Créditos; clave; dependencia externa | **Adoptado como integración lista y desactivada** | `scripts/acs/voice.py`, `config/voices.json`, `studio.py voice` |
| **Biblioteca de assets** | Inexistente (cada vídeo redibujaba) | `library/sfx` + sets reutilizables, pero **sin catálogo ni metadatos** | El repo reutiliza archivos; no tiene catálogo consultable | Reutilización real de sonidos | Copiar MP3 ajenos | **Mejorado**: catálogo propio | `assets/catalog.json` + `scripts/acs/library.py` + `studio.py assets` |
| **Mezcla** | `qa` mide loudness media | `mixcheck.py` compara voz/efectos/música por ventanas | El suyo protege el diálogo | Detecta música tapando voz | Sin voz no aplica | **Adoptado** | `scripts/acs/mixcheck.py` + `studio.py mix` |
| **Mastering** | `loudnorm` a una pasada, objetivo −16 LUFS | `master.py`: dos pasadas a −14 LUFS, TP −1.5 dBTP | El suyo mide y luego aplica en lineal | Loudness de entrega correcto | Cambia el audio ya validado | **Adoptado** | `assemble.py` mide y aplica `measured_*`; objetivo −14 LUFS |
| **Planificación por palabras** | No existía | `plan.py`: cortes sobre palabras, ritmo de cortes/min | El suyo edita sobre el habla | Ritmo medido, no estimado | Requiere voz real | **Implementado** en 0.4.0: `voice.py` produce `words.json` y `edit.py` alinea los cortes con tolerancia (demo_003: ±0.30 s) | Hecho |
| **Testing** | 21 tests (ahora 35) | Sin tests automatizados; checklist manual en `references/look.md` | El mío es más fuerte en automatización | — | — | **Mantener el mío**, importar el checklist como guía | Ver `VISUAL_STYLE_GUIDE.md` |
| **Documentación** | 12 documentos | 5 referencias muy concretas (`formula`, `look`, `kit`, `sound`, `traps`) | El suyo documenta trampas reales | `traps.md` es oro | — | **Adoptado como referencia** | Enlazado en `ARCHITECTURE.md` |

## 2. Qué se integró (y qué no)

Integrado: catálogo de assets y reutilización, storyboard con stills y hoja de
contacto, hoja de cast, velo de contraste y conos de luz, helpers de easing,
pipeline de voz con caché y autorización explícita, `mixcheck`, mastering a
−14 LUFS en dos pasadas, y las trampas de `traps.md` como checklist.

Descartado a propósito: sets en perspectiva (reescritura total), motor de
segmentos con `reverse`/`looks` (no hay caso de uso), librería de MP3 ajena
(licencia de cuenta), y cualquier copia de personajes o historias.

## 3. Compatibilidad

| Pieza | Repo | Este proyecto | Decisión |
|---|---|---|---|
| Remotion | 4.0.530 | 4.0.540 | no se baja; los helpers copiados son TS puro |
| React | 19.0.0 | 19.1.1 | compatible |
| TypeScript | 5.8.2 | 5.9.2 | compatible |
| Node / FFmpeg / Python | 18+ / ffmpeg+ffprobe / 3.9+ numpy+Pillow | Node 24, FFmpeg 9.0.2, Python 3.14 con numpy 2.5 y Pillow 12 | compatible |
| `@remotion/renderer` | dependencia directa | transitiva de `@remotion/cli` | se resuelve con `createRequire` desde `studio/package.json`; verificado al renderizar el storyboard |

No se añadió ninguna dependencia nueva al proyecto.

## 4. Licencias

| Recurso | Licencia | Uso |
|---|---|---|
| Código del repositorio | MIT (FreshStack) | ideas y adaptaciones reescritas; aviso en `ATTRIBUTION.md` |
| Sus 40 MP3 de `library/sfx` | generados en su cuenta de ElevenLabs | **no copiados** |
| Sus personajes (Pip, Mo…) | originales suyos | **no usados** |
| Google Fonts del repo | SIL OFL | no se usan (este proyecto no carga fuentes remotas) |
| Remotion | licencia propia (gratis para individuos/≤3 personas) | ya en uso |
