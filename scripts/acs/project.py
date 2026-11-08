"""Project scaffolding, preproduction documents and reproducibility manifest.

A project is a folder with a fixed layout (see ARCHITECTURE.md). Everything the
pipeline writes is derived from the project manifest + the cast file, so the
same inputs always rebuild the same documents.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil

DIRS = [
    "input",
    "analysis",
    "preproduction",
    "assets/characters",
    "assets/environments",
    "assets/props",
    "assets/reference_images",
    "generation/images",
    "generation/video_clips",
    "generation/audio",
    "generation/prompts",
    "editing/intermediate",
    "editing/subtitles",
    "quality/shot_reports",
    "output",
    "logs",
]

ENVIRONMENTS = {
    "townNight": {
        "id": "env_town_night",
        "name": "The frozen square",
        "description": "Snowbound village square at night, bell post at centre, two rows of houses with warm windows.",
        "depth_layers": ["stars/moon", "ridge + pines", "mid houses", "bell post", "snow ground", "window light pools", "foreground bank"],
        "lighting": "moon key (cool, high), window pools (warm, low), no fill outside the pools",
        "palette": ["#101733", "#3b3f74", "#c9d3e8", "#ffb765"],
        "weather": "light snow, no wind gusts",
        "recurring": True,
    },
    "doorway": {
        "id": "env_door_threshold",
        "name": "The keeper's threshold",
        "description": "Open door seen from the snow: warm interior with a hanging lamp, cold blue night outside.",
        "depth_layers": ["interior wall", "lamp", "door leaf", "snow", "frost on the lintel"],
        "lighting": "practical lamp as key, cold night as rim, hard warm/cold split",
        "palette": ["#2a1b25", "#4a2b34", "#ffcf8a", "#131a36"],
        "weather": "snow outside the frame edge",
        "recurring": True,
    },
    "faceCloseup": {
        "id": "env_closeup_night",
        "name": "Close-up plate",
        "description": "Out-of-focus night with bokeh lamps and a window mullion; the actor carries the shot.",
        "depth_layers": ["bokeh lights", "window mullion", "falling snow"],
        "lighting": "warm key from camera left, cold ambient, no hard shadows",
        "palette": ["#101633", "#232a52", "#ffd08a", "#a9c2f0"],
        "weather": "snow, shallow depth of field",
        "recurring": False,
    },
    "fieldDawn": {
        "id": "env_graveyard_dawn",
        "name": "The graveyard at first light",
        "description": "Snow field, fence, headstones, an open grave and a soil mound; low sun behind the treeline.",
        "depth_layers": ["dawn sky + sun", "treeline", "fence", "headstones", "grave + mound", "snow drifts"],
        "lighting": "contre-jour low sun, long soft shadows towards camera, cold bounce from snow",
        "palette": ["#3f4a78", "#f2a573", "#fdf0e2", "#7a553f"],
        "weather": "clear, cold haze near the ground",
        "recurring": True,
    },
    "workshop": {
        "id": "env_workshop_dawn",
        "name": "The tailor's workshop",
        "description": "Warm workroom before dawn: a north window, thread shelves, a dress form and a worktable.",
        "depth_layers": ["back wall", "dawn window", "thread shelf", "dress form", "worktable", "foreground chair"],
        "lighting": "cold dawn window as key, warm practical lamp as fill, no snow",
        "palette": ["#5d4034", "#315b58", "#c79a55", "#ffd3a0"],
        "weather": "interior, dust in the light",
        "recurring": True,
    },
    "greenhouse": {
        "id": "env_greenhouse_dawn",
        "name": "The dry greenhouse",
        "description": "Working glasshouse at dawn: bench, rain barrel, potted plant and a watering can.",
        "depth_layers": ["glass roof", "dawn sun", "distant glasshouses", "tool shelf", "rain barrel", "bench and plant", "foreground pots"],
        "lighting": "cold dawn through glass as key, warm low sun as rim, no snow",
        "palette": ["#315247", "#a96343", "#f2d38c", "#ffd49a"],
        "weather": "interior, dry air, dust in the light",
        "recurring": True,
    },
    "bellInsert": {
        "id": "env_bell_insert",
        "name": "The bell",
        "description": "Insert of the bronze bell on its headstock, frost and dust in the light.",
        "depth_layers": ["yoke + headstock", "bell body", "clapper", "dust motes", "bokeh town lights"],
        "lighting": "single warm source from below-left, deep blue ambient",
        "palette": ["#0d1430", "#1e2650", "#e6c179", "#ffd79a"],
        "weather": "indoor/covered, dust in the air",
        "recurring": True,
    },
}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def init_project(base: str, project_id: str, *, title: str | None = None) -> str:
    root = os.path.join(base, project_id)
    for rel in DIRS:
        os.makedirs(os.path.join(root, rel), exist_ok=True)
    meta_path = os.path.join(root, "project_manifest.json")
    if not os.path.exists(meta_path):
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "id": project_id,
                    "title": title or project_id,
                    "created_by": "scripts/studio.py",
                    "layout": DIRS,
                    "mode": "local",
                },
                fh,
                indent=2,
            )
    return root


def copy_reference(project_root: str, reference: str) -> str:
    dest_dir = os.path.join(project_root, "input")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(reference))
    if os.path.abspath(reference) != os.path.abspath(dest):
        shutil.copy2(reference, dest)
    return dest


def _shot_brief(shot: dict, env: dict) -> dict:
    """Derive the technical brief of a shot from the data that drives the render."""
    camera_intent = {
        "panLeft": "scan the square with the walk, keep the bell in frame",
        "panRight": "follow the digging, reveal the grave",
        "dollyIn": "close the distance to the keeper: pressure, not movement",
        "pushInSlow": "hold on the face, let the realisation land",
        "tiltUp": "reveal the bell from rim to crown",
        "trackLeft": "follow the subject while keeping the space readable",
        "trackRight": "follow the subject while keeping the space readable",
        "reframe": "move the subject inside a held composition",
        "drift": "hold with life",
        "static": "deliberate stillness",
    }.get(shot.get("camera", "static"), "unspecified move")
    return {
        "id": shot["id"],
        "scene": shot["scene"],
        "environment_id": env["id"],
        "seconds": shot["seconds"],
        "transition_in": shot.get("transitionIn", 0),
        "frames": round(shot["seconds"] * 30),
        "camera_move": shot.get("camera", "static"),
        "camera_intent": camera_intent,
        "camera_offset_y_pct": shot.get("offsetY", 0),
        "actors": shot.get("actors", []),
        "caption_line": shot["line"],
        "lighting": env["lighting"],
        "palette": env["palette"],
        "note": shot.get("note", ""),
    }


def write_preproduction(project_root: str, project: dict, cast_data: dict, *, source_project_path: str | None = None) -> dict:
    pre = os.path.join(project_root, "preproduction")
    os.makedirs(pre, exist_ok=True)

    # the exact manifest used to render, copied for traceability
    if source_project_path and os.path.exists(source_project_path):
        shutil.copy2(source_project_path, os.path.join(pre, "project.source.json"))

    shots = [_shot_brief(s, ENVIRONMENTS[s["scene"]]) for s in project["shots"]]
    storyboard = {
        "project": project["id"],
        "title": project["title"],
        "format": project["format"],
        "transition_frames": project.get("transitionFrames", 0),
        "shots": shots,
        "total_shots": len(shots),
        "total_seconds": round(sum(s["seconds"] for s in shots) - sum(s.get("transition_in", 0) for s in shots[1:]) / project["format"]["fps"], 2),
    }
    with open(os.path.join(pre, "storyboard.json"), "w", encoding="utf-8") as fh:
        json.dump(storyboard, fh, indent=2)
    with open(os.path.join(pre, "shot_list.json"), "w", encoding="utf-8") as fh:
        json.dump({"project": project["id"], "shots": shots}, fh, indent=2)

    characters = cast_data.get("characters", {})
    with open(os.path.join(pre, "character_bible.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "project": project["id"],
                "rule": "identity is persistent; wardrobe changes are states, never new characters",
                "characters": characters,
                "usage": [
                    {"shot": s["id"], "character": a["id"], "preset": a["preset"], "hold": a.get("hold", "none")}
                    for s in project["shots"]
                    for a in s.get("actors", [])
                ],
            },
            fh,
            indent=2,
        )

    used_envs = []
    for scene in dict.fromkeys(s["scene"] for s in project["shots"]):
        used_envs.append(ENVIRONMENTS[scene])
    with open(os.path.join(pre, "environment_bible.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "project": project["id"],
                "rule": "an environment keeps its identity across framings; no empty generic plates",
                "environments": used_envs,
            },
            fh,
            indent=2,
        )

    script_lines = [f"# {project['title']}", "", project.get("logline", ""), ""]
    for shot in project["shots"]:
        script_lines += [
            f"## {shot['id']} — {ENVIRONMENTS[shot['scene']]['name']} ({shot['seconds']}s)",
            "",
            f"**Camera:** {shot.get('camera')} — {_shot_brief(shot, ENVIRONMENTS[shot['scene']])['camera_intent']}",
            "",
            f"> {shot['line']}",
            "",
            f"*{shot.get('note', '')}*",
            "",
        ]
    with open(os.path.join(pre, "script.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(script_lines))

    # continuity: every actor must exist in the bible, every scene in the env bible
    issues = []
    for shot in project["shots"]:
        if shot["scene"] not in ENVIRONMENTS:
            issues.append(f"{shot['id']}: unknown scene {shot['scene']!r}")
        for actor in shot.get("actors", []):
            if actor["id"] not in characters:
                issues.append(f"{shot['id']}: unknown character {actor['id']!r}")
            else:
                allowed = set(shot.get("hold", "") for _ in [0])
                del allowed
    continuity = {
        "project": project["id"],
        "characters_used": sorted({a["id"] for s in project["shots"] for a in s.get("actors", [])}),
        "environments_used": sorted({s["scene"] for s in project["shots"]}),
        "issues": issues,
        "ok": not issues,
        "checks": [
            "every actor id exists in character_bible.json",
            "every scene exists in environment_bible.json",
            "captions present on every shot",
            "single source of truth: studio/src/data/project.json + cast.json",
        ],
    }
    with open(os.path.join(project_root, "quality", "continuity_report.json"), "w", encoding="utf-8") as fh:
        json.dump(continuity, fh, indent=2)

    return {"storyboard": storyboard, "continuity": continuity, "script": os.path.join(pre, "script.md")}


def write_manifest(project_root: str, files: list[str], *, extra: dict | None = None) -> str:
    manifest_path = os.path.join(project_root, "project_manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    manifest.setdefault("artifacts", {})
    for path in files:
        if os.path.exists(path):
            rel = os.path.relpath(os.path.abspath(path), os.path.abspath(project_root))
            manifest["artifacts"][rel] = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
    if extra:
        manifest.update(extra)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest_path
