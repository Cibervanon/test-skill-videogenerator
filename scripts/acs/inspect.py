"""Visual inspection of renders.

Two kinds of evidence, kept separate on purpose:

* **pixels** — measured on a still or a video frame (empty scene, edge energy,
  caption contrast, palette drift, depth bands);
* **geometry** — computed from the manifest (overlay collisions, face coverage,
  caption band, safe area), because the composition already knows where every
  element is.

Neither is an aesthetic judgement. Aesthetic review stays in
``preproduction/visual_review.json`` and is reported as *pending* until a human
writes it. The inspector never converts a metric into a score of quality.
"""

from __future__ import annotations

import json
import os

from PIL import Image, ImageFilter, ImageStat

from . import overlays as overlays_mod
from . import uiqa as uiqa_mod

CHECK_KIND = {
    "empty_ratio": "automatic (pixels)",
    "edge_density": "automatic (pixels)",
    "subject_score": "automatic (pixels)",
    "caption_contrast": "automatic (pixels)",
    "palette_shift": "automatic (pixels)",
    "depth_bands": "automatic (pixels)",
    "overlays": "geometry (manifest)",
    "ui": "geometry + timing (manifest)",
    "cuts": "automatic (video)",
}

THRESHOLDS = {
    "empty_ratio_max": 0.62,
    "caption_spread_min": 70.0,
    "caption_edge_min": 5.0,
    "subject_score_min": 1.55,
    "palette_shift_max": 0.30,
    "depth_bands_min": 2,
    "cut_sync_tolerance_s": 0.35,
}


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_style(root: str, style_id: str | None) -> dict:
    data = load_json(os.path.join(root, "studio", "src", "data", "styles.json"), {}) or {}
    styles = data.get("styles", {})
    return styles.get(style_id or data.get("default", "cinematic"), styles.get("cinematic", {}))


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    value = value.strip()
    if not value.startswith("#") or len(value) not in (4, 7):
        return None
    if len(value) == 4:
        value = "#" + "".join(c * 2 for c in value[1:])
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def _palette_rgb(style: dict) -> list[tuple[int, int, int]]:
    out = []
    for value in (style.get("palette") or {}).values():
        rgb = _hex_to_rgb(value) if isinstance(value, str) else None
        if rgb:
            out.append(rgb)
    return out


def _tile_stats(gray: Image.Image, cols: int = 12, rows: int = 21) -> list[dict]:
    width, height = gray.size
    tw, th = max(1, width // cols), max(1, height // rows)
    out = []
    for r in range(rows):
        for c in range(cols):
            tile = gray.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))
            stat = ImageStat.Stat(tile)
            out.append(
                {
                    "row": r,
                    "col": c,
                    "std": round(stat.stddev[0], 2),
                    "mean": round(stat.mean[0], 2),
                    "edges": round(ImageStat.Stat(tile.filter(ImageFilter.FIND_EDGES)).mean[0], 2),
                }
            )
    return out


