"""Canonical character identity audit.

One question: does every shot use the same identity record for the same
character, or does a shot quietly invent a variant? This module answers that
from `cast.json` and the manifest, and it is deliberately structural: it does
not claim to see drift, it proves that no shot-level override exists.

The visual half lives in `studio/src/composition/IdentitySheet.tsx` (same rig,
seven poses) and in the rendered film; this audit is the cheap gate that runs in
the test suite.
"""

from __future__ import annotations

import os

#: A character without these cannot be rebuilt identically by the rig.
REQUIRED = (
    "id",
    "name",
    "coat",
    "coatDark",
    "hat",
    "hatBand",
    "height",
    "headRadius",
    "hatStyle",
    "hairStyle",
    "facialHair",
)

#: Identity fields a shot must never override. Pose, position, scale and facing
#: are direction; coat, head size and hat are identity.
IDENTITY_FIELDS = (
    "coat",
    "coatDark",
    "hat",
    "hatBand",
    "height",
    "headRadius",
    "hatStyle",
    "hairStyle",
    "facialHair",
    "silhouette",
    "palette",
)

#: These mirror studio/src/characters/geometry.ts. Kept here so the cheap
#: structural audit can report a proportion without importing the TSX rig.
RIG_BODY_HEIGHT_PX = 170.0  # RIG.bodyTop(-226) - RIG.hem(-56)
PROPORTION_BAND = (0.35, 0.65)



def audit(project: dict, cast: dict) -> dict:
    characters = []
    problems: list[str] = []
    warnings: list[str] = []
    ids: dict[str, str] = {}

    for key, spec in sorted((cast or {}).items()):
        missing = [field for field in REQUIRED if spec.get(field) in (None, "")]
        if missing:
            problems.append(f"character '{key}' is missing {', '.join(missing)}")
        cid = spec.get("id")
        if cid:
            if cid in ids:
                problems.append(f"duplicate canonical id '{cid}' in '{ids[cid]}' and '{key}'")
            ids[cid] = key
        height = spec.get("height", 1)
        head = spec.get("headRadius")
        if not isinstance(height, (int, float)) or not 0.75 <= float(height) <= 1.25:
            warnings.append(f"character '{key}': height {height!r} is outside the calibrated 0.75–1.25 band")
        if not isinstance(head, (int, float)) or not 24 <= float(head) <= 72:
            warnings.append(f"character '{key}': headRadius {head!r} is outside the calibrated 24–72 px band")
        head_to_body = round((2 * float(head or 0)) / RIG_BODY_HEIGHT_PX, 3)
        if not PROPORTION_BAND[0] <= head_to_body <= PROPORTION_BAND[1]:
            warnings.append(
                f"character '{key}': head/body ratio {head_to_body:.3f} is outside the calibrated "
                f"{PROPORTION_BAND[0]}–{PROPORTION_BAND[1]} band"
            )
        states = spec.get("wardrobe_states") or {}
        if not states:
            warnings.append(f"character '{key}' declares no wardrobe states")
        characters.append(
            {
                "key": key,
                "id": cid,
                "name": spec.get("name"),
                "height": height,
                "headRadius": head,
                "head_to_body": head_to_body,
                "body_height_px": RIG_BODY_HEIGHT_PX,
                "hatStyle": spec.get("hatStyle"),
                "silhouette": spec.get("silhouette"),
                "wardrobe_states": sorted(states),
            }
        )

    usage: dict[str, list[str]] = {key: [] for key in (cast or {})}
    modes: dict[str, set[str]] = {key: set() for key in (cast or {})}
    for shot in project.get("shots", []):
        mode = (shot.get("presentation") or {}).get("mode")
        for actor in shot.get("actors") or []:
            aid = actor.get("id")
            if aid not in usage:
                problems.append(f"{shot.get('id')}: actor '{aid}' has no canonical identity in cast.json")
                continue
            usage[aid].append(shot.get("id"))
            if mode:
                modes[aid].add(mode)
            overrides = [field for field in IDENTITY_FIELDS if field in actor]
            if overrides:
                problems.append(
                    f"{shot.get('id')}: actor '{aid}' overrides canonical {', '.join(overrides)} "
                    "(identity is data; pose/position/scale are direction)"
                )
            wardrobe = actor.get("wardrobe") or actor.get("wardrobe_state")
            if wardrobe and wardrobe not in ((cast.get(aid) or {}).get("wardrobe_states") or {}):
                problems.append(f"{shot.get('id')}: actor '{aid}' uses unregistered wardrobe '{wardrobe}'")

    for key in sorted(usage):
        if not usage[key]:
            warnings.append(f"character '{key}' is in the cast but never appears in this project")

    coverage = {
        key: {"shots": sorted(set(shots)), "modes": sorted(modes[key])}
        for key, shots in usage.items()
    }
    return {
        "ok": not problems,
        "characters": characters,
        "coverage": coverage,
        "problems": problems,
        "warnings": warnings,
        "method": (
            "cast.json + manifest: canonical ids, required fields, no shot-level identity overrides, "
            "registered wardrobe and a measured head/body ratio. It does not measure pixels; "
            "the identity sheet and the render do."
        ),
    }


