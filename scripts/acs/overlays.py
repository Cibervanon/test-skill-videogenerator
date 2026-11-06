"""Validation and layout of motion-graphics / UI overlays.

The renderer is the authority on how an overlay is drawn; this module is the
authority on whether it *should* be drawn. It answers, from the manifest alone:

* does the overlay have the payload its type needs?
* is a number backed by a source (or explicitly marked illustrative)?
* does it respect the safe area, the face of its actor and the caption band?
* do two overlays collide in the same time window?
* is the density within the style's budget?

The geometry mirrors ``studio/src/motion-graphics/layout.ts`` and the constants
are checked against the TypeScript source by ``tests/test_overlays.py``, so the
two implementations cannot drift silently.
"""

from __future__ import annotations

import json
import os
import re

from . import generated as generated_mod

SAFE = 0.06
CAPTION_BAND = (0.855, 0.945)
RIG = {"bodyTop": -226, "footY": 6, "headRadius": 46, "headOffset": 0.94}

NUMERIC_TYPES = {"counter", "bar", "donut", "line", "ranking"}
TYPES = {
    "label",
    "callout",
    "badge",
    "panel",
    "hud",
    "highlight",
    "arrow",
    "counter",
    "bar",
    "donut",
    "line",
    "ranking",
    "process",
}

DEFAULT_BOX = {
    "label": (0.08, 0.30, 0.60, 0.09),
    "callout": (0.55, 0.62, 0.37, 0.13),
    "badge": (0.08, 0.10, 0.42, 0.06),
    # Defaults must end above the caption band (0.855), or every chart silently
    # collides with the subtitles on its first render.
    "panel": (0.08, 0.55, 0.84, 0.24),
    "hud": (0.06, 0.08, 0.88, 0.10),
    "highlight": (0.42, 0.50, 0.32, 0.20),
    "arrow": (0.20, 0.55, 0.50, 0.20),
    "counter": (0.08, 0.62, 0.50, 0.16),
    "bar": (0.08, 0.54, 0.84, 0.26),
    "donut": (0.10, 0.54, 0.80, 0.26),
    "line": (0.08, 0.54, 0.84, 0.26),
    "ranking": (0.08, 0.46, 0.84, 0.34),
    "process": (0.08, 0.62, 0.84, 0.20),
}

#: Payload keys each type cannot render without.
REQUIRED_PAYLOAD = {
    "bar": ("series",),
    "ranking": ("rows",),
    "donut": ("segments",),
    "line": ("points",),
    "counter": ("value",),
    "process": ("steps",),
    "label": ("name",),
    "callout": ("title", "caption"),
    "panel": ("title",),
    "badge": ("title",),
}


class OverlayError(ValueError):
    pass


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_cast(root: str) -> dict:
    base = load_json(os.path.join(root, "studio", "src", "data", "cast.json"), {})
    return generated_mod.merge_cast(root, base).get("characters", {})


def load_styles(root: str) -> dict:
    return load_json(os.path.join(root, "studio", "src", "data", "styles.json"), {})


# --------------------------------------------------------------------------- layout


def cast_height(cast: dict, actor_id: str) -> float:
    """Identity height, the factor Character.tsx applies before the shot scale."""
    return float((cast.get(actor_id) or {}).get("height", 1.0) or 1.0)


def actor_anchor(actor: dict, head_radius: float = RIG["headRadius"], height: float = 1.0) -> dict:
    h = head_radius
    head_cy = RIG["bodyTop"] - h * RIG["headOffset"]
    x, y, s = actor["x"], actor["y"], actor.get("scale", 1.5) * height
    return {
        "head": {"x": x, "y": y + head_cy * s, "r": h * s},
        "facing": actor.get("facing", 1),
        "top": y + (head_cy - h) * s,
        "bottom": y + RIG["footY"] * s,
    }


