"""Creative QA, measured from the edit plan rather than guessed from pixels.

This is not a taste score. It checks the decisions that can be verified in the
manifest: whether the cut has a hook and a close, whether shot scales and camera
moves vary without becoming noise, whether every move and dissolve has a stated
motive, whether reaction and action shots exist, whether sound is attached to
action, and whether lines repeat information.

Narrative, performance quality and style still require human review. Those stay
pending; they are never inferred from a passing structural check.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

SCALES = ("wide", "full", "medium", "close", "detail")
ACTIVE_PRESETS = {"walkIn", "dig", "reach", "turn", "call"}
AUTO_SOUND_SCENES = {"bellInsert", "townNight", "fieldDawn"}
REQUIRED_BEATS = ("hook", "setup", "escalation", "reaction", "close")


def _max_actor_scale(shot: dict) -> float:
    return max([float(a.get("scale", 1.5)) for a in shot.get("actors", [])] or [1.5])


def _scale(shot: dict) -> tuple[str, str]:
    declared = shot.get("scale")
    if declared in SCALES:
        return str(declared), "declared"
    peak = _max_actor_scale(shot)
    if peak >= 3.0:
        return "close", "derived from actor scale"
    if peak >= 2.2:
        return "medium", "derived from actor scale"
    if peak >= 1.6:
        return "full", "derived from actor scale"
    if not shot.get("actors"):
        return ("detail" if shot.get("scene") == "bellInsert" else "wide"), "derived from scene"
    return "wide", "derived from actor scale"


def _duration(project: dict) -> float:
    fps = float((project.get("format") or {}).get("fps", 30))
    shots = project.get("shots", [])
    return round(sum(float(s.get("seconds", 0)) for s in shots) - sum(int(s.get("transitionIn", 0)) for s in shots[1:]) / fps, 3)


def _effective_sound(shot: dict) -> list:
    if "sound" in shot:
        return list(shot.get("sound") or [])
    return [{"type": "scene-derived"}] if shot.get("scene") in AUTO_SOUND_SCENES else []


def _longest_run(values: list[str]) -> int:
    best = current = 1 if values else 0
    for a, b in zip(values, values[1:]):
        current = current + 1 if a == b else 1
        best = max(best, current)
    return best


def audit(project: dict) -> dict:
    shots = project.get("shots", [])
    scales, scale_sources = [], set()
    for shot in shots:
        scale, source = _scale(shot)
        scales.append(scale)
        scale_sources.add(source)
    cameras = [str(s.get("camera", "static")) for s in shots]
    beats = [s.get("beat") for s in shots]
    declared_beats = [b for b in beats if b]
    lines = [str(s.get("line") or "").strip() for s in shots]
    spoken = [line for line in lines if line]
    sound = [_effective_sound(s) for s in shots]
    actors = [a for s in shots for a in s.get("actors", [])]
    active = [s for s in shots if any(a.get("preset") in ACTIVE_PRESETS for a in s.get("actors", []))]
    reactions = [s for s in shots if s.get("beat") == "reaction"]
    dissolves = [s for s in shots if s.get("transition") == "dissolve"]
    moving = [s for s in shots if s.get("camera", "static") != "static"]
    motivated = [s for s in moving if str(s.get("cameraMotive") or "").strip()]
    motivated_dissolves = [s for s in dissolves if str(s.get("transitionMotive") or "").strip()]
    duplicate_lines = sorted({line for line in spoken if spoken.count(line) > 1})
    total = _duration(project)

    scale_counts: dict[str, int] = {}
    camera_counts: dict[str, int] = {}
    for scale in scales:
        scale_counts[scale] = scale_counts.get(scale, 0) + 1
    for camera in cameras:
        camera_counts[camera] = camera_counts.get(camera, 0) + 1

    def add(cid: str, label: str, value, ok: bool | None, evidence: str, *, status: str = "measured") -> dict:
        return {"id": cid, "label": label, "status": status, "value": value, "pass": ok, "evidence": evidence}

    checks: list[dict] = []
    if declared_beats:
        missing = [b for b in REQUIRED_BEATS if b not in declared_beats]
        checks.append(add("structure", "hook, setup, escalation, reaction and close are declared", {"missing": missing}, not missing, "beats present in the manifest"))
        checks.append(add("hook", "the hook stays short", next((s["seconds"] for s in shots if s.get("beat") == "hook"), None), next((float(s["seconds"]) <= 3.8 for s in shots if s.get("beat") == "hook"), False), "the premise must arrive before the first explanation"))
        checks.append(add("reaction", "there is at least one reaction shot", len(reactions), bool(reactions), "reaction is a separate edit decision, not an actor idle"))
    else:
        checks.append(add("structure", "beat structure", None, None, "legacy manifest: no beat fields", status="pending"))
        checks.append(add("hook", "hook", None, None, "legacy manifest: no hook decision recorded", status="pending"))
        checks.append(add("reaction", "reaction shot", None, None, "legacy manifest: no reaction beat recorded", status="pending"))

    checks += [
        add("scale_variety", "shot scales vary", {"unique": len(set(scales)), "counts": scale_counts}, len(set(scales)) >= 3, "at least three scales; source: " + ", ".join(sorted(scale_sources))),
        add("scale_run", "no more than two consecutive shots of the same scale", _longest_run(scales), _longest_run(scales) <= 2, "repetition is allowed, a run is not"),
        add("camera_variety", "camera intents vary", {"unique": len(set(cameras)), "counts": camera_counts}, len(set(cameras)) >= 3, "static shots are allowed; an entire film of one move is not"),
        add("camera_motivation", "every non-static camera move has a narrative motive", f"{len(motivated)}/{len(moving)}", (len(motivated) == len(moving)) if moving else None, "motive fields in the manifest" if moving else "no moving camera"),
        add("movement_balance", "movement is neither absent nor constant", round(len(moving) / len(shots), 3) if shots else None, (0.35 <= len(moving) / len(shots) <= 0.9) if shots else None, "share of moving shots; quiet shots are not penalised by themselves"),
        add("transition_motivation", "every dissolve is motivated", f"{len(motivated_dissolves)}/{len(dissolves)}", (len(motivated_dissolves) == len(dissolves)) if dissolves else None, "cuts need no overlap; a dissolve must explain why"),
        add("sound_coverage", "sound follows action in at least half the shots", f"{sum(1 for cues in sound if cues)}/{len(shots)}", (sum(1 for cues in sound if cues) / len(shots) >= 0.5) if shots else None, "declared cues or the existing scene-derived effects"),
        add("action_coverage", "characters perform actions, not only poses", f"{len(active)}/{len(shots)}", (len(active) / len(shots) >= 0.3) if shots else None, "walkIn/dig/reach/turn/call presets"),
        add("information", "no narration line is repeated", duplicate_lines, not duplicate_lines, "duplicate spoken lines would repeat information"),
        add("duration", "the cut is a short vertical piece, not a fragment", total, 20 <= total <= 45, "measured after transition overlaps"),
    ]

    failed = [c["id"] for c in checks if c["status"] == "measured" and c["pass"] is False]
    pending = [c["id"] for c in checks if c["status"] == "pending"]
    return {
        "project": project.get("id"),
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "structural audit of the edit plan; narrative, performance and taste remain human review",
        "metrics": {
            "shots": len(shots),
            "seconds": total,
            "average_shot_seconds": round(total / len(shots), 2) if shots else 0,
            "beat_counts": {b: declared_beats.count(b) for b in dict.fromkeys(declared_beats)},
            "scale_counts": scale_counts,
            "scale_source": sorted(scale_sources),
            "longest_scale_run": _longest_run(scales),
            "camera_counts": camera_counts,
            "moving_ratio": round(len(moving) / len(shots), 3) if shots else 0,
            "camera_motives": f"{len(motivated)}/{len(moving)}",
            "dissolve_motives": f"{len(motivated_dissolves)}/{len(dissolves)}",
            "sound_shots": sum(1 for cues in sound if cues),
            "sound_cues": sum(len(cues) for cues in sound),
            "action_shots": len(active),
            "reaction_shots": len(reactions),
            "two_actor_shots": sum(1 for s in shots if len(s.get("actors", [])) >= 2),
            "wordless_shots": sum(1 for line in lines if not line),
            "spoken_lines": len(spoken),
            "actors_used": sorted({a.get("id") for a in actors if a.get("id")}),
            "scenes": sorted({s.get("scene") for s in shots if s.get("scene")}),
        },
        "checks": checks,
        "summary": {
            "ok": not failed,
            "failed": failed,
            "pending": pending,
            "headline": "sin fallos estructurales" if not failed else "fallos estructurales: " + ", ".join(failed),
        },
        "human_review": ["narrative", "acting", "rhythm", "style_integrity"],
    }


def render_markdown(report: dict) -> str:
    m = report["metrics"]
    lines = [
        f"# Creative QA — {report.get('project')}",
        "",
        f"**{report['summary']['headline']}** · {m['shots']} planos · {m['seconds']}s · media {m['average_shot_seconds']}s",
        "",
        "| comprobación | valor | estado | evidencia |",
        "|---|---|---|---|",
    ]
    for check in report["checks"]:
        mark = "✅" if check["pass"] else ("❌" if check["pass"] is False else "⏳")
        lines.append(f"| {check['label']} | `{check['value']}` | {mark} {check['status']} | {check['evidence']} |")
    lines += [
        "",
        "## Lectura",
        "",
        f"- Escalas: {m['scale_counts']} · racha máxima {m['longest_scale_run']}",
        f"- Cámara: {m['camera_counts']} · motivos {m['camera_motives']}",
        f"- Montaje: {m['action_shots']} planos con acción, {m['reaction_shots']} de reacción, {m['two_actor_shots']} con dos personajes",
        f"- Audio: cues en {m['sound_shots']}/{m['shots']} planos ({m['sound_cues']} eventos)",
        "",
        "> " + report["method"] + ". Lo pendiente no se puntúa.",
        "",
    ]
    return "\n".join(lines)


def compare(before: dict, after: dict) -> dict:
    """Compare two audits on structural metrics. This is not a taste score."""
    b, a = before.get("metrics", {}), after.get("metrics", {})

    def unique(values: dict) -> int:
        return len(values or {})

    rows = [
        ("planos", b.get("shots"), a.get("shots"), "neutral"),
        ("duración (s)", b.get("seconds"), a.get("seconds"), "neutral"),
        ("media por plano (s)", b.get("average_shot_seconds"), a.get("average_shot_seconds"), "lower"),
        ("escalas distintas", unique(b.get("scale_counts")), unique(a.get("scale_counts")), "higher"),
        ("racha máxima de escala", b.get("longest_scale_run"), a.get("longest_scale_run"), "lower"),
        ("cámaras distintas", unique(b.get("camera_counts")), unique(a.get("camera_counts")), "higher"),
        ("proporción en movimiento", b.get("moving_ratio"), a.get("moving_ratio"), "higher"),
        ("planos con acción", b.get("action_shots"), a.get("action_shots"), "higher"),
        ("planos de reacción", b.get("reaction_shots"), a.get("reaction_shots"), "higher"),
        ("planos con audio", b.get("sound_shots"), a.get("sound_shots"), "higher"),
        ("eventos de audio", b.get("sound_cues"), a.get("sound_cues"), "higher"),
        ("planos con dos actores", b.get("two_actor_shots"), a.get("two_actor_shots"), "higher"),
    ]
    deltas = []
    for label, old, new, direction in rows:
        delta = None
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            delta = round(new - old, 3)
        deltas.append({"metric": label, "before": old, "after": new, "delta": delta, "direction": direction})
    return {
        "before": before.get("project"),
        "after": after.get("project"),
        "note": "structural comparison; narrative, acting and taste still require human review",
        "before_failed": before.get("summary", {}).get("failed", []),
        "after_failed": after.get("summary", {}).get("failed", []),
        "before_pending": before.get("summary", {}).get("pending", []),
        "after_pending": after.get("summary", {}).get("pending", []),
        "after_human_review": after.get("human_review", []),
        "rows": deltas,
    }


def render_comparison(report: dict) -> str:
    lines = [
        f"# Before / after — {report['before']} → {report['after']}",
        "",
        "| métrica | antes | después | delta |",
        "|---|---|---|---|",
    ]
    for row in report["rows"]:
        delta = "—" if row["delta"] is None else f"{row['delta']:+g}"
        lines.append(f"| {row['metric']} | {row['before']} | {row['after']} | {delta} |")
    lines += [
        "",
        f"Fallos estructurales: antes `{report['before_failed'] or 'ninguno'}` · después `{report['after_failed'] or 'ninguno'}`",
        f"Pendiente de juicio humano: `{report.get('after_human_review') or report['after_pending']}`",
        "",
        f"> {report['note']}.",
        "",
    ]
    return "\n".join(lines)


def write(project_dir: str, project: dict) -> dict:
    report = audit(project)
    quality = os.path.join(project_dir, "quality")
    os.makedirs(quality, exist_ok=True)
    json_path = os.path.join(quality, "av_audit.json")
    md_path = os.path.join(quality, "av_audit.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(report))
    return {"json": json_path, "markdown": md_path, "report": report}


def write_comparison(project_dir: str, comparison: dict) -> str:
    quality = os.path.join(project_dir, "quality")
    os.makedirs(quality, exist_ok=True)
    path = os.path.join(quality, "before_after.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_comparison(comparison))
    return path
