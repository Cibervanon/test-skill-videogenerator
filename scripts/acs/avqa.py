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
ACTIVE_PRESETS = {"walkIn", "dig", "reach", "turn", "call", "point", "react"}
TERMINAL_PRESETS = {"idle", "closeup", "dig", "reach", "turn", "call", "point", "react"}

# A beat is not only a label: it implies a framing range. A reaction shot in
# extreme wide is usually a missed reaction, and a close is rarely a detail.
FRAMING = {
    "hook": {"detail", "close", "medium"},
    "setup": {"wide", "full", "medium", "close"},
    "development": {"wide", "full", "medium", "close"},
    "insert": {"detail", "close", "medium"},
    "escalation": {"medium", "close", "full"},
    "reaction": {"close", "medium", "detail"},
    "reveal": {"detail", "close", "medium"},
    "close": {"wide", "full", "medium"},
}
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


def _presets(actor: dict) -> list[str]:
    """The base preset plus every phase of a compound performance."""
    values = [str(actor.get("preset") or "idle")]
    values.extend(str(p.get("preset") or "idle") for p in actor.get("sequence", []) or [] if isinstance(p, dict))
    return values


def _sequence_audit(shots: list[dict]) -> dict:
    """Validate declared action scores without pretending to judge acting."""
    issues: list[dict] = []
    unfinished: list[dict] = []
    sequences = 0
    phases = 0
    for shot in shots:
        for actor in shot.get("actors", []):
            sequence = actor.get("sequence") or []
            if not sequence:
                continue
            sequences += 1
            phases += len(sequence)
            cursor = 0.0
            for index, phase in enumerate(sequence):
                if not isinstance(phase, dict):
                    issues.append({"shot": shot.get("id"), "actor": actor.get("id"), "phase": index, "problem": "not an object"})
                    continue
                try:
                    start = float(phase.get("start"))
                    end = float(phase.get("end"))
                except (TypeError, ValueError):
                    issues.append({"shot": shot.get("id"), "actor": actor.get("id"), "phase": index, "problem": "missing window"})
                    continue
                if not 0.0 <= start < end <= 1.0:
                    issues.append({"shot": shot.get("id"), "actor": actor.get("id"), "phase": index, "problem": f"window {start}..{end}"})
                if start < cursor - 0.001:
                    issues.append({"shot": shot.get("id"), "actor": actor.get("id"), "phase": index, "problem": "overlaps previous phase"})
                cursor = max(cursor, end)
            last = sequence[-1] if isinstance(sequence[-1], dict) else {}
            if last.get("preset") == "walkIn" or last.get("preset") not in TERMINAL_PRESETS:
                unfinished.append({"shot": shot.get("id"), "actor": actor.get("id"), "last": last.get("preset")})
    return {"sequences": sequences, "phases": phases, "issues": issues, "unfinished": unfinished}


def _continuity_audit(shots: list[dict]) -> dict:
    """Measure the resolved actor ledger, not just the declared x fields."""
    issues: list[dict] = []
    evidence = 0
    carried = 0
    previous: dict[str, dict] = {}
    for shot in shots:
        scene = shot.get("scene")
        for actor in shot.get("actors", []):
            actor_id = actor.get("id")
            if not actor_id:
                continue
            state = actor.get("continuity")
            if not isinstance(state, dict):
                previous[actor_id] = None
                continue
            evidence += 1
            if state.get("carried"):
                carried += 1
            entry = state.get("entry") or {}
            exit_state = state.get("exit") or {}
            prev = previous.get(actor_id)
            if prev and prev.get("scene") == scene and isinstance(prev.get("exit"), dict):
                previous_x = prev["exit"].get("x")
                entry_x = entry.get("x")
                if isinstance(previous_x, (int, float)) and isinstance(entry_x, (int, float)):
                    shift = round(float(entry_x) - float(previous_x), 1)
                    if abs(shift) > 260 and not state.get("carried") and not state.get("motive"):
                        issues.append({"shot": shot.get("id"), "actor": actor_id, "shift": shift, "reason": "same-scene teleport"})
            previous[actor_id] = {"scene": scene, "exit": exit_state}
    return {"evidence": evidence, "carried": carried, "issues": issues}


def _axis_order(shot: dict) -> list[str]:
    """Left-to-right actor order in a shot, using the declared stage x."""
    actors = [a for a in shot.get("actors", []) if a.get("id") and isinstance(a.get("x"), (int, float))]
    return [a["id"] for a in sorted(actors, key=lambda actor: float(actor["x"]))]