def frame_metrics(path: str, style: dict) -> dict:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_mean = round(ImageStat.Stat(edges).mean[0], 2)

    tiles = _tile_stats(gray)
    empty = [t for t in tiles if t["std"] < 6.0]
    tile_edges = sorted(t["edges"] for t in tiles)
    median_edges = tile_edges[len(tile_edges) // 2] if tile_edges else 0.0
    peak_edges = tile_edges[-1] if tile_edges else 0.0
    subject_score = round(peak_edges / max(1.0, median_edges), 3)

    # Caption legibility is *local*: a 3-word line covers one small cell, so a
    # whole-band percentile reads the background and calls a legible caption
    # flat. Split the band into cells and keep the densest one; that cell is
    # where the words are, and its internal spread is the real contrast.
    band = gray.crop((0, int(height * 0.855), width, int(height * 0.945)))
    band_edges = round(ImageStat.Stat(band.filter(ImageFilter.FIND_EDGES)).mean[0], 2)
    bw, bh = band.size
    cols, rows = 12, 4
    cw, ch = max(1, bw // cols), max(1, bh // rows)
    spread = 0.0
    for r in range(rows):
        for c in range(cols):
            cell = sorted(band.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)).getdata())
            if not cell:
                continue
            local = cell[int(len(cell) * 0.95)] - cell[int(len(cell) * 0.05)]
            spread = max(spread, local)
    spread = round(float(spread), 2)

    # palette drift: dominant colours of the render against the style palette
    quant = image.resize((160, 284)).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    palette = quant.getpalette() or []
    counts = sorted(quant.getcolors() or [], reverse=True)[:6]
    palette_rgb = _palette_rgb(style)
    shifts = []
    for count, index in counts:
        r, g, b = palette[index * 3 : index * 3 + 3]
        if not palette_rgb:
            continue
        distance = min(((r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2) ** 0.5 for pr, pg, pb in palette_rgb)
        shifts.append((distance / 441.0, count))
    total = sum(c for _, c in shifts) or 1
    palette_shift = round(sum(d * c for d, c in shifts) / total, 3)

    rows = [tiles[r * 12 : (r + 1) * 12] for r in range(21)]
    thirds = [[tile for row in rows[a:b] for tile in row] for a, b in ((0, 7), (7, 14), (14, 21))]
    bands = [round(sum(t["edges"] for t in third) / len(third), 2) for third in thirds]
    depth_bands = sum(1 for value in bands if value > 2.0)

    return {
        "path": os.path.abspath(path),
        "size": {"width": width, "height": height},
        "empty_ratio": round(len(empty) / len(tiles), 3),
        "edge_density": edge_mean,
        "subject_score": subject_score,
        "caption_contrast": {"spread": spread, "edges": band_edges},
        "palette_shift": palette_shift,
        "depth_bands": depth_bands,
        "depth_profile": bands,
    }


def flags_for(metrics: dict, th: dict | None = None, mode: str | None = None) -> list[str]:
    th = {**THRESHOLDS, **(th or {})}
    flags = []
    # A night sky is legitimately flat: emptiness needs *both* many flat tiles
    # and no detail anywhere, otherwise every dark scene reads as a defect.
    empty = metrics["empty_ratio"] > th["empty_ratio_max"] or (
        metrics["empty_ratio"] > 0.50 and metrics["edge_density"] < 5.0
    )
    # Modes E and F are graphic compositions on purpose: a flat plate is the
    # design, so "empty scene" would be a false positive there.
    if mode in ("E", "F"):
        empty = False
    if empty:
        flags.append(f"escena vacía: {metrics['empty_ratio']:.0%} de teselas planas, detalle {metrics['edge_density']:.1f}")
    if metrics["subject_score"] < th["subject_score_min"]:
        flags.append(f"poco sujeto: contraste de detalle {metrics['subject_score']:.2f}")
    contrast = metrics["caption_contrast"]
    if metrics.get("has_captions") and (contrast["spread"] < th["caption_spread_min"] or contrast["edges"] < th["caption_edge_min"]):
        flags.append(f"texto de riesgo: spread {contrast['spread']}, bordes {contrast['edges']}")
    if metrics["palette_shift"] > th["palette_shift_max"]:
        flags.append(f"deriva de paleta: {metrics['palette_shift']:.2f} respecto al estilo")
    if metrics["depth_bands"] < th["depth_bands_min"]:
        flags.append(f"poca profundidad: {metrics['depth_bands']}/3 bandas con detalle")
    return flags


def inspect_stills(project_dir: str, project: dict, *, root: str, board_dir: str | None = None, video: str | None = None) -> dict:
    style = load_style(root, project.get("style"))
    board = board_dir or os.path.join(project_dir, "preproduction", "board")
    fps = project.get("format", {}).get("fps", 30)
    cursor = 0
    shots = []
    problems = []
    for shot in project.get("shots", []):
        still = os.path.join(board, f"{shot['id']}.png")
        entry = {
            "shot": shot["id"],
            "scene": shot.get("scene"),
            "mode": (shot.get("presentation") or {}).get("mode"),
            "line": shot.get("line", ""),
            "still": os.path.relpath(still, root).replace(os.sep, "/") if os.path.exists(still) else None,
        }
        if not os.path.exists(still):
            entry["status"] = "missing still"
            problems.append(f"{shot['id']}: no still at {still}")
            shots.append(entry)
        else:
            metrics = frame_metrics(still, style)
            metrics["has_captions"] = bool(str(shot.get("line", "")).strip())
            entry.update(metrics)
            entry["flags"] = flags_for(metrics, mode=entry["mode"])
            entry["status"] = "reviewed (pixels)" if entry["flags"] else "clean (pixels)"
            shots.append(entry)
        cursor += round(float(shot.get("seconds", 0)) * fps) - int(shot.get("transitionIn", project.get("transitionFrames", 0)))
    del cursor

    styles = load_json(os.path.join(root, "studio", "src", "data", "styles.json"), {})
    cast = overlays_mod.load_cast(root)
    geometry = overlays_mod.validate_project(project, cast=cast, styles=styles)
    ui = uiqa_mod.inspect_ui(project, cast=cast, styles=styles)
    if video and os.path.exists(video):
        ffmpeg = "ffmpeg"
        try:
            from .ffmpeg import Tools

            ffmpeg = Tools.detect().ffmpeg
        except Exception:  # inspection must still run without ffmpeg on PATH
            pass
        ui["render"] = uiqa_mod.measure_render(video=video, project=project, project_dir=project_dir, ffmpeg=ffmpeg)
    review_path = os.path.join(project_dir, "preproduction", "visual_review.json")
    review = load_json(review_path, {}) or {}
    reported = {
        "style": style.get("id"),
        "shots": shots,
        "overlays": geometry,
        "ui": ui,
        "aesthetic_review": {
            "status": "pending" if not review else "provided",
            "source": os.path.relpath(review_path, root).replace(os.sep, "/"),
            "note": "composition/acting/storytelling are not measurable by this tool",
        },
        "method": {
            "pixels": "PIL on the storyboard stills (downscaled tiles, luma, edge energy, quantised palette)",
            "geometry": "overlay boxes resolved from the manifest with the renderer's own constants",
            "limitations": "no semantic understanding, no OCR, no judgement of taste",
        },
        "problems": problems,
        "kind_map": CHECK_KIND,
        "thresholds": THRESHOLDS,
    }
    return reported


def render_markdown(report: dict) -> str:
    lines = [
        "# Visual inspection",
        "",
        f"Style: **{report.get('style')}** · method: pixels + manifest geometry",
        "",
        "| shot | vacío | sujeto | texto | paleta | profundidad | estado |",
        "|---|---|---|---|---|---|---|",
    ]
    for shot in report["shots"]:
        if shot.get("status") == "missing still":
            lines.append(f"| {shot['shot']} | — | — | — | — | — | missing still |")
            continue
        contrast = shot["caption_contrast"]
        lines.append(
            f"| {shot['shot']} | {shot['empty_ratio']:.0%} | {shot['subject_score']:.2f} | {contrast['spread']:.0f}/{contrast['edges']:.0f} | "
            f"{shot['palette_shift']:.2f} | {shot['depth_bands']}/3 | {'⚠ ' + '; '.join(shot['flags']) if shot['flags'] else 'clean'} |"
        )
    lines += ["", "## Overlays", ""]
    geo = report.get("overlays", {})
    lines.append(f"Validación: **{'OK' if geo.get('ok') else 'FAIL'}** — {sum(geo.get('counts', {}).values())} overlays")
    for problem in geo.get("problems", []):
        lines.append(f"- ❌ {problem}")
    for warning in geo.get("warnings", []):
        lines.append(f"- ⚠ {warning}")
    lines += ["", uiqa_mod.to_markdown(report.get("ui", {}))]
    lines += [
        "",
        "## Lo que esta inspección no mide",
        "",
        "- Actuación, narrativa, ritmo y gusto: quedan **pendientes** de revisión humana.",
        "- No hay OCR: el contraste de texto se mide en la banda de subtítulos, no se lee el texto.",
        "- La profundidad es un proxy de energía de bordes por tercios, no un mapa de profundidad.",
        "",
    ]
    return "\n".join(lines)


def write_report(project_dir: str, report: dict) -> dict:
    quality = os.path.join(project_dir, "quality")
    os.makedirs(quality, exist_ok=True)
    json_path = os.path.join(quality, "visual_inspection.json")
    md_path = os.path.join(quality, "visual_inspection.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(report))
    return {"json": json_path, "markdown": md_path}
