# Fase 3 — Comparación antes / después

## Regla de esta comparación

- El baseline v2 está congelado en `quality/phase3/baseline_v2.mp4`; no se sobrescribe.
- La versión nueva se renderiza con el mismo proyecto, renderer, resolución, FPS y mezcla de voz.
- No se declara una mejora que no esté respaldada por un archivo, una métrica o un still.
- Un PASS técnico no equivale a una mejora cinematográfica.

## Antes: baseline v2

| Área | Evidencia observada |
|---|---|
| Historia | Un jardinero y su aprendiz intentan salvar una planta seca; el agua aparece en el barril. |
| Claridad | Se entiende por la narración; S02 no mostraba un grifo y dependía del texto. |
| Acting | Presets y secuencias existen; S06 es el plano más claro. |
| Acciones | Riego y reacción legibles; el gesto del grifo no tenía objeto visible. |
| Continuidad | Set, barril, mesa, planta y regadera se mantienen; no hay física de agua. |
| Cámara | Variedad de motivos; S01/S07 con demasiada pared; S03/S05 con actores pequeños. |
| Composición | Consistente, pero plana; mucho espacio negativo no siempre intencional. |
| Ritmo | 7 planos / 26.3 s; media 3.76 s. No se ha evaluado percepción completa. |
| Audio | −14.1 dB, voz presente; **no escuchado**. |
| Calidad global | Técnicamente válida, cinematográficamente no cerrada. |

Métricas verificadas: `qa` PASS 13/13; motion 5.081; freeze 0.0165; black 0; `avqa` PASS; `inspect` 0/7; `evaluate` PASS (`empty_ratio_max=0.405`, `worst_edges=5.24`); 187 tests; `tsc` 0.

## Después: referencia v3

Estado: referencia v3 cerrada y validada técnicamente: MP4 de 26.3 s, 789 frames, 1080×1920, H.264/AAC, 14.5 MB; `qa` PASS 13/13; `avqa` PASS; `inspect` 0/7; `evaluate` PASS con 4 dimensiones subjetivas pendientes. La historia nueva también tiene un MP4 validado.

Métricas v3: motion 5.226; freeze 0.0152; black 0; loudness −14.1 dB; voz 0.7188; audio_activity 0.19; caption_plan 0.897.

Cambios aplicados:

- grifo visible en `Greenhouse` y sin trazo de agua;
- S01/S07 sin recorte de planta;
- S02 con grifo y actor completos;
- S03/S05 con actores completos y encuadre más cerrado;
- misma historia, misma voz y misma mezcla.

Comparación técnica final:

| Área | Antes | Después | Evidencia |
|---|---|---|---|
| Historia | La misma | La misma | manifiesto |
| Claridad | Dependía del caption en S02 | Grifo visible; el gesto se lee sin depender del texto | stills/vídeo |
| Acting | Presets | Presets y secuencias; sigue sin IK ni contacto real | vídeo |
| Acciones | Grifo no visible | Grifo visible; gesto sin IK | stills/vídeo |
| Continuidad | Correcta | Misma continuidad; sin física de agua | manifiesto/vídeo |
| Cámara | S01/S07 abiertos | Encuadres ajustados; inspect 0/7 flags | stills |
| Composición | Plana | inspect/evaluate PASS; 4 dimensiones subjetivas pendientes | inspect/evaluate |
| Ritmo | 26.3 s | 26.3 s; motion 5.226; freeze 0.0152 | ffprobe/qa |
| Audio | No escuchado | No escuchado; sólo waveform/espectro | waveform |
| Global | Pendiente | Técnicamente validada; cinematográficamente pendiente | revisión humana |

## Historia nueva: La última luz

No es una comparación contra la planta; es una prueba de generalización.

| Área | Evidencia |
|---|---|
| Premisa | Una mujer espera a alguien que no vuelve; un farolero viene a apagar la lámpara. |
| Conflicto | Deber del farolero vs memoria de la mujer. |
| Objeto | Farol en mano y farol dejado en la nieve. |
| Set | `doorway`, noche, nieve. |
| Acción | Entrada, alcance, reacción, salida. |
| Resolución | Él deja su propia luz; ella se queda. |
| Diferencia real | No hay planta, agua, invernadero ni restauración. |

Estado: MP4 de 21.3 s, 639 frames, 1080×1920, H.264/AAC, 10.5 MB; `qa` PASS 13/13; `avqa` PASS; `inspect` marca sólo S04 (54% de teselas planas); `evaluate` PASS con 4 dimensiones subjetivas pendientes. Motion 5.912, freeze 0.1596, black 0, loudness −13.6 dB, voz 0.7179. El aviso de `av` sobre S05 es correcto: el farol no se transfiere físicamente, se cambia el estado del set en el corte.

## Segunda pieza adicional existente

`av_ultima_medida` es una pieza preexistente de sastrería: 672 frames, 22.4 s, 1080×1920, H.264/AAC. Su contact sheet confirma otro set, otros personajes y otro conflicto. No se ha reescrito en esta fase; se usa como evidencia de variedad, no como prueba de autoría autónoma.

## Criterio de cierre

La comparación técnica ya existe (v3 y la historia nueva). No se cerrará cinematográficamente hasta que:

- se haya reproducido el movimiento completo, no sólo frames;
- se haya escuchado el audio;
- exista revisión humana con timestamps.

Hasta entonces:

**TÉCNICAMENTE VALIDADA, PERO CINEMATOGRÁFICAMENTE PENDIENTE.**
