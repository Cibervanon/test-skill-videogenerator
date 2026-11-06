"""Evaluation: a scorecard that separates what was measured from what is pending.

Deliberate choices:

* there is **no single quality score** — averaging a caption contrast with a
  narrative judgement produces a number that means nothing;
* every dimension declares its evidence kind and its status;
* ``compare`` checks a new render against an accepted reference by metric, so a
  regression is a delta on a measurement, not an opinion.

The human review file is ``preproduction/visual_review.json``; until it exists,
the aesthetic dimensions stay ``pending``.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date

DIMENSIONS = [
    {"id": "composition", "kind": "automatic (pixels)", "source": "inspection: empty_ratio, subject_score, depth_bands"},
    {"id": "legibility", "kind": "automatic (pixels)", "source": "inspection: caption contrast on the caption band"},
    {"id": "consistency", "kind": "automatic (pixels)", "source": "inspection: palette drift against the chosen style"},
    {"id": "motion", "kind": "automatic (video)", "source": "qa: mean motion energy"},
    {"id": "technical", "kind": "automatic (qa)", "source": "qa: readable/format/duration/black/freeze"},
    {"id": "sound", "kind": "automatic (qa)", "source": "qa: loudness band + audio activity"},
    {"id": "captions", "kind": "automatic (plan)", "source": "qa: caption coverage from the cue plan"},
    {"id": "overlays", "kind": "geometry (manifest)", "source": "overlays: safe area, face, caption band, collisions"},
    {"id": "ui_composition", "kind": "geometry + timing (manifest)", "source": "uiqa: mode, placement, reading window, occlusion"},
    {"id": "montage", "kind": "structural (edit plan)", "source": "avqa: beats, scales, camera motives, transitions, action and sound coverage"},
    {"id": "narrative", "kind": "subjective", "source": "human review"},
    {"id": "acting", "kind": "subjective", "source": "human review"},
    {"id": "rhythm", "kind": "subjective", "source": "human review"},
    {"id": "style_integrity", "kind": "subjective + measured", "source": "palette drift + human review"},
]


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _qa_check(quality: dict, check_id: str) -> dict | None:
    return next((c for c in (quality or {}).get("checks", []) if c.get("id") == check_id), None)


def scorecard(*, project_dir: str, project: dict, quality: dict | None = None, inspection: dict | None = None, review: dict | None = None, av: dict | None = None) -> dict:
    shots = (inspection or {}).get("shots", [])
    reviewed = [s for s in shots if s.get("status") != "missing still"]
    # E and F are graphic plates by design: a flat background is the composition,
    # so "empty scene" does not apply. They are judged by ui_composition and
    # legibility instead. The inspector already exempts them per shot; the
    # scorecard must use the same rule or it contradicts the inspection it reads.
    modes = {s["id"]: ((s.get("presentation") or {}).get("mode") or "A") for s in project.get("shots", [])}
    scene = [s for s in reviewed if modes.get(s.get("shot"), "A") not in ("E", "F")]
    # A declared detail insert is a deliberate plate, not an empty scene. It is
    # still measured, but it does not fail composition by itself: the prompt's
    # rule is to distinguish a narrative pause from a scene with no content.
    inserts = {
        s.get("id") for s in project.get("shots", [])
        if s.get("beat") == "insert" and s.get("scale") == "detail"
    }
    empty_all = [s for s in scene if s.get("empty_ratio", 0) > 0.55]
    empty = [s for s in empty_all if s.get("shot") not in inserts]
    detail_plates = [s for s in empty_all if s.get("shot") in inserts]
    subjects = [s.get("subject_score", 0) for s in scene]
    contrasts = [s.get("caption_contrast", {}) for s in reviewed]
    shifts = [s.get("palette_shift", 0) for s in reviewed]
    text_risk = [s for s in reviewed if s.get("has_captions") and (s.get("caption_contrast", {}).get("spread", 0) < 70 or s.get("caption_contrast", {}).get("edges", 0) < 5)]
    geometry = (inspection or {}).get("overlays", {})
    review = review or {}

    def subjective(dim: str) -> dict:
        entry = review.get(dim) or review.get("shots", {}).get("*", {}).get(dim)
        if entry:
            return {"status": "reviewed", "kind": "subjective", "evidence": entry.get("note", ""), "value": entry.get("score"), "reviewer": entry.get("reviewer", "")}
        return {"status": "pending", "kind": "subjective", "evidence": "sin revisión humana: no se puntúa", "value": None}

    ui = (inspection or {}).get("ui", {})
    dims = {
        "ui_composition": {
            "status": "measured" if ui else "pending",
            "kind": "geometry + timing (manifest)",
            "value": ui.get("modes") if ui else None,
            "evidence": (
                f"{ui.get('totals', {}).get('problems', 0)} problema(s), {ui.get('totals', {}).get('warnings', 0)} aviso(s) en {ui.get('totals', {}).get('overlays', 0)} elemento(s)"
                if ui
                else "sin plan de UI"
            ),
            "pass": bool(ui.get("ok")) if ui else None,
        },
        "composition": {
            "status": "measured",
            "kind": "automatic (pixels)",
            "value": {
                "empty_ratio_max": max([s.get("empty_ratio", 0) for s in scene], default=None),
                "subject_min": min(subjects) if subjects else None,
                "declared_insert_max": max([s.get("empty_ratio", 0) for s in detail_plates], default=None),
            },
            "evidence": f"{len(empty)} plano(s) de escena (A–D) con más del 55% de teselas planas; E/F se evalúan como placa gráfica; {len(detail_plates)} insert(s) de detalle declarados no se penalizan",
            "pass": not empty,
        },
        "legibility": {
            "status": "measured",
            "kind": "automatic (pixels)",
            "value": {"worst_spread": min([c.get("spread", 0) for c in contrasts], default=None), "worst_edges": min([c.get("edges", 0) for c in contrasts], default=None)},
            "evidence": f"{len(text_risk)} plano(s) con texto de riesgo",
            "pass": not text_risk,
        },
        "consistency": {
            "status": "measured",
            "kind": "automatic (pixels)",
            "value": {"palette_shift_max": max(shifts, default=None)},
            "evidence": "deriva de paleta respecto al estilo elegido",
            "pass": (max(shifts) if shifts else 0) <= 0.30,
        },
        "overlays": {
            "status": "measured",
            "kind": "geometry (manifest)",
            "value": geometry.get("counts", {}),
            "evidence": f"{len(geometry.get('problems', []))} problema(s), {len(geometry.get('warnings', []))} aviso(s)",
            "pass": bool(geometry.get("ok", False)),
        },
        "montage": {
            "status": "measured" if av else "pending",
            "kind": "structural (edit plan)",
            "value": (av or {}).get("metrics") if av else None,
            "evidence": (av or {}).get("summary", {}).get("headline", "sin auditoría de montaje") if av else "sin av_audit.json",
            "pass": bool(av.get("summary", {}).get("ok")) if av else None,
        },
        "style_integrity": {
            **subjective("style_integrity"),
            "measured_part": {"palette_shift_max": max(shifts, default=None)},
        },
        "narrative": subjective("narrative"),
        "acting": subjective("acting"),
        "rhythm": subjective("rhythm"),
    }

    for dim, check_id in (("motion", "motion"), ("technical", "format"), ("sound", "loudness"), ("captions", "caption_plan")):
        check = _qa_check(quality or {}, check_id)
        dims[dim] = {
            "status": "measured" if check else "pending",
            "kind": "automatic (qa)",
            "value": check.get("value") if check else None,
            "evidence": check.get("detail", "no qa report") if check else "sin informe de QA",
            "pass": bool(check.get("pass")) if check else None,
        }

    measured = [d for d in dims.values() if d["status"] == "measured"]
    failed = [k for k, d in dims.items() if d["status"] == "measured" and d["pass"] is False]
    return {
        "project": project.get("id"),
        "style": project.get("style"),
        "dimensions": dims,
        "summary": {
            "measured": len(measured),
            "pending": sum(1 for d in dims.values() if d["status"] == "pending"),
            "failed": failed,
            "headline": "sin fallos medidos" if not failed else "fallos medidos: " + ", ".join(failed),
        },
        "note": "No hay una nota global: cada dimensión conserva su tipo de evidencia. Lo pendiente no se puntúa.",
        "catalogue": DIMENSIONS,
    }


def render_markdown(card: dict) -> str:
    lines = [
        f"# Evaluation — {card.get('project')}",
        "",
        f"**{card['summary']['headline']}** · {card['summary']['measured']} medidas · {card['summary']['pending']} pendientes",
        "",
        "| dimensión | tipo | estado | valor | evidencia |",
        "|---|---|---|---|---|",
    ]
    for dim, entry in card["dimensions"].items():
        value = entry.get("value")
        if isinstance(value, dict):
            value = ", ".join(f"{k}={v}" for k, v in value.items() if v is not None) or "—"
        mark = "✅" if entry.get("pass") else ("❌" if entry.get("pass") is False else "⏳")
        lines.append(f"| {dim} | {entry['kind']} | {mark} {entry['status']} | `{value}` | {entry.get('evidence', '')} |")
    lines += ["", f"> {card['note']}", ""]
    return "\n".join(lines)


def write_card(project_dir: str, card: dict) -> dict:
    quality = os.path.join(project_dir, "quality")
    os.makedirs(quality, exist_ok=True)
    json_path = os.path.join(quality, "evaluation.json")
    md_path = os.path.join(quality, "evaluation.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(card))
    return {"json": json_path, "markdown": md_path}


# --------------------------------------------------------------------------- references


def index_path(root: str) -> str:
    return os.path.join(root, "references", "regression", "index.json")


def load_index(root: str) -> dict:
    return load_json(index_path(root), {}) or {"_comment": "Accepted renders used as regression references.", "renders": []}


def snapshot(root: str, *, render_id: str, video: str, metrics: dict, inspection: dict | None = None, accepted: bool = True, note: str = "") -> dict:
    data = load_index(root)
    entry = {
        "id": render_id,
        "date": date.today().isoformat(),
        "video": os.path.relpath(os.path.abspath(video), root).replace(os.sep, "/"),
        "sha256": sha256(video),
        "bytes": os.path.getsize(video),
        "metrics": metrics,
        "inspection": (inspection or {}).get("shots", []),
        "accepted": accepted,
        "note": note,
    }
    data["renders"] = [r for r in data.get("renders", []) if r["id"] != render_id] + [entry]
    path = index_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return entry


def compare(root: str, *, render_id: str, current: dict) -> dict:
    data = load_index(root)
    reference = next((r for r in data.get("renders", []) if r["id"] == render_id), None)
    if not reference:
        return {"ok": False, "reason": f"no reference render {render_id!r}", "deltas": []}
    deltas = []
    for key, value in current.items():
        old = reference["metrics"].get(key)
        if isinstance(value, (int, float)) and isinstance(old, (int, float)):
            delta = round(value - old, 4)
            deltas.append({"metric": key, "reference": old, "current": value, "delta": delta, "ok": abs(delta) <= max(0.05, abs(old) * 0.25)})
    return {"ok": all(d["ok"] for d in deltas), "reference": reference["id"], "deltas": deltas}