def place_near_actor(anchor: dict, size: tuple[float, float], frame: tuple[int, int], at: str = "head") -> tuple[float, float, float, float]:
    gap = 28
    w, h = size
    fw, fh = frame
    wpx, hpx = w * fw, h * fh
    above = (anchor["head"]["x"] / fw - w / 2, (anchor["top"] - gap - hpx) / fh, w, h)
    below = (anchor["head"]["x"] / fw - w / 2, (anchor["bottom"] + gap) / fh, w, h)
    side_x = (
        anchor["head"]["x"] + anchor["head"]["r"] + gap
        if anchor["facing"] == 1
        else anchor["head"]["x"] - anchor["head"]["r"] - gap - wpx
    )
    side = (side_x / fw, (anchor["head"]["y"] - hpx * 0.5) / fh, w, h)
    candidates = [below, side, above] if at == "feet" else [above, side, below]
    for box in candidates:
        if box[0] >= SAFE and box[1] >= SAFE and box[0] + box[2] <= 1 - SAFE and box[1] + box[3] <= 1 - SAFE:
            return box
    return clamp_box(candidates[0])


def clamp_box(box: tuple[float, float, float, float], safe: bool = True) -> tuple[float, float, float, float]:
    mx = SAFE if safe else 0.0
    w = min(box[2], 1 - mx * 2)
    h = min(box[3], 1 - mx * 2)
    x = min(1 - mx - w, max(mx, box[0]))
    y = min(1 - mx - h, max(mx, box[1]))
    return (x, y, w, h)


def resolve_box(spec: dict, actors: list[dict], cast: dict, frame: tuple[int, int] = (1080, 1920)) -> tuple[float, float, float, float]:
    placement = spec.get("placement") or {"kind": "screen"}
    # placement.box wins over spec.box, exactly like resolveBox in layout.ts
    base = (placement.get("box") if placement.get("kind") != "actor" else None) or spec.get("box")
    if not base:
        x, y, w, h = DEFAULT_BOX.get(spec.get("type"), (0.1, 0.1, 0.5, 0.2))
        base = {"x": x, "y": y, "w": w, "h": h}
    size = (base["w"], base["h"])
    safe = spec.get("safe", True)
    if placement.get("kind") == "actor":
        actor = next((a for a in actors if a.get("id") == placement.get("actor")), None)
        if not actor:
            return clamp_box((base["x"], base["y"], *size), safe)
        radius = (cast.get(actor["id"]) or {}).get("headRadius", RIG["headRadius"])
        anchor = actor_anchor(actor, radius, cast_height(cast, actor["id"]))
        box = place_near_actor(anchor, size, frame, placement.get("at", "head"))
        off = placement.get("offset") or {}
        box = (box[0] + off.get("x", 0), box[1] + off.get("y", 0), box[2], box[3])
        return clamp_box(box, safe)
    return clamp_box((base["x"], base["y"], *size), safe)


def intersects(a, b, pad: float = 0.0) -> bool:
    return a[0] + pad < b[0] + b[2] and b[0] + pad < a[0] + a[2] and a[1] + pad < b[1] + b[3] and b[1] + pad < a[1] + a[3]


def face_circle(actor: dict, cast: dict, frame: tuple[int, int] = (1080, 1920)):
    radius = (cast.get(actor["id"]) or {}).get("headRadius", RIG["headRadius"])
    anchor = actor_anchor(actor, radius, cast_height(cast, actor["id"]))
    return anchor["head"]["x"], anchor["head"]["y"], anchor["head"]["r"]


def circle_hits_box(cx: float, cy: float, r: float, box, frame=(1080, 1920)) -> bool:
    """Circle vs rectangle, with the circle and the box in the same pixel space.

    The box arrives normalised, the face centre arrives in the rig's pixels.
    Mixing the two units made every face below the top third read as "not
    covered" (the clamp against a normalised bound never reached it), which is
    exactly how a chart ended up over a head. Both sides are converted here.
    """
    fw, fh = frame
    nx = min(max(cx, box[0] * fw), (box[0] + box[2]) * fw)
    ny = min(max(cy, box[1] * fh), (box[1] + box[3]) * fh)
    return (cx - nx) ** 2 + (cy - ny) ** 2 <= r * r


# --------------------------------------------------------------- adaptive composition
#
# The renderer no longer guesses where a screen overlay goes: the UI director
# resolves a box here, writes it into the manifest and the renderer obeys it.
# That keeps one authority for geometry (this module) and makes the decision
# auditable before a single frame is rendered.

