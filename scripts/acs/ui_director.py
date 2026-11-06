"""Contextual UI director: decide, place and time every overlay.

The renderer draws what it is given; this module decides *whether* a line
deserves UI at all, which presentation mode it needs, where the element can
live without covering a face, a body or the captions, how long a viewer needs
to read it and when it must leave so the scene can take over again.

It is rule-based and deterministic. Every decision carries a ``reason`` that
``uiqa`` audits, and a decision that does not fit is **escalated** (B → D → E)
instead of being forced into a gap that does not exist.

Modes
-----
A  scene only                     (default; no UI)
B  short clarification over it    (small plate, scene and actor keep playing)
C  scene + UI integrated          (label/arrow/highlight bound to the actor)
D  scene attenuated               (scrim, chart takes the focus, actor remains)
E  independent explainer          (neutral plate, no actors, one idea)
F  UI as a transition             (full-frame card carries into the next shot)
"""

from __future__ import annotations

import copy
import json
import os
import re

from . import overlays as O

HEAVY = {"bar", "line", "donut", "ranking", "panel", "process"}
ACTOR_BOUND = {"label", "arrow", "highlight"}

INTENTS = (
    "narracion",
    "aclaracion",
    "dato",
    "comparacion",
    "proceso",
    "accion",
    "emocion",
    "cierre",
)

# Order matters: the first family whose vocabulary appears wins.
KEYWORDS = (
    ("comparacion", ("compara", "comparó", "comparo", "antes", "después", "despues", "mitad", "en cambio", "más que", "mas que", "menos que")),
    ("proceso", ("pasos", "proceso", "etapas", "mecanismo", "primero", "luego", "por último", "por ultimo")),
    ("aclaracion", ("es decir", "o sea", "en realidad", "no era", "se llama", "significa", "porque")),
    ("cierre", ("desde entonces", "al final", "por eso", "así fue", "asi fue", "y nunca")),
    ("accion", ("subió", "subio", "tocó", "toco", "levantó", "levanto", "tiró", "tiro", "abrió", "abrio", "cerró", "cerro", "corrió", "corrio", "caminó", "camino", "señaló", "senalo", "empujó", "empujo", "cogió", "cogio", "saltó", "salto")),
    ("emocion", ("recordó", "recordo", "sintió", "sintio", "temió", "temi", "quiso", "lloró", "lloro", "tembló", "temblo", "pensó", "penso")),
    ("dato", ("cifra", "número", "numero", "contó", "conto", "contaba", "inviernos", "años", "anos", "por ciento", "veces", "docena")),
)

MODE_RULES = {
    "A": "la escena ya explica la frase: no se añade UI",
    "B": "aclaración breve sobre el fondo; la escena sigue viva",
    "C": "la UI identifica algo del personaje y se integra en el encuadre",
    "D": "la comparación pide foco: la escena se atenúa sin desaparecer",
    "E": "la explicación no cabe en el encuadre: composición independiente",
    "F": "la UI conduce al plano siguiente como transición",
}


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def classify(text: str) -> str:
    lowered = (text or "").lower()
    for intent, words in KEYWORDS:
        if any(word in lowered for word in words):
            return intent
    return "narracion"


def choose_mode(*, intent: str, overlays: list[dict], actors: list[dict], ui_role: str = "") -> tuple[str, str]:
    if not overlays:
        return "A", MODE_RULES["A"]
    types = {o.get("type") for o in overlays}
    if ui_role == "bridge" or any(o.get("ui_role") == "bridge" for o in overlays):
        return "F", MODE_RULES["F"]
    if "process" in types:
        return "E", MODE_RULES["E"]
    if types & HEAVY:
        if intent == "comparacion":
            return "D", MODE_RULES["D"]
        if not actors:
            return "E", MODE_RULES["E"]
        return "B", "el gráfico intenta convivir con la escena en formato compacto"
    if types & ACTOR_BOUND and actors:
        return "C", MODE_RULES["C"]
    return "B", MODE_RULES["B"]


def reading_seconds(spec: dict) -> float:
    """How long the element needs on screen, from its own text and data.

    Reading pace is 3.3 words/s (slower than narration, because the viewer is
    also watching the scene); charts add a beat per series so the eye can scan
    the shape before the values.
    """
    data = spec.get("data") or {}
    words = 0
    for key in ("title", "caption", "name", "role", "status", "center"):
        words += len(str(data.get(key) or "").split())
    for item in data.get("labels") or []:
        words += len(str(item).split())
    for key in ("series", "rows", "segments"):
        for row in data.get(key) or []:
            words += len(str(row.get("label", "")).split())
    for step in data.get("steps") or []:
        words += len(str(step.get("label", "")).split()) + len(str(step.get("detail", "")).split())
    base = 0.7
    if spec.get("type") in ("bar", "line", "donut", "ranking"):
        series = data.get("series") or data.get("rows") or data.get("segments") or data.get("points") or []
        base += 0.3 + 0.2 * len(series)
    return round(base + words / 4.0, 2)