def _axis_violations(shots: list[dict]) -> list[dict]:
    """Detect an unmotivated 180-degree flip between two shots in one scene.

    Only a reversed left-to-right order of the *same* two or more actors counts;
    a new composition, a new scene or a deliberate single close-up does not.
    """
    out: list[dict] = []
    for before, after in zip(shots, shots[1:]):
        if before.get("scene") != after.get("scene"):
            continue
        a, b = _axis_order(before), _axis_order(after)
        if len(a) < 2 or len(b) < 2 or set(a) != set(b):
            continue
        if a == list(reversed(b)):
            out.append({"from": before.get("id"), "to": after.get("id"), "before": a, "after": b})
    return out


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
    active = [s for s in shots if any(preset in ACTIVE_PRESETS for a in s.get("actors", []) for preset in _presets(a))]
    sequences = _sequence_audit(shots)
    continuity = _continuity_audit(shots)
    phased_shots = [s for s in shots if any(a.get("sequence") for a in s.get("actors", []))]
    reactions = [s for s in shots if s.get("beat") == "reaction"]
    dissolves = [s for s in shots if s.get("transition") == "dissolve"]
    moving = [s for s in shots if s.get("camera", "static") != "static"]
    motivated = [s for s in moving if str(s.get("cameraMotive") or "").strip()]
    motivated_dissolves = [s for s in dissolves if str(s.get("transitionMotive") or "").strip()]
    duplicate_lines = sorted({line for line in spoken if spoken.count(line) > 1})
    total = _duration(project)
    beat_positions = {s.get("beat"): i for i, s in enumerate(shots) if s.get("beat")}
    hook_first = beat_positions.get("hook") == 0 if "hook" in beat_positions else None
    close_last = beat_positions.get("close") == len(shots) - 1 if "close" in beat_positions else None
    framing_mismatches = []
    for shot in shots:
        beat = shot.get("beat")
        if beat not in FRAMING:
            continue
        scale, _ = _scale(shot)
        if scale not in FRAMING[beat]:
            framing_mismatches.append({"shot": shot.get("id"), "beat": beat, "scale": scale, "allowed": sorted(FRAMING[beat])})
    axis_violations = _axis_violations(shots)
    static_shots = [s for s in shots if s.get("camera", "static") == "static"]
    unmotivated_static = [s for s in static_shots if not str(s.get("cameraMotive") or "").strip()]
    static_ratio = round(len(static_shots) / len(shots), 3) if shots else 0.0
    purpose_missing = [
        s for s in shots
        if not str(s.get("line") or "").strip()
        and not s.get("actors")
        and s.get("beat") not in ("insert", "reaction")
        and s.get("scene") != "bellInsert"
    ]
    densities = [
        (len(str(s.get("line") or "").split()), round(len(str(s.get("line") or "").split()) / max(0.8, float(s.get("seconds", 0))), 3), s.get("id"))
        for s in shots
        if str(s.get("line") or "").strip()
    ]
    max_density = max((d[1] for d in densities), default=0.0)
    bad_intensity = [
        {"shot": s.get("id"), "value": s.get("cameraIntensity")}
        for s in shots
        if s.get("cameraIntensity") is not None
        and not (
            (s.get("camera", "static") == "static" and float(s["cameraIntensity"]) == 0.0)
            or 0.35 <= float(s["cameraIntensity"]) <= 1.35
        )
    ]

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
        checks.append(add("beat_order", "the hook opens and the close ends the cut", {"hook_first": hook_first, "close_last": close_last}, bool(hook_first) and bool(close_last), "the order is a narrative decision, not just a set of labels"))
        checks.append(add("beat_framing", "every beat has a framing that can carry it", [m["shot"] for m in framing_mismatches], not framing_mismatches, "hook/reaction/close are checked against a framing range"))
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
        add("action_coverage", "characters perform actions, not only poses", f"{len(active)}/{len(shots)}", (len(active) / len(shots) >= 0.3) if shots else None, "walkIn/dig/reach/turn/call presets, including phases"),
        add(
            "action_completion",
            "declared compound actions are ordered and finish on a terminal preset",
            {"sequences": sequences["sequences"], "unfinished": sequences["unfinished"]},
            (not sequences["issues"] and not sequences["unfinished"]) if sequences["sequences"] else None,
            "a sequence ending mid-walk or with an invalid window is a performance error",
            status="measured" if sequences["sequences"] else "pending",
        ),
        add("information", "no narration line is repeated", duplicate_lines, not duplicate_lines, "duplicate spoken lines would repeat information"),
        add("speech_density", "no line is delivered faster than the ear can follow", max_density, max_density <= 4.0 if densities else None, "worst word/second rate; wordless shots are skipped"),
        add("shot_purpose", "every shot carries a line, an action or a declared insert/reaction", [s.get("id") for s in purpose_missing], not purpose_missing, "a shot with no information is a candidate for removal"),
        add("axis_continuity", "two-shots in the same scene keep screen direction", len(axis_violations), not axis_violations, "only a reversed actor order between the same two actors is flagged"),
        add(
            "character_continuity",
            "actors keep their stage state or declare a motivated move",
            {"carried": continuity["carried"], "issues": continuity["issues"]},
            (not continuity["issues"]) if continuity["evidence"] else None,
            "resolved entry/exit ledger; carry across a scene change is refused",
            status="measured" if continuity["evidence"] else "pending",
        ),
        add("static_intent", "static shots are deliberate and bounded", {"shots": len(static_shots), "ratio": static_ratio, "unmotivated": [s.get("id") for s in unmotivated_static]}, static_ratio <= 0.4 and not unmotivated_static, "a held frame must have a motive; a film of tripods is not variety"),
        add("camera_intensity", "declared camera intensity stays inside the authored range", bad_intensity, not bad_intensity, "0.35..1.35; static shots use 0"),
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
            "phased_shots": len(phased_shots),
            "action_phases": sequences["phases"],
            "action_sequences": sequences["sequences"],
            "unfinished_sequences": sequences["unfinished"],
            "sequence_issues": sequences["issues"],
            "reaction_shots": len(reactions),
            "two_actor_shots": sum(1 for s in shots if len(s.get("actors", [])) >= 2),
            "axis_violations": axis_violations,
            "carried_actors": continuity["carried"],
            "continuity_issues": continuity["issues"],
            "static_shots": len(static_shots),
            "static_ratio": static_ratio,
            "framing_mismatches": framing_mismatches,
            "purpose_missing": [s.get("id") for s in purpose_missing],
            "max_words_per_second": max_density,
            "camera_intensity_invalid": bad_intensity,
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

    def ratio(value, total):
        return round(float(value or 0) / float(total), 3) if total else None

    rows = [
        ("planos", b.get("shots"), a.get("shots"), "neutral"),
        ("duración (s)", b.get("seconds"), a.get("seconds"), "neutral"),
        ("media por plano (s)", b.get("average_shot_seconds"), a.get("average_shot_seconds"), "lower"),
        ("escalas distintas", unique(b.get("scale_counts")), unique(a.get("scale_counts")), "higher"),
        ("racha máxima de escala", b.get("longest_scale_run"), a.get("longest_scale_run"), "lower"),
        ("cámaras distintas", unique(b.get("camera_counts")), unique(a.get("camera_counts")), "higher"),
        ("proporción en movimiento", b.get("moving_ratio"), a.get("moving_ratio"), "higher"),
        ("planos con acción", b.get("action_shots"), a.get("action_shots"), "higher"),
        ("planos con secuencia", b.get("phased_shots"), a.get("phased_shots"), "higher"),
        ("fases de acción", b.get("action_phases"), a.get("action_phases"), "higher"),
        ("planos de reacción", b.get("reaction_shots"), a.get("reaction_shots"), "higher"),
        ("planos con audio", b.get("sound_shots"), a.get("sound_shots"), "higher"),
        ("eventos de audio", b.get("sound_cues"), a.get("sound_cues"), "higher"),
        ("planos con dos actores", b.get("two_actor_shots"), a.get("two_actor_shots"), "higher"),
        ("planos estáticos", b.get("static_shots"), a.get("static_shots"), "lower"),
        ("densidad máxima de habla", b.get("max_words_per_second"), a.get("max_words_per_second"), "lower"),
        ("violaciones de eje", len(b.get("axis_violations") or []), len(a.get("axis_violations") or []), "lower"),
        # Length-independent readings: a 6-shot demo and a 10-shot story are
        # not comparable on raw counts alone.
        ("acción por plano", ratio(b.get("action_shots"), b.get("shots")), ratio(a.get("action_shots"), a.get("shots")), "higher"),
        ("dos actores por plano", ratio(b.get("two_actor_shots"), b.get("shots")), ratio(a.get("two_actor_shots"), a.get("shots")), "higher"),
        ("variedad de cámara por plano", ratio(unique(b.get("camera_counts")), b.get("shots")), ratio(unique(a.get("camera_counts")), a.get("shots")), "higher"),
        ("variedad de escala por plano", ratio(unique(b.get("scale_counts")), b.get("shots")), ratio(unique(a.get("scale_counts")), a.get("shots")), "higher"),
        ("eventos de audio por segundo", ratio(b.get("sound_cues"), b.get("seconds")), ratio(a.get("sound_cues"), a.get("seconds")), "higher"),
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