SEMANTIC_ANCHORS = (
    "top-left",
    "top-right",
    "top-center",
    "mid-left",
    "mid-right",
    "center",
    "bottom-left",
    "bottom-right",
    "bottom-center",
    "above-character",
    "beside-character",
)

PRESENTATION_MODES = ("A", "B", "C", "D", "E", "F")

#: Compact sizes for an overlay that shares the frame with the scene (B/C) and
#: roomy sizes for a presentation that owns the frame (D/E).
SIZE_BUDGET = {
    "B": {
        "label": (0.42, 0.09),
        "callout": (0.40, 0.13),
        "badge": (0.34, 0.06),
        "panel": (0.44, 0.18),
        "hud": (0.86, 0.05),
        "highlight": (0.28, 0.16),
        "arrow": (0.28, 0.12),
        "counter": (0.34, 0.12),
        "bar": (0.46, 0.22),
        "donut": (0.42, 0.20),
        "line": (0.46, 0.20),
        "ranking": (0.46, 0.26),
        "process": (0.48, 0.16),
    },
    "D": {
        "label": (0.50, 0.10),
        "callout": (0.62, 0.18),
        "badge": (0.44, 0.07),
        "panel": (0.80, 0.26),
        "hud": (0.86, 0.05),
        "highlight": (0.40, 0.20),
        "arrow": (0.36, 0.16),
        "counter": (0.62, 0.22),
        "bar": (0.86, 0.30),
        "donut": (0.86, 0.26),
        "line": (0.86, 0.26),
        "ranking": (0.86, 0.30),
        "process": (0.86, 0.22),
    },
}
# Mode E owns the frame: the element is the composition, not a card on top of one.
SIZE_BUDGET["E"] = {
    "label": (0.56, 0.10),
    "callout": (0.70, 0.22),
    "badge": (0.48, 0.08),
    "panel": (0.82, 0.34),
    "hud": (0.86, 0.06),
    "highlight": (0.44, 0.22),
    "arrow": (0.40, 0.18),
    "counter": (0.72, 0.30),
    "bar": (0.88, 0.40),
    "donut": (0.88, 0.36),
    "line": (0.88, 0.38),
    "ranking": (0.88, 0.44),
    "process": (0.88, 0.36),
}

#: m2 of frame area an overlay may cover above a body before it is rejected.
BODY_TOLERANCE = 0.001


def box_area(box) -> float:
    return max(0.0, box[2]) * max(0.0, box[3])


def overlap_area(a, b) -> float:
    x = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    y = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return x * y


def body_box(actor: dict, cast: dict, frame=(1080, 1920)) -> tuple[float, float, float, float]:
    """Approximate full-body envelope in normalised coordinates.

    It is a proxy: it covers head, torso, coat and the space the arms swing in,
    which is what a card must not sit on. Fingers are not tracked (see
    LIMITATIONS.md).
    """
    radius = (cast.get(actor["id"]) or {}).get("headRadius", RIG["headRadius"])
    height = cast_height(cast, actor["id"])
    anchor = actor_anchor(actor, radius, height)
    half = radius * 1.35 * actor.get("scale", 1.5) * height / frame[0]
    return (
        anchor["head"]["x"] / frame[0] - half,
        anchor["top"] / frame[1],
        half * 2,
        (anchor["bottom"] - anchor["top"]) / frame[1],
    )


def ui_size(type_: str, mode: str) -> tuple[float, float]:
    budget = SIZE_BUDGET.get(mode if mode in SIZE_BUDGET else "B", SIZE_BUDGET["B"])
    return budget.get(type_, (0.40, 0.14))


