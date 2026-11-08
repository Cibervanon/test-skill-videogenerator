"""Storyboard stage: one still per shot, then a captioned contact sheet.

The external repository's best process idea, ported: look at a still of every
shot *before* paying for the animation. A still costs seconds; a render costs
tens of minutes.

    python scripts/studio.py storyboard --project projects/demo_002

Writes ``preproduction/board/<shot>.png`` and ``preproduction/storyboard.jpg``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def key_frames(project: dict) -> list[dict]:
    """The frame each shot is judged at: the midpoint of its visible span.

    The midpoint is used instead of 55% because a 55% sample can land in the
    gap after a shot's last caption, which makes the legibility check measure a
    blank band rather than the subtitle it is supposed to judge.
    """
    fps = project["format"]["fps"]
    default = project.get("transitionFrames", 0)
    shots = project["shots"]
    cursor = 0
    out = []
    for i, shot in enumerate(shots):
        frames = round(shot["seconds"] * fps)
        nxt = shots[i + 1].get("transitionIn", default) if i + 1 < len(shots) else 0
        out.append(
            {
                "id": shot["id"],
                "scene": shot.get("scene", ""),
                "from": cursor,
                "frames": frames,
                "frame": cursor + int(frames * 0.50),
                "line": shot.get("line", ""),
                "note": shot.get("note", ""),
            }
        )
        cursor += frames - nxt
    return out


def _font(size: int, bold: bool = True):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_stills(studio: str, board_dir: str, project: dict, *, scale: float = 0.45) -> list[dict]:
    frames = key_frames(project)
    spec_path = os.path.join(board_dir, "_frames.json")
    os.makedirs(board_dir, exist_ok=True)
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"entry": "src/index.ts", "composition": "CinematicDemo", "frames": frames},
            fh,
            indent=2,
        )
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storyboard.mjs")
    result = subprocess.run(
        ["node", script, os.path.abspath(spec_path), os.path.abspath(board_dir), "--scale", str(scale)],
        cwd=studio,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"storyboard stills failed:\n{result.stdout}\n{result.stderr}")
    return frames


def build_sheet(board_dir: str, frames: list[dict], out_path: str, *, title: str = "", cols: int = 3) -> dict:
    head, body, note = _font(34), _font(26), _font(21, False)
    cell_w, cell_h, cap = 520, 924, 150
    pad = 22
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * pad, rows * (cell_h + cap + pad) + pad + 80), (18, 15, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 24), f"{title}  ·  storyboard, one key frame per shot", font=head, fill=(246, 239, 227))

    for i, shot in enumerate(frames):
        x = pad + (i % cols) * (cell_w + pad)
        y = 80 + pad + (i // cols) * (cell_h + cap + pad)
        still = os.path.join(board_dir, f"{shot['id']}.png")
        if os.path.exists(still):
            image = Image.open(still).convert("RGB")
            image.thumbnail((cell_w, cell_h))
            sheet.paste(image, (x + (cell_w - image.width) // 2, y))
        else:
            draw.rectangle([x, y, x + cell_w, y + cell_h], fill=(58, 28, 38))
            draw.text((x + 20, y + 20), f"missing {shot['id']}.png", font=body, fill=(255, 120, 120))
        draw.rectangle([x, y + cell_h, x + cell_w, y + cell_h + cap], fill=(30, 25, 38))
        draw.text((x + 16, y + cell_h + 10), f"{i + 1}  {shot['id']}  {shot['scene']}", font=head, fill=(255, 177, 90))
        t = f"{shot['from'] / 30:.1f} s"
        draw.text((x + cell_w - 16 - draw.textlength(t, font=note), y + cell_h + 18), t, font=note, fill=(170, 160, 185))
        line = f"\"{shot['line']}\"" if shot.get("line") else "(no words)"
        draw.text((x + 16, y + cell_h + 56), line[:64], font=body, fill=(246, 239, 227))
        if shot.get("note"):
            draw.text((x + 16, y + cell_h + 100), shot["note"][:74], font=note, fill=(170, 160, 185))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    sheet.save(out_path, quality=88)
    return {"sheet": out_path, "size": sheet.size, "shots": len(frames), "columns": cols}


def build(project_dir: str, project: dict, *, studio: str, scale: float = 0.45) -> dict:
    board_dir = os.path.join(project_dir, "preproduction", "board")
    frames = render_stills(studio, board_dir, project, scale=scale)
    result = build_sheet(
        board_dir,
        frames,
        os.path.join(project_dir, "preproduction", "storyboard.jpg"),
        title=project.get("title", project.get("id", "")),
    )
    with open(os.path.join(project_dir, "preproduction", "storyboard_frames.json"), "w", encoding="utf-8") as fh:
        json.dump(frames, fh, indent=2)
    return {**result, "frames": frames}


if __name__ == "__main__":  # manual use
    print("Use: python scripts/studio.py storyboard --project <dir>", file=sys.stderr)
    raise SystemExit(2)
