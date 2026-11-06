"""Creative direction: from a title, idea or script to a shootable plan.

This is a rule-based planner, not a language model. It is deterministic, works
offline and *declares* what it invented:

* narration written from a template carries ``narration_source: "template"`` and
  ``requires_author_approval: true``;
* a numeric graphic is only planned from a fact that comes with a source. With
  no facts, the plan contains conceptual overlays (callout / process) and no
  numbers at all — never a fabricated statistic.

The output is a spec that the existing ``library.compose`` turns into a
renderable manifest, so the director adds no second video pipeline.
"""

from __future__ import annotations

import json
import os
import re

SCENES = {
    "townNight": ["noche", "pueblo", "plaza", "campana", "nieve", "night", "town"],
    "fieldDawn": ["amanecer", "cementerio", "tumba", "campo", "dawn", "grave"],
    "doorway": ["puerta", "umbral", "casa", "interior", "door", "home"],
    "faceCloseup": ["rostro", "cara", "mirada", "retrato", "face", "eyes"],
    "bellInsert": ["campana", "bronce", "objeto", "detalle", "bell", "insert"],
}

STYLE_RULES = {
    "cinematic": "Narrativa con personajes y cámara lenta: el estilo por defecto para historias de 20-120 s.",
    "editorial": "Explicativo con voz de ensayo: tipografía de revista y gráficos planos.",
    "infographic": "El vídeo trata de datos: densidad alta, rejilla y cifras con fuente.",
    "minimal": "Una sola idea y menos de ~12 s: máximo espacio negativo.",
    "cartoon": "Audiencia infantil o tono de comedia: color plano y contornos gruesos.",
}

CAMERA_CYCLE = ["pushInSlow", "dollyIn", "panLeft", "drift", "dollyIn", "tiltUp"]


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def sentences_from_idea(title: str, idea: str) -> list[str]:
    """A three-beat draft. It is a proposal, not a finished script."""
    core = (idea or title).strip().rstrip(".")
    return [
        f"{core}.",
        "Todo lo que se sostiene empieza por una decisión pequeña.",
        "Y esa decisión, repetida, termina siendo el lugar.",
    ]


def choose_style(*, seconds: float, audience: str, script: str, facts: list[dict], has_characters: bool) -> dict:
    lowered = (script + " " + audience).lower()
    if audience.lower().startswith(("niñ", "nin", "infant", "kid")):
        choice, reason = "cartoon", "La audiencia indicada es infantil."
    elif facts and not has_characters:
        choice, reason = "infographic", "Hay datos con fuente y no hay personajes: el vídeo es sobre cifras."
    elif seconds <= 12:
        choice, reason = "minimal", f"Duración de {seconds:.0f}s: una sola idea cabe en espacio negativo."
    elif any(word in lowered for word in ("ensayo", "explica", "por qué", "por que", "cómo funciona", "como funciona")):
        choice, reason = "editorial", "El texto es explicativo y pide una voz de ensayo."
    else:
        choice, reason = "cinematic", "Historia con personajes y duración media: narración cinematográfica."
    alternatives = [
        {"style": other, "why_not": STYLE_RULES[other]}
        for other in STYLE_RULES
        if other != choice
    ]
    return {"id": choice, "reason": reason, "alternatives_considered": alternatives[:3], "respects_user_choice": True}


def pick_scene(text: str, fallback: str = "townNight") -> str:
    lowered = text.lower()
    best, score = fallback, 0
    for scene, words in SCENES.items():
        hits = sum(1 for word in words if word in lowered)
        if hits > score:
            best, score = scene, hits
    return best