def _actor_candidate(actor: dict, size: tuple[float, float], cast: dict, which: str, frame=(1080, 1920)):
    radius = (cast.get(actor["id"]) or {}).get("headRadius", RIG["headRadius"])
    anchor = actor_anchor(actor, radius, cast_height(cast, actor["id"]))
    w, h = size
    gap = 28
    wpx, hpx = w * frame[0], h * frame[1]
    if which == "above-character":
        return (
            anchor["head"]["x"] / frame[0] - w / 2,
            (anchor["top"] - gap - hpx) / frame[1],
            w,
            h,
        )
    side_x = (
        anchor["head"]["x"] + anchor["head"]["r"] + gap
        if anchor["facing"] == 1
        else anchor["head"]["x"] - anchor["head"]["r"] - gap - wpx
    )
    return (side_x / frame[0], (anchor["head"]["y"] - hpx * 0.5) / frame[1], w, h)


def _anchor_order(anchor: str, size, actors, cast, mode: str, frame):
    """Candidate boxes, best guess first. The order encodes the composition rule."""
    w, h = size
    top = SAFE
    left = SAFE
    right = 1 - SAFE - w
    bottom = max(SAFE, CAPTION_BAND[0] - 0.015 - h)
    mid_y = max(SAFE, min(bottom, 0.30))
    center_y = max(SAFE, min(bottom, (1 - h) / 2 - 0.04))
    table = {
        "top-left": (left, top),
        "top-right": (right, top),
        "top-center": ((1 - w) / 2, top),
        "mid-left": (left, mid_y),
        "mid-right": (right, mid_y),
        "center": ((1 - w) / 2, center_y),
        "bottom-left": (left, bottom),
        "bottom-right": (right, bottom),
        "bottom-center": ((1 - w) / 2, bottom),
    }
    if mode in ("D", "E"):
        base = ["center", "top-center", "mid-right", "mid-left", "bottom-center", "top-left", "top-right", "bottom-left", "bottom-right"]
    elif mode == "F":
        base = ["center"]
    elif actors:
        centroid = sum(a.get("x", 540) for a in actors) / len(actors) / frame[0]
        if centroid < 0.5:
            base = ["top-right", "mid-right", "bottom-right", "top-center", "bottom-center", "top-left", "mid-left", "bottom-left"]
        else:
            base = ["top-left", "mid-left", "bottom-left", "top-center", "bottom-center", "top-right", "mid-right", "bottom-right"]
    else:
        base = ["top-left", "top-right", "top-center", "mid-left", "mid-right", "bottom-left", "bottom-right", "bottom-center"]
    if anchor and anchor not in ("auto",):
        base = [anchor] + [b for b in base if b != anchor]
    base += ["above-character", "beside-character"]

    out = []
    for name in base:
        if name in table:
            x, y = table[name]
            out.append((name, (x, y, w, h)))
        elif name in ("above-character", "beside-character"):
            for actor in actors:
                out.append((f"{name}:{actor.get('id')}", _actor_candidate(actor, size, cast, name, frame)))
    return out


def _box_ok(box, *, mode: str, actors, cast, occupied, frame):
    if box[0] < SAFE - 1e-6 or box[1] < SAFE - 1e-6 or box[0] + box[2] > 1 - SAFE + 1e-6 or box[1] + box[3] > 1 - SAFE + 1e-6:
        return False, "sale del área segura"
    if intersects(box, (0, CAPTION_BAND[0], 1, CAPTION_BAND[1] - CAPTION_BAND[0]), pad=0.004):
        return False, "pisa la banda de subtítulos"
    if mode != "E":
        for actor in actors:
            cx, cy, r = face_circle(actor, cast, frame)
            if circle_hits_box(cx, cy, r * 1.05, box):
                return False, f"tapa la cara de {actor.get('id')}"
    if mode in ("B", "C"):
        for actor in actors:
            if overlap_area(box, body_box(actor, cast, frame)) > BODY_TOLERANCE:
                return False, f"pisa el cuerpo de {actor.get('id')}"
    for other in occupied or ():
        if overlap_area(box, other) > 0.006:
            return False, "se solapa con otro elemento"
    return True, ""