def _window(spec: dict, *, mode: str, seconds: float) -> tuple[float, float, float, list[str]]:
    warnings: list[str] = []
    reading = reading_seconds(spec)
    if mode == "F":
        # A bridge exists to reach the cut: it never ends before the shot does.
        limit, default_from, default_to = 1.0, 0.45, 1.0
        return round(min(float(spec.get("from", default_from)), 0.85), 3), 1.0, reading, warnings
    if mode in ("B", "C"):
        # The UI must be gone before the shot ends so the scene can close it.
        limit, default_from, default_to = 0.90, 0.16, None
    else:
        limit, default_from, default_to = 0.94, 0.10, None
    start = float(spec.get("from", default_from))
    if default_to is not None:
        end = float(spec.get("to", default_to))
    else:
        end = float(spec.get("to", min(limit, start + (reading + 0.45) / max(1.0, seconds))))
    if (end - start) * seconds < reading:
        end = min(limit, start + reading / max(1.0, seconds))
    if end <= start:
        end = min(limit, start + 0.05)
    if (end - start) * seconds < reading - 0.05:
        warnings.append(f"{spec.get('id')}: la ventana ({(end - start) * seconds:.1f}s) es más corta que la lectura ({reading}s)")
    return round(start, 3), round(min(end, limit), 3), reading, warnings


def plan_shot(shot: dict, *, cast: dict, style: dict) -> dict:
    seconds = float(shot.get("seconds", 4.0))
    actors = shot.get("actors") or []
    intent = shot.get("intent") or classify(shot.get("line", ""))
    overlays = copy.deepcopy(shot.get("overlays") or [])
    dropped: list[dict] = []
    warnings: list[str] = []

    # A graphic over an action hides the thing the viewer came to see.
    if intent in ("accion", "emocion"):
        heavy = [o for o in overlays if o.get("type") in HEAVY]
        if heavy:
            overlays = [o for o in overlays if o.get("type") not in HEAVY]
            dropped += [{"id": o.get("id"), "type": o.get("type"), "reason": "la acción manda: se retira el gráfico"} for o in heavy]

    role = shot.get("ui_role", "")
    mode, reason = choose_mode(intent=intent, overlays=overlays, actors=actors, ui_role=role)
    budget = int((style.get("ui") or {}).get("maxPanels", 2))
    if mode in ("B", "C") and len(overlays) > budget:
        for extra in overlays[budget:]:
            dropped.append({"id": extra.get("id"), "type": extra.get("type"), "reason": f"el estilo permite {budget} paneles por plano"})
        overlays = overlays[:budget]

    occupied: list[tuple] = []
    placed: list[dict] = []
    escalated_from = None
    for spec in overlays:
        placement = spec.get("placement") or {"kind": "screen"}
        anchor = spec.get("anchor") or ("above-character" if placement.get("kind") == "actor" else "auto")
        if placement.get("kind") == "actor" and mode in ("B", "C"):
            box = O.resolve_box(spec, actors, cast)
        else:
            res = O.resolve_ui_box(O.ui_size(spec.get("type"), mode), actors, cast, occupied=tuple(occupied), anchor=anchor, mode=mode)
            while res["box"] is None and mode in ("B", "D"):
                nxt = res.get("mode_shift") or ("E" if mode == "D" else "D")
                if escalated_from is None:
                    escalated_from = mode
                mode = nxt
                if mode == "F":
                    mode = "E"
                res = O.resolve_ui_box(O.ui_size(spec.get("type"), mode), actors, cast, occupied=tuple(occupied), anchor=anchor, mode=mode)
            if res["box"] is None:
                dropped.append({"id": spec.get("id"), "type": spec.get("type"), "reason": "no queda una zona libre que no tape al personaje ni a los subtítulos"})
                continue
            box = res["box"]
            anchor = res["anchor"] or anchor
            spec["placement"] = {"kind": "screen", "box": {"x": round(box[0], 4), "y": round(box[1], 4), "w": round(box[2], 4), "h": round(box[3], 4)}}
        if mode == "F":
            # A bridge is full-bleed by definition: the safe area would leave a
            # strip of the scene around it and break the cut.
            spec["placement"] = {"kind": "screen", "box": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}}
            spec["safe"] = False

        frm, to, reading, window_warnings = _window(spec, mode=mode, seconds=seconds)
        warnings.extend(window_warnings)
        spec["from"], spec["to"] = frm, to
        spec["ui"] = {
            "intent": intent,
            "mode": mode,
            "anchor": anchor,
            "reading_seconds": reading,
            "window_seconds": round((to - frm) * seconds, 2),
            "reason": spec.get("ui_reason") or f"{MODE_RULES.get(mode, '')}: {reason}",
        }
        occupied.append(box)
        placed.append(spec)

    if escalated_from:
        reason = f"{reason} — se amplió de {escalated_from} a {mode} porque no había hueco sin tapar al personaje"
    presentation = {
        "mode": mode,
        "reason": reason,
        "scrim": 0.58 if mode == "D" else 0.0,
        "independent": mode == "E",
        "bridge": mode == "F",
    }
    return {
        "shot": shot.get("id"),
        "seconds": seconds,
        "intent": intent,
        "mode": mode,
        "reason": reason,
        "escalated_from": escalated_from,
        "overlays": placed,
        "dropped": dropped,
        "warnings": warnings,
        "presentation": presentation,
    }