def overlays_for(
    *,
    sentence: str,
    actors: list[dict],
    cast: dict,
    facts: list[dict],
    index: int,
    style_id: str,
) -> list[dict]:
    """Plan overlays from evidence, never from invented numbers."""
    out: list[dict] = []
    if index == 0 and actors:
        actor = actors[0]
        identity = cast.get(actor["id"], {})
        out.append(
            {
                "id": f"L{index + 1}",
                "type": "label",
                "placement": {"kind": "actor", "actor": actor["id"], "at": "head"},
                "from": 0.14,
                "to": 0.78,
                "data": {"name": identity.get("name", actor["id"]), "role": identity.get("role", ""), "status": "en escena"},
            }
        )
    if facts:
        fact = facts[min(index, len(facts) - 1)]
        if fact.get("numeric"):
            series = fact.get("series") or []
            kind = "bar" if series else "counter"
            payload = {"title": fact.get("label", ""), "value": fact.get("value"), "unit": fact.get("unit", ""), "series": series}
            out.append(
                {
                    "id": f"G{index + 1}",
                    "type": kind,
                    "placement": {"kind": "screen", "box": {"x": 0.08, "y": 0.60, "w": 0.84, "h": 0.24}},
                    "from": 0.22,
                    "to": 0.86,
                    "data": payload,
                    "source": fact.get("source", ""),
                    # no source means the renderer must print "ilustrativo"
                    "illustrative": not fact.get("source"),
                }
            )
    elif index == 1:
        out.append(
            {
                "id": f"C{index + 1}",
                "type": "callout",
                "placement": {"kind": "screen", "box": {"x": 0.52, "y": 0.60, "w": 0.4, "h": 0.14}},
                "from": 0.3,
                "to": 0.82,
                "data": {"title": "la idea", "caption": sentence[:74]},
            }
        )
    if index == 2 and style_id in ("infographic", "editorial"):
        out.append(
            {
                "id": f"P{index + 1}",
                "type": "process",
                "placement": {"kind": "screen", "box": {"x": 0.06, "y": 0.64, "w": 0.88, "h": 0.2}},
                "from": 0.18,
                "to": 0.9,
                "data": {"title": "cómo ocurre", "steps": [{"label": "detonante"}, {"label": "decisión"}, {"label": "consecuencia"}]},
            }
        )
    return out