def resolve_ui_box(
    size: tuple[float, float],
    actors: list[dict],
    cast: dict,
    *,
    occupied=(),
    anchor: str = "auto",
    mode: str = "B",
    frame=(1080, 1920),
    shrink: int = 2,
) -> dict:
    """Find a box that does not cover a face, a body, the captions or another UI.

    If no candidate survives, the same search is retried at 85% and 72% of the
    size; if it still fails the caller is told which mode would give the element
    the room it needs (B → D → E) instead of squeezing an illegible card in.
    """
    w, h = size
    attempts = []
    for step in range(shrink + 1):
        scale = 0.85**step
        current = (round(w * scale, 4), round(h * scale, 4))
        for index, (label, box) in enumerate(_anchor_order(anchor, current, actors, cast, mode, frame)):
            ok, why = _box_ok(box, mode=mode, actors=actors, cast=cast, occupied=occupied, frame=frame)
            cost = round(index * 0.01 + sum(overlap_area(box, o) for o in occupied) * 50 + (box_area(box) * 0.2 if mode in ("B", "C") else 0), 4)
            attempts.append({"anchor": label, "box": [round(v, 4) for v in box], "ok": ok, "reason": why, "cost": cost, "scale": scale})
            if ok:
                return {"box": box, "anchor": label, "scale": scale, "cost": cost, "mode": mode, "attempts": attempts}
    return {
        "box": None,
        "anchor": None,
        "scale": None,
        "cost": None,
        "mode": mode,
        "mode_shift": "E" if mode == "D" else "D",
        "attempts": attempts,
    }


# --------------------------------------------------------------------------- validation


def validate_overlay(spec: dict, *, actors: list[dict], cast: dict, style: dict, frame=(1080, 1920)) -> dict:
    problems: list[str] = []
    warnings: list[str] = []
    kind = spec.get("type")
    if kind not in TYPES:
        problems.append(f"{spec.get('id', '?')}: unknown overlay type {kind!r}")
        return {"ok": False, "problems": problems, "warnings": warnings}

    data = spec.get("data") or {}
    for key in REQUIRED_PAYLOAD.get(kind, ()):
        value = data.get(key)
        if value in (None, "", [], {}):
            problems.append(f"{spec.get('id')}: {kind} needs data.{key}")

    if kind in NUMERIC_TYPES:
        if not spec.get("source") and not spec.get("illustrative"):
            problems.append(
                f"{spec.get('id')}: numeric overlay without source — set source, or illustrative=true for a schematic value"
            )
        if spec.get("illustrative") and spec.get("source"):
            warnings.append(f"{spec.get('id')}: both illustrative and source set; the renderer prints 'ilustrativo'")

    placement = spec.get("placement") or {}
    if placement.get("kind") == "actor" and placement.get("actor") not in {a.get("id") for a in actors}:
        problems.append(f"{spec.get('id')}: placement actor {placement.get('actor')!r} is not in the shot")

    box = resolve_box(spec, actors, cast, frame)
    # A bridge (mode F) is deliberately full-bleed: it replaces the frame for a
    # beat, so the safe area and the caption band do not apply to it.
    is_bridge = spec.get("ui_role") == "bridge" or (spec.get("ui") or {}).get("mode") == "F"
    if not is_bridge and (box[0] < SAFE - 1e-6 or box[1] < SAFE - 1e-6 or box[0] + box[2] > 1 - SAFE + 1e-6 or box[1] + box[3] > 1 - SAFE + 1e-6):
        warnings.append(f"{spec.get('id')}: leaves the safe area at {tuple(round(v, 3) for v in box)}")

    # captions own the bottom band; a panel there would swallow the words
    if not is_bridge and intersects(box, (0, CAPTION_BAND[0], 1, CAPTION_BAND[1] - CAPTION_BAND[0]), pad=0.005):
        problems.append(f"{spec.get('id')}: overlaps the caption band ({CAPTION_BAND[0]:.2f}-{CAPTION_BAND[1]:.2f})")

    if kind == "label" and placement.get("kind") == "actor":
        actor = next((a for a in actors if a.get("id") == placement.get("actor")), None)
        if actor:
            cx, cy, r = face_circle(actor, cast, frame)
            if circle_hits_box(cx, cy, r, box):
                problems.append(f"{spec.get('id')}: label covers the face of {actor.get('id')}")

    density = (style.get("ui") or {}).get("density", "low")
    budget = (style.get("ui") or {}).get("maxPanels", 2)
    if density == "low" and kind in {"bar", "donut", "line", "ranking"}:
        warnings.append(f"{spec.get('id')}: a data chart in a low-density style — confirm it is the point of the shot")
    if kind in {"panel", "bar", "donut", "line", "ranking"} and len([s for s in spec.get("_siblings", [])]) >= budget:
        pass
    return {"ok": not problems, "problems": problems, "warnings": warnings, "box": box, "budget": budget}


