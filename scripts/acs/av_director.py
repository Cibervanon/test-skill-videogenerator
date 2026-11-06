"""Audiovisual direction: turn narrative beats into an editable shot plan.

This is a planning layer, not a second renderer. It writes the same manifest the
existing Remotion composition already consumes (scene, camera, actors, line,
transition), and adds the decisions the engine previously lacked: beat function,
shot scale, why the camera moves, why the cut happens, and which sounds belong
to the action.

The planner is deterministic and deliberately conservative. It does not invent
extra shots from prose; the author supplies the beats, and the planner checks
that the sequence has a legible structure, that every camera move has a reason,
and that transitions are motivated rather than decorative.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone

BEAT_FUNCTIONS = (
    "hook",
    "setup",
    "development",
    "insert",
    "escalation",
    "reaction",
    "reveal",
    "close",
)

SCALES = ("wide", "full", "medium", "close", "detail")

CAMERA_MOVES = (
    "static",
    "drift",
    "dollyIn",
    "dollyOut",
    "panLeft",
    "panRight",
    "tiltUp",
    "craneDown",
    "pushInSlow",
    "trackLeft",
    "trackRight",
    "reframe",
)

SOUND_TYPES = ("bell", "footstep", "dig")

DEFAULT_SCALE = {
    "hook": "detail",
    "setup": "close",
    "development": "full",
    "insert": "detail",
    "escalation": "medium",
    "reaction": "close",
    "reveal": "close",
    "close": "wide",
}

DEFAULT_CAMERA = {
    "hook": "tiltUp",
    "setup": "pushInSlow",
    "development": "panRight",
    "insert": "static",
    "escalation": "trackRight",
    "reaction": "dollyIn",
    "reveal": "pushInSlow",
    "close": "dollyOut",
}

DEFAULT_MOTIVE = {
    "hook": "reveal the image that poses the story's question before anyone explains it",
    "setup": "let the information land on the character who carries it",
    "development": "follow the action across the space instead of cutting it into pieces",
    "insert": "hold the detail until it reads; no movement is more informative here",
    "escalation": "move with the decision, not against it",
    "reaction": "close the distance so the reaction is the information",
    "reveal": "arrive at the consequence without announcing the cut",
    "close": "release the frame and show what the story has changed",
}


def _number(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _transition(beat: dict, default_frames: int) -> tuple[str, int, str]:
    raw = beat.get("transition", "cut")
    if isinstance(raw, str):
        kind, motive = raw, beat.get("transitionMotive", "")
    elif isinstance(raw, dict):
        kind = raw.get("type", "cut")
        motive = raw.get("motive", beat.get("transitionMotive", ""))
    else:
        kind, motive = "cut", ""
    kind = str(kind)
    if kind not in ("cut", "dissolve"):
        return kind, 0, str(motive)
    frames = int(beat.get("transitionIn", 0 if kind == "cut" else default_frames))
    if kind == "cut":
        frames = 0
    return kind, frames, str(motive)


def _sound(beat: dict, seconds: float) -> tuple[list[dict], list[str]]:
    problems: list[str] = []
    cues: list[dict] = []
    for cue in beat.get("sound", []) or []:
        if not isinstance(cue, dict):
            problems.append(f"{beat.get('id', '?')}: sound cue is not an object")
            continue
        kind = cue.get("type")
        if kind not in SOUND_TYPES:
            problems.append(f"{beat.get('id', '?')}: unknown sound cue {kind!r}")
            continue
        at = _number(cue.get("at"), 0.0)
        if at < 0 or at > seconds:
            problems.append(f"{beat.get('id', '?')}: sound cue {kind} outside the shot ({at}s)")
            continue
        cues.append({**cue, "type": kind, "at": round(at, 3)})
    return cues, problems


def plan(spec: dict) -> dict:
    """Normalise a beat sheet into the render manifest plus an audit record."""
    problems: list[str] = []
    warnings: list[str] = []
    beats = spec.get("beats") or []
    if not beats:
        problems.append("the beat sheet is empty")

    fps = int(_number(spec.get("fps"), 30))
    default_frames = int(_number(spec.get("transitionFrames"), 10))
    narration = bool(spec.get("narration", False))
    shots: list[dict] = []
    seen_ids: set[str] = set()

    for index, beat in enumerate(beats):
        shot_id = str(beat.get("id") or f"S{index + 1:02d}")
        if shot_id in seen_ids:
            problems.append(f"duplicate shot id {shot_id}")
        seen_ids.add(shot_id)

        function = str(beat.get("function") or "development")
        if function not in BEAT_FUNCTIONS:
            problems.append(f"{shot_id}: unknown beat function {function!r}")
            function = "development"
        scale = str(beat.get("scale") or DEFAULT_SCALE[function])
        if scale not in SCALES:
            problems.append(f"{shot_id}: unknown scale {scale!r}")
            scale = DEFAULT_SCALE[function]
        camera = str(beat.get("camera") or DEFAULT_CAMERA[function])
        if camera not in CAMERA_MOVES:
            problems.append(f"{shot_id}: unknown camera {camera!r}")
            camera = DEFAULT_CAMERA[function]

        seconds = _number(beat.get("seconds"), 3.0)
        if seconds < 0.8:
            problems.append(f"{shot_id}: {seconds}s is too short to read as a shot")

        camera_motive = str(beat.get("cameraMotive") or DEFAULT_MOTIVE[function]).strip()
        if not camera_motive:
            problems.append(f"{shot_id}: camera move {camera} has no narrative motive")

        transition, transition_in, transition_motive = _transition(beat, default_frames)
        if transition == "dissolve" and not transition_motive.strip():
            problems.append(f"{shot_id}: dissolve without a motive is decorative")
        if transition == "dissolve" and transition_in <= 0:
            problems.append(f"{shot_id}: dissolve needs transitionIn frames")

        cues, cue_problems = _sound({**beat, "id": shot_id}, seconds)
        problems.extend(cue_problems)

        line = str(beat.get("line") or "").strip()
        dialogue = bool(beat.get("dialogue", False))
        speaker = str(beat.get("speaker") or ("narrator" if line else "none"))
        if narration and line and not dialogue:
            speaker = "narrator"
        actors = copy.deepcopy(beat.get("actors") or [])
        for actor in actors:
            actor.setdefault("preset", "idle")
            actor.setdefault("scale", 1.5)
            actor.setdefault("facing", 1)
            actor.setdefault("hold", "none")

        shots.append(
            {
                **{k: copy.deepcopy(v) for k, v in beat.items() if k not in ("actors", "sound", "transition")},
                "id": shot_id,
                "beat": function,
                "scene": beat.get("scene"),
                "camera": camera,
                "scale": scale,
                "cameraMotive": camera_motive,
                "seconds": round(seconds, 3),
                "transition": transition,
                "transitionIn": transition_in,
                "transitionMotive": transition_motive,
                "line": line,
                "speaker": speaker,
                "dialogue": dialogue,
                "intent": beat.get("intent", function),
                "note": beat.get("note", ""),
                "actors": actors,
                "sound": cues,
                "overlays": copy.deepcopy(beat.get("overlays") or []),
                "presentation": beat.get(
                    "presentation",
                    {
                        "mode": "A",
                        "reason": "the scene already carries the information: no UI",
                        "scrim": 0.0,
                        "independent": False,
                        "bridge": False,
                    },
                ),
            }
        )

    if beats and not any(s["beat"] == "hook" for s in shots):
        warnings.append("no hook: the opening may explain instead of attract")
    if beats and not any(s["beat"] == "close" for s in shots):
        warnings.append("no close: the edit has no declared ending")
    if shots and shots[-1]["beat"] != "close" and any(s["beat"] == "close" for s in shots):
        warnings.append("the close is not the final shot")
    if any(s["beat"] == "hook" for s in shots):
        hook = next(s for s in shots if s["beat"] == "hook")
        if hook["seconds"] > 3.8:
            warnings.append(f"the hook takes {hook['seconds']}s; the premise may arrive late")

    total = sum(s["seconds"] for s in shots) - sum(s["transitionIn"] for s in shots[1:]) / fps
    functions: dict[str, int] = {}
    scales: dict[str, int] = {}
    cameras: dict[str, int] = {}
    for shot in shots:
        functions[shot["beat"]] = functions.get(shot["beat"], 0) + 1
        scales[shot["scale"]] = scales.get(shot["scale"], 0) + 1
        cameras[shot["camera"]] = cameras.get(shot["camera"], 0) + 1

    manifest = {
        "id": spec.get("id", "av_project"),
        "title": spec.get("title", spec.get("id", "av_project")),
        "logline": spec.get("logline", ""),
        "mode": "LOCAL",
        "style": spec.get("style", "cinematic"),
        "fps": fps,
        "format": {"width": 1080, "height": 1920, "fps": fps, "aspect": "9:16"},
        "transitionFrames": default_frames,
        "narration": narration,
        "library": copy.deepcopy(spec.get("library") or []),
        "shots": shots,
    }
    record = {
        "project": manifest["id"],
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "beat sheet -> manifest; no generated footage, no extra shots",
        "narration": narration,
        "structure": {
            "functions": functions,
            "missing": [f for f in ("hook", "setup", "escalation", "reaction", "close") if f not in functions],
            "hook_seconds": next((s["seconds"] for s in shots if s["beat"] == "hook"), None),
        },
        "edit": {
            "shots": len(shots),
            "seconds": round(total, 3),
            "average_shot_seconds": round(total / len(shots), 2) if shots else 0,
            "scale_counts": scales,
            "camera_counts": cameras,
            "wordless_shots": sum(1 for s in shots if not s["line"]),
            "sound_cues": sum(len(s["sound"]) for s in shots),
        },
        "validation": {"ok": not problems, "problems": problems, "warnings": warnings},
        "shots": [
            {
                "id": s["id"],
                "beat": s["beat"],
                "scale": s["scale"],
                "camera": s["camera"],
                "seconds": s["seconds"],
                "cameraMotive": s["cameraMotive"],
                "transition": s["transition"],
                "transitionMotive": s["transitionMotive"],
                "line": s["line"],
                "sound": [c["type"] for c in s["sound"]],
            }
            for s in shots
        ],
    }
    return {"ok": not problems, "problems": problems, "warnings": warnings, "manifest": manifest, "record": record}


def render_markdown(record: dict) -> str:
    edit = record["edit"]
    lines = [
        f"# AV plan — {record.get('project')}",
        "",
        f"**{edit['shots']} planos · {edit['seconds']}s · media {edit['average_shot_seconds']}s**",
        "",
        "| plano | beat | escala | cámara | motivo | transición | audio |",
        "|---|---|---|---|---|---|---|",
    ]
    for shot in record["shots"]:
        lines.append(
            f"| {shot['id']} | {shot['beat']} | {shot['scale']} | {shot['camera']} | "
            f"{shot['cameraMotive']} | {shot['transition']}: {shot['transitionMotive'] or '—'} | "
            f"{', '.join(shot['sound']) or 'silencio'} |"
        )
    if record["validation"]["warnings"]:
        lines += ["", "## Avisos", ""] + [f"- {w}" for w in record["validation"]["warnings"]]
    lines.append("")
    return "\n".join(lines)


def write_plan(project_dir: str, record: dict) -> dict:
    pre = os.path.join(project_dir, "preproduction")
    os.makedirs(pre, exist_ok=True)
    json_path = os.path.join(pre, "av_plan.json")
    md_path = os.path.join(pre, "av_plan.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(record))
    return {"json": json_path, "markdown": md_path}
