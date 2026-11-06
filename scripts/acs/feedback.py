"""Structured feedback memory.

This module *records and scopes* corrections. It does not learn by itself and it
never turns one scene note into a global rule: every record declares a scope,
and the generated documents keep the distinction visible.

Store layout::

    feedback/records.jsonl          one JSON record per line (append-only)
    feedback/regression_cases.json  checks that a fix must not break
    USER_FEEDBACK.md                table of every observation
    VISUAL_PREFERENCES.md           recurring notes (still not rules)
    STYLE_RULES.md                  only rules with validated evidence
    IMPROVEMENT_LOG.md              what was applied and what was measured

Categories follow the vocabulary of the production brief; keywords are matched
in Spanish and English because the notes are written in Spanish.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone

STORE_DIR = "feedback"
RECORDS = os.path.join(STORE_DIR, "records.jsonl")
REGRESSION = os.path.join(STORE_DIR, "regression_cases.json")

DOCS = {
    "feedback": "USER_FEEDBACK.md",
    "preferences": "VISUAL_PREFERENCES.md",
    "rules": "STYLE_RULES.md",
    "log": "IMPROVEMENT_LOG.md",
}

CATEGORIES = {
    "character_design": ("character_design", "diseño de personaje", "character design"),
    "character_animation": ("character_animation", "animación de personaje"),
    "acting": ("acting", "interpretación", "actuación", "emoción"),
    "background": ("background", "fondo", "fondos", "escenario"),
    "composition": ("composition", "composición", "encuadre"),
    "camera": ("camera", "cámara", "movimiento de cámara"),
    "lighting": ("lighting", "iluminación", "luz"),
    "color": ("color", "paleta", "saturación", "contraste"),
    "typography": ("typography", "tipografía", "texto", "etiqueta", "rótulo"),
    "ui": ("ui", "interfaz", "hud", "panel", "tarjeta"),
    "motion_graphics": ("motion graphics", "gráfico", "gráficos", "infografía"),
    "storytelling": ("storytelling", "narrativa", "historia", "guion"),
    "editing": ("editing", "montaje", "corte", "ritmo"),
    "audio": ("audio", "sonido", "música"),
    "voice": ("voice", "voz", "narración"),
    "consistency": ("consistency", "consistencia", "estilo ha cambiado", "coherencia"),
    "technical_rendering": ("technical", "render", "artefacto", "parpadeo", "roto"),
}

SEVERITIES = ("low", "medium", "high", "blocker")
STATUSES = ("recorded", "in_progress", "applied", "validated", "rejected")
SCOPES = ("local", "project", "character", "style", "global")

KEYWORDS = {
    "camera": ("cámara", "camara", "movimiento", "plano", "zoom", "paneo"),
    "typography": ("etiqueta", "texto", "subtítulo", "subtitulo", "tipografía", "tipografia", "legible", "tamaño"),
    "background": ("fondo", "fondos", "escenario", "vacío", "vacio", "simple"),
    "acting": ("rígido", "rigido", "emoción", "emocion", "actuación", "actuacion", "expresión"),
    "editing": ("cortes", "corte", "ritmo", "montaje", "demasiados"),
    "motion_graphics": ("gráfico", "grafico", "gráficos", "graficos", "presentación", "presentacion", "infografía"),
    "ui": ("interfaz", "hud", "panel", "tarjeta", "callout"),
    "consistency": ("estilo", "consistencia", "coherencia", "cambia entre escenas"),
    "voice": ("voz", "narración", "narracion", "entonación", "entonacion"),
    "lighting": ("luz", "iluminación", "iluminacion", "sombra"),
    "color": ("color", "paleta", "saturación", "saturacion", "contraste"),
    "composition": ("composición", "composicion", "encuadre", "solapa", "tapa"),
    "storytelling": ("historia", "narrativa", "guion", "guión", "final"),
}

GLOBAL_MARKERS = ("todas", "todos", "siempre", "nunca", "en general", "global", "en todo el vídeo", "en todo el video")
STYLE_MARKERS = ("estilo", "look", "paleta de", "estética", "estetica")
CHARACTER_MARKERS = ("personaje", "el viejo", "la viuda", "el aprendiz", "el guardián", "character")
PROJECT_MARKERS = ("este vídeo", "este video", "este proyecto", "esta pieza")
LOCAL_MARKERS = ("esta escena", "este plano", "en esta", "aquí", "aqui", "en s0", "en s1", "en s2", "en s3", "en s4")


class FeedbackError(ValueError):
    pass


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def records_path(root: str) -> str:
    return os.path.join(root, RECORDS)


def load(root: str) -> list[dict]:
    path = records_path(root)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _save_all(root: str, records: list[dict]) -> None:
    path = records_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _next_id(records: list[dict]) -> str:
    numbers = [int(r["id"].split("-")[1]) for r in records if str(r.get("id", "")).startswith("FB-")]
    return f"FB-{max(numbers, default=0) + 1:04d}"


def classify(text: str) -> str:
    lowered = text.lower()
    best, score = "composition", 0
    for category, words in KEYWORDS.items():
        hits = sum(1 for word in words if word in lowered)
        if hits > score:
            best, score = category, hits
    return best


def infer_scope(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in GLOBAL_MARKERS):
        return "global"
    if any(marker in lowered for marker in STYLE_MARKERS):
        return "style"
    if any(marker in lowered for marker in CHARACTER_MARKERS):
        return "character"
    if any(marker in lowered for marker in PROJECT_MARKERS):
        return "project"
    if any(marker in lowered for marker in LOCAL_MARKERS):
        return "local"
    return "local"


def infer_severity(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("roto", "no se ve", "ilegible", "error", "artefacto")):
        return "high"
    if "demasiado" in lowered or "too " in lowered:
        return "medium"
    return "low"


def add(
    root: str,
    *,
    problem: str,
    requested: str = "",
    project: str = "",
    scene: str = "",
    component: str = "",
    category: str | None = None,
    severity: str | None = None,
    scope: str | None = None,
    evidence: str = "",
) -> dict:
    if not problem.strip():
        raise FeedbackError("a feedback record needs a problem statement")
    records = load(root)
    record = {
        "id": _next_id(records),
        "date": date.today().isoformat(),
        "created_at": _now(),
        "project": project,
        "scene": scene,
        "component": component,
        "problem": problem.strip(),
        "requested": requested.strip(),
        "category": category or classify(problem + " " + requested),
        "severity": severity or infer_severity(problem + " " + requested),
        "scope": scope or infer_scope(problem + " " + requested),
        "evidence": evidence,
        "solution": "",
        "status": "recorded",
        "validation": "",
    }
    if record["category"] not in CATEGORIES:
        raise FeedbackError(f"unknown category {record['category']!r}")
    if record["severity"] not in SEVERITIES:
        raise FeedbackError(f"unknown severity {record['severity']!r}")
    if record["scope"] not in SCOPES:
        raise FeedbackError(f"unknown scope {record['scope']!r}")
    records.append(record)
    _save_all(root, records)
    return record


def get(root: str, record_id: str) -> dict | None:
    return next((r for r in load(root) if r["id"] == record_id), None)


def update(root: str, record_id: str, **fields) -> dict:
    records = load(root)
    for record in records:
        if record["id"] == record_id:
            record.update({k: v for k, v in fields.items() if k in record})
            if "status" in fields and fields["status"] not in STATUSES:
                raise FeedbackError(f"unknown status {fields['status']!r}")
            record["updated_at"] = _now()
            _save_all(root, records)
            return record
    raise FeedbackError(f"no record {record_id}")


def apply_fix(root: str, record_id: str, *, solution: str, component: str = "") -> dict:
    if not solution.strip():
        raise FeedbackError("an applied fix needs a solution statement")
    fields = {"solution": solution.strip(), "status": "applied"}
    if component:
        fields["component"] = component
    return update(root, record_id, **fields)


def validate(root: str, record_id: str, *, evidence: str, passed: bool = True) -> dict:
    if not evidence.strip():
        raise FeedbackError("validation needs evidence (a measurement, a still, a render)")
    return update(
        root,
        record_id,
        status="validated" if passed else "in_progress",
        validation=f"{'PASS' if passed else 'FAIL'} — {evidence.strip()}",
    )


def recurring(root: str, minimum: int = 2) -> list[dict]:
    """Categories that came back more than once. A pattern is evidence, not a rule."""
    groups: dict[str, list[dict]] = {}
    for record in load(root):
        groups.setdefault(record["category"], []).append(record)
    out = []
    for category, items in groups.items():
        if len(items) >= minimum:
            out.append(
                {
                    "category": category,
                    "count": len(items),
                    "ids": [i["id"] for i in items],
                    "scopes": sorted({i["scope"] for i in items}),
                    "promotable": all(i["status"] in ("validated",) for i in items) and all(i["scope"] != "local" for i in items),
                }
            )
    return sorted(out, key=lambda g: -g["count"])


# --------------------------------------------------------------------------- documents


def _table(rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |")
    return "\n".join(lines)


def render_feedback_doc(root: str) -> str:
    items = load(root)
    lines = [
        "# User feedback",
        "",
        "> Registro de observaciones. **El sistema no aprende solo**: cada fila se aplica a mano y solo",
        "> se marca `validated` cuando existe una comprobación (render, medición o still) que lo demuestra.",
        "",
        f"Registros: **{len(items)}** · store: `{RECORDS}`",
        "",
    ]
    if not items:
        lines += ["Todavía no hay observaciones registradas.", ""]
    else:
        rows = [
            [
                r["id"],
                r["date"],
                r["category"],
                r["severity"],
                r["scope"],
                (r["scene"] or "—"),
                r["problem"][:90],
                r["status"],
            ]
            for r in items
        ]
        lines += [_table(rows, ["ID", "Fecha", "Categoría", "Sev.", "Ámbito", "Escena", "Problema", "Estado"]), ""]
        lines += ["## Detalle", ""]
        for r in items:
            lines += [
                f"### {r['id']} · {r['category']} · {r['severity']} · {r['scope']}",
                "",
                f"- **Problema:** {r['problem']}",
                f"- **Corrección pedida:** {r['requested'] or '—'}",
                f"- **Componente:** `{r['component'] or '—'}`",
                f"- **Evidencia:** {r['evidence'] or '—'}",
                f"- **Solución aplicada:** {r['solution'] or '—'}",
                f"- **Validación:** {r['validation'] or '—'}",
                "",
            ]
    return "\n".join(lines)


def render_preferences_doc(root: str) -> str:
    groups = recurring(root)
    lines = [
        "# Visual preferences",
        "",
        "> Preferencias **recurrentes** derivadas de las observaciones. Todavía no son reglas: una",
        "> preferencia necesita evidencia validada y un ámbito no local para promocionarse.",
        "",
    ]
    if not groups:
        lines += ["No hay categorías repetidas (mínimo 2 observaciones).", ""]
        return "\n".join(lines)
    rows = [[g["category"], g["count"], ", ".join(g["ids"]), ", ".join(g["scopes"]), "sí" if g["promotable"] else "no"] for g in groups]
    lines += [_table(rows, ["Categoría", "Repeticiones", "IDs", "Ámbitos", "Promocionable"]), ""]
    return "\n".join(lines)


def render_rules_doc(root: str) -> str:
    validated = [r for r in load(root) if r["status"] == "validated" and r["scope"] in ("global", "style", "character", "project")]
    lines = [
        "# Style rules",
        "",
        "> Solo aparecen reglas con estado `validated` **y** ámbito global, de estilo, de personaje o de",
        "> proyecto. Una corrección puntual de una escena nunca se escribe aquí.",
        "",
    ]
    if not validated:
        lines += ["No hay reglas promocionadas todavía.", ""]
        return "\n".join(lines)
    rows = [[r["id"], r["scope"], r["category"], r["requested"] or r["problem"], r["validation"]] for r in validated]
    lines += [_table(rows, ["ID", "Ámbito", "Categoría", "Regla", "Validación"]), ""]
    return "\n".join(lines)


def render_log_doc(root: str) -> str:
    items = [r for r in load(root) if r["status"] in ("applied", "validated", "in_progress")]
    lines = [
        "# Improvement log",
        "",
        "> Qué se cambió, por qué y qué se midió. Un cambio sin validación se marca como pendiente.",
        "",
    ]
    if not items:
        lines += ["Sin cambios registrados.", ""]
        return "\n".join(lines)
    for r in items:
        lines += [
            f"## {r['id']} — {r['category']} ({r['status']})",
            "",
            f"- Observación: {r['problem']}",
            f"- Cambio: {r['solution'] or 'pendiente'}",
            f"- Componente: `{r['component'] or '—'}`",
            f"- Validación: {r['validation'] or 'pendiente de comprobación'}",
            "",
        ]
    return "\n".join(lines)


def write_documents(root: str) -> dict:
    outputs = {
        "feedback": render_feedback_doc(root),
        "preferences": render_preferences_doc(root),
        "rules": render_rules_doc(root),
        "log": render_log_doc(root),
    }
    paths = {}
    for key, text in outputs.items():
        path = os.path.join(root, DOCS[key])
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        paths[key] = path
    return paths


def regression_cases(root: str) -> list[dict]:
    data = load_json(os.path.join(root, REGRESSION), {}) or {}
    return data.get("cases", [])


def add_regression_case(root: str, *, case_id: str, description: str, check: str, threshold: str, evidence: str = "") -> dict:
    path = os.path.join(root, REGRESSION)
    data = load_json(path, {}) or {"_comment": "Checks an accepted render must keep passing.", "cases": []}
    if any(c["id"] == case_id for c in data["cases"]):
        raise FeedbackError(f"regression case {case_id} already exists")
    case = {"id": case_id, "description": description, "check": check, "threshold": threshold, "evidence": evidence, "added": date.today().isoformat()}
    data["cases"].append(case)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return case


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