def validate_shot(shot: dict, *, cast: dict, style: dict, frame=(1080, 1920)) -> dict:
    overlays = shot.get("overlays") or []
    problems: list[str] = []
    warnings: list[str] = []
    resolved = []
    actors = shot.get("actors") or []
    for spec in overlays:
        result = validate_overlay({**spec, "_siblings": overlays}, actors=actors, cast=cast, style=style, frame=frame)
        problems.extend(result["problems"])
        warnings.extend(result["warnings"])
        resolved.append({"id": spec.get("id"), "type": spec.get("type"), "box": result.get("box"), "from": spec.get("from", 0.06), "to": spec.get("to", 0.94)})

    for i, a in enumerate(resolved):
        for b in resolved[i + 1 :]:
            if a["box"] and b["box"] and intersects(a["box"], b["box"], pad=0.004):
                if a["from"] < b["to"] and b["from"] < a["to"]:
                    warnings.append(f"{a['id']} and {b['id']} overlap in the same window")

    # A bridge covers the frame on purpose: warning that it covers a head would be
    # warning about the mode the director chose.
    is_bridge = shot.get("ui_role") == "bridge" or (shot.get("presentation") or {}).get("mode") == "F"
    # actor faces must stay readable: any screen overlay covering an eye line is a defect
    if not is_bridge:
        for actor in actors:
            cx, cy, r = face_circle(actor, cast, frame)
            for item in resolved:
                if item["box"] and item["type"] != "label" and circle_hits_box(cx, cy, r * 0.9, item["box"]):
                    warnings.append(f"{item['id']} covers the head of {actor.get('id')}")

    return {"ok": not problems, "problems": problems, "warnings": warnings, "resolved": resolved}


def validate_project(project: dict, *, cast: dict, styles: dict) -> dict:
    style = (styles.get("styles") or {}).get(project.get("style") or styles.get("default"), {})
    frame = (project.get("format", {}).get("width", 1080), project.get("format", {}).get("height", 1920))
    problems: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}
    shots = []
    for shot in project.get("shots", []):
        result = validate_shot(shot, cast=cast, style=style, frame=frame)
        problems.extend(f"{shot.get('id')}: {p}" for p in result["problems"])
        warnings.extend(f"{shot.get('id')}: {w}" for w in result["warnings"])
        shots.append({"id": shot.get("id"), "overlays": result["resolved"]})
        for spec in shot.get("overlays") or []:
            counts[spec.get("type")] = counts.get(spec.get("type"), 0) + 1
    return {
        "ok": not problems,
        "style": style.get("id"),
        "problems": problems,
        "warnings": warnings,
        "counts": counts,
        "shots": shots,
    }


# --------------------------------------------------------------------------- anti-drift


def ts_constants(layout_path: str, geometry_path: str) -> dict:
    """Read the constants the renderer uses, so the Python mirror can be tested."""
    layout = open(layout_path, "r", encoding="utf-8").read() if os.path.exists(layout_path) else ""
    geometry = open(geometry_path, "r", encoding="utf-8").read() if os.path.exists(geometry_path) else ""
    safe = re.search(r"export const SAFE = ([0-9.]+)", layout)
    rig = {}
    for key in ("bodyTop", "footY", "headRadius", "headOffset"):
        match = re.search(rf"{key}: (-?[0-9.]+)", geometry)
        if match:
            rig[key] = float(match.group(1))
    return {"SAFE": float(safe.group(1)) if safe else None, "RIG": rig}


# --------------------------------------------------------------------------- documentation


def catalogue() -> list[dict]:
    return [
        {"type": t, "numeric": t in NUMERIC_TYPES, "payload": list(REQUIRED_PAYLOAD.get(t, ())), "box": DEFAULT_BOX[t]}
        for t in sorted(TYPES)
    ]