def shot_sheet(project_dir: str, project: dict, cast: dict, out_path: str) -> str | None:
    """Crop every appearance of a recurring character into one comparison sheet.

    Uses the storyboard stills that the renderer produced, and the same rig
    geometry as the overlay solver, so the crop is the character, not a guess.
    """
    from PIL import Image, ImageDraw, ImageFont

    from . import overlays as O

    board = os.path.join(project_dir, "preproduction", "board")
    rows: dict[str, list] = {}
    for shot in project.get("shots") or []:
        # A full-bleed bridge (F) covers the cast on purpose; cropping it would
        # produce a dark rectangle and imply the character changed.
        if (shot.get("presentation") or {}).get("mode") == "F":
            continue
        still = os.path.join(board, f"{shot.get('id')}.png")
        if not os.path.exists(still):
            continue
        for actor in shot.get("actors") or []:
            aid = actor.get("id")
            if aid not in cast:
                continue
            spec = cast[aid]
            height = float(spec.get("height", 1) or 1)
            radius = float(spec.get("headRadius", 46) or 46)
            anchor = O.actor_anchor(actor, radius, height)
            s = float(actor.get("scale", 1.5)) * height
            half = max(40.0, radius * 1.7 * s)
            top = max(0, int(anchor["top"] - 24))
            bottom = min(1920, int(anchor["bottom"] + 24))
            left = max(0, int(anchor["head"]["x"] - half))
            right = min(1080, int(anchor["head"]["x"] + half))
            if right - left < 20 or bottom - top < 20:
                continue
            rows.setdefault(aid, []).append((shot.get("id"), still, (left, top, right, bottom)))

    if not rows:
        return None
    font_path = "C:/Windows/Fonts/segoeui.ttf"
    font = ImageFont.truetype(font_path, 20) if os.path.exists(font_path) else ImageFont.load_default()
    small = ImageFont.truetype(font_path, 15) if os.path.exists(font_path) else ImageFont.load_default()
    thumb_h = 300
    gap = 16
    pad = 28
    label_h = 58
    row_images = []
    for aid in sorted(rows):
        crops = []
        for shot_id, still, box in rows[aid]:
            image = Image.open(still).convert("RGB")
            # The storyboard is rendered at a fraction of 1080×1920; the rig
            # geometry is in the full stage, so both must be in the same space.
            factor = image.width / 1080.0
            scaled = tuple(max(0, min(limit, round(value * factor))) for value, limit in zip(box, (image.width, image.height, image.width, image.height)))
            crop = image.crop(scaled)
            width = max(1, round(crop.width * thumb_h / crop.height))
            crops.append((shot_id, crop.resize((width, thumb_h), Image.LANCZOS)))
        row_w = pad * 2 + sum(c.width + gap for _, c in crops) - gap
        row_h = thumb_h + label_h + gap
        canvas = Image.new("RGB", (max(900, row_w), row_h), "#0e0c16")
        draw = ImageDraw.Draw(canvas)
        draw.text((pad, 6), f"{cast[aid].get('name', aid).upper()} · {aid}", font=font, fill="#ffb15a")
        x = pad
        for shot_id, crop in crops:
            draw.text((x, label_h - 30), shot_id, font=small, fill="#cfc7db")
            canvas.paste(crop, (x, label_h))
            x += crop.width + gap
        row_images.append(canvas)
    width = max(r.width for r in row_images)
    text_h = 52
    height = text_h + sum(r.height + gap for r in row_images)
    sheet = Image.new("RGB", (width, height), "#0e0c16")
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 12), "SAME CHARACTER, DIFFERENT SHOTS · cropped from the storyboard with rig geometry", font=font, fill="#f6efe3")
    y = text_h
    for row in row_images:
        sheet.paste(row, (0, y))
        y += row.height + gap
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    sheet.save(out_path)
    return out_path


def render_markdown(report: dict) -> str:
    lines = [
        "# Character identity audit",
        "",
        f"Result: **{'OK' if report['ok'] else 'FAIL'}** · {len(report['characters'])} canonical character(s)",
        "",
        "| character | id | height | head r | head/body | hat | shots | modes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for char in report["characters"]:
        use = report["coverage"].get(char["key"], {"shots": [], "modes": []})
        shots = ", ".join(use["shots"]) or "—"
        modes = ", ".join(use["modes"]) or "—"
        lines.append(
            f"| {char['key']} | `{char['id']}` | {char['height']} | {char['headRadius']} | "
            f"{char.get('head_to_body')} | {char['hatStyle']} | {shots} | {modes} |"
        )
    lines += ["", "## Problems", ""]
    lines += [f"- {p}" for p in report["problems"]] or ["- none"]
    lines += ["", "## Warnings", ""]
    lines += [f"- {w}" for w in report["warnings"]] or ["- none"]
    lines += ["", f"> {report['method']}"]
    return "\n".join(lines) + "\n"