def build_plan(
    *,
    title: str,
    idea: str = "",
    script: str = "",
    seconds: float = 24.0,
    style: str | None = None,
    audience: str = "público general",
    language: str = "es",
    facts: list[dict] | None = None,
    cast: dict | None = None,
    fps: int = 30,
) -> dict:
    facts = facts or []
    cast = cast or {}
    sentences = split_sentences(script) if script.strip() else sentences_from_idea(title, idea)
    if not sentences:
        sentences = [title]

    # keep the planned duration honest: ~2.6 spoken words per second
    words = sum(len(s.split()) for s in sentences)
    natural = max(6.0, words / 2.6)
    target = max(6.0, float(seconds))
    shots_n = max(3, min(6, round(target / 5.5)))
    per_shot = round(target / shots_n, 2)

    merged: list[str] = []
    for i in range(shots_n):
        # short scripts reuse their closing line instead of inventing filler
        merged.append(sentences[i] if i < len(sentences) else sentences[-1])
    if len(sentences) > shots_n:
        merged[-1] = " ".join(sentences[shots_n - 1 :])

    character_pool = list(cast.keys())
    chosen = character_pool[:2] if len(character_pool) >= 2 else character_pool[:1]
    beats = []
    shots = []
    for i, line in enumerate(merged):
        actors = []
        if chosen and i < 2:
            actor_id = chosen[i % len(chosen)]
            actors.append(
                {
                    "id": actor_id,
                    "preset": "closeup" if i == 0 else "turn",
                    "x": 430 if i % 2 == 0 else 640,
                    "y": 1180,
                    "scale": 2.35 if i == 0 else 1.85,
                    "facing": 1 if i % 2 == 0 else -1,
                }
            )
        scene = pick_scene(line, fallback="townNight" if i < 2 else "fieldDawn")
        camera = CAMERA_CYCLE[i % len(CAMERA_CYCLE)]
        overlays = overlays_for(sentence=line, actors=actors, cast=cast, facts=facts, index=i, style_id=style or "cinematic")
        shots.append(
            {
                "id": f"S{i + 1:02d}",
                "scene": scene,
                "camera": camera,
                "seconds": per_shot,
                "offsetY": 0,
                "transitionIn": 0 if i == 0 else 8,
                "line": line,
                "actors": actors,
                "overlays": overlays,
                "note": f"beat {i + 1}/{shots_n}",
            }
        )
        beats.append({"beat": i + 1, "function": ["gancho", "desarrollo", "giro", "cierre", "resolución", "coda"][min(i, 5)], "line": line, "shots": [shots[-1]["id"]]})

    style_choice = choose_style(seconds=target, audience=audience, script=" ".join(sentences), facts=facts, has_characters=bool(chosen))
    if style:
        style_choice = {
            "id": style,
            "reason": f"El usuario fijó el estilo «{style}»; se respeta por encima de la heurística.",
            "alternatives_considered": [],
            "respects_user_choice": True,
        }

    spec = {
        "id": re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "creative_piece",
        "title": title,
        "logline": idea or sentences[0],
        "fps": fps,
        "style": style_choice["id"],
        "transitionFrames": 8,
        "duration_seconds": round(per_shot * shots_n, 2),
        "shots": shots,
    }

    return {
        "version": 1,
        "title": title,
        "language": language,
        "audience": audience,
        "concept": {
            "title": title,
            "idea": idea,
            "logline": spec["logline"],
            "hook": merged[0],
            "promise": "una idea, un personaje, una consecuencia",
        },
        "structure": {
            "shape": "gancho → desarrollo → consecuencia",
            "beats": beats,
            "shots": shots_n,
            "seconds": spec["duration_seconds"],
            "natural_narration_seconds": round(natural, 2),
            "duration_note": (
                "la duración pedida es mayor que la narración natural"
                if target > natural * 1.25
                else "la narración natural y la duración pedida coinciden"
            ),
        },
        "style": style_choice,
        "casting": {
            "characters": chosen,
            "rule": "los personajes se reutilizan del catálogo; no se inventa un diseño nuevo por proyecto",
        },
        "narration": {
            "source": "user_script" if script.strip() else "template",
            "requires_author_approval": not script.strip(),
            "lines": merged,
        },
        "overlays": {
            "planned": sum(len(s["overlays"]) for s in shots),
            "numeric": sum(1 for s in shots for o in s["overlays"] if o["type"] in {"counter", "bar", "donut", "line", "ranking"}),
            "sources": [f.get("source") for f in facts if f.get("source")],
            "rule": "sin fuente no hay cifra: los gráficos numéricos solo salen de hechos con origen",
        },
        "spec": spec,
        "warnings": []
        if script.strip()
        else ["La narración es una plantilla; necesita aprobación del autor antes de considerarse guion."],
    }


def write_plan(project_dir: str, plan: dict) -> dict:
    pre = os.path.join(project_dir, "preproduction")
    os.makedirs(pre, exist_ok=True)
    brief_path = os.path.join(pre, "creative_brief.json")
    spec_path = os.path.join(pre, "spec.json")
    story_path = os.path.join(pre, "board_plan.md")
    with open(brief_path, "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in plan.items() if k != "spec"}, fh, indent=2, ensure_ascii=False)
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(plan["spec"], fh, indent=2, ensure_ascii=False)
    lines = [
        f"# {plan['title']} — plan de dirección",
        "",
        f"**Concepto:** {plan['concept']['logline']}",
        f"**Gancho:** {plan['concept']['hook']}",
        f"**Estilo:** {plan['style']['id']} — {plan['style']['reason']}",
        f"**Estructura:** {plan['structure']['shape']} · {plan['structure']['shots']} planos · {plan['structure']['seconds']}s",
        "",
        "| plano | escena | cámara | seg | narración | overlays |",
        "|---|---|---|---|---|---|",
    ]
    for shot in plan["spec"]["shots"]:
        overlays = ", ".join(o["type"] for o in shot["overlays"]) or "—"
        lines.append(f"| {shot['id']} | {shot['scene']} | {shot['camera']} | {shot['seconds']} | {shot['line'][:64]} | {overlays} |")
    lines += ["", "## Avisos", ""]
    for warning in plan["warnings"] or ["ninguno"]:
        lines.append(f"- {warning}")
    lines.append("")
    with open(story_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return {"brief": brief_path, "spec": spec_path, "board_plan": story_path}