def plan_project(project: dict, *, cast: dict, styles: dict) -> dict:
    style = (styles.get("styles") or {}).get(project.get("style") or styles.get("default"), {})
    planned = copy.deepcopy(project)
    results = []
    warnings: list[str] = []
    for shot in planned.get("shots", []):
        result = plan_shot(shot, cast=cast, style=style)
        shot["overlays"] = result["overlays"]
        shot["presentation"] = result["presentation"]
        shot["intent"] = result["intent"]
        warnings.extend(result["warnings"])
        results.append({k: v for k, v in result.items() if k != "overlays"} | {
            "overlays": [
                {
                    "id": o.get("id"),
                    "type": o.get("type"),
                    "box": (o.get("placement") or {}).get("box"),
                    "anchor": (o.get("ui") or {}).get("anchor"),
                    "reading_seconds": (o.get("ui") or {}).get("reading_seconds"),
                    "window_seconds": (o.get("ui") or {}).get("window_seconds"),
                    "from": o.get("from"),
                    "to": o.get("to"),
                }
                for o in result["overlays"]
            ]
        })
    modes: dict[str, int] = {}
    for result in results:
        modes[result["mode"]] = modes.get(result["mode"], 0) + 1
    record = {
        "version": 1,
        "project": planned.get("id"),
        "style": planned.get("style"),
        "rule": "la UI está subordinada a la historia: sin justificación no hay elemento",
        "modes": modes,
        "shots": results,
        "warnings": warnings,
        "totals": {
            "shots": len(results),
            "overlays": sum(len(r["overlays"]) for r in results),
            "dropped": sum(len(r["dropped"]) for r in results),
            "escalated": sum(1 for r in results if r.get("escalated_from")),
        },
    }
    return {"project": planned, "record": record}


def to_markdown(record: dict) -> str:
    lines = [
        "# Dirección de UI",
        "",
        f"Proyecto: **{record.get('project')}** · estilo `{record.get('style')}`",
        f"Planos: {record['totals']['shots']} · elementos: {record['totals']['overlays']} · descartados: {record['totals']['dropped']} · escalados: {record['totals']['escalated']}",
        "",
        "| plano | intención | modo | UI | ventana | lectura | motivo |",
        "|---|---|---|---|---|---|---|",
    ]
    for shot in record["shots"]:
        ui = ", ".join(f"{o['type']}({o['anchor']})" for o in shot["overlays"]) or "—"
        windows = ", ".join(f"{o['from']:.2f}–{o['to']:.2f}" for o in shot["overlays"]) or "—"
        reading = ", ".join(f"{o['reading_seconds']}s" for o in shot["overlays"]) or "—"
        lines.append(
            f"| {shot['shot']} | {shot['intent']} | **{shot['mode']}** | {ui} | {windows} | {reading} | {shot['reason']} |"
        )
    if record.get("warnings"):
        lines += ["", "## Avisos", ""] + [f"- {w}" for w in record["warnings"]]
    lines += [
        "",
        "## Reglas aplicadas",
        "",
        "- Un plano de acción o emoción no lleva gráfico: tapa justo lo que el espectador vino a ver.",
        "- El modo B solo se usa si el elemento cabe sin tocar cara, cuerpo, subtítulos ni otro elemento.",
        "- Si no cabe, el director **escala** a D (escena atenuada) o E (composición independiente), y lo registra.",
        "- En B y C la UI se retira antes de 0.90 del plano: la escena vuelve a mandar antes del corte.",
        "- La duración sale del tiempo de lectura del propio elemento, no de un valor universal.",
        "",
    ]
    return "\n".join(lines)


def write_plan(project_dir: str, record: dict) -> dict:
    pre = os.path.join(project_dir, "preproduction")
    os.makedirs(pre, exist_ok=True)
    json_path = os.path.join(pre, "ui_plan.json")
    md_path = os.path.join(pre, "ui_plan.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(record))
    return {"json": json_path, "markdown": md_path}
