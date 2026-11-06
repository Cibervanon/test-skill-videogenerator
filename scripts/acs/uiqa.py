"""UI composition QA.

The question is not "did the component render" but "was this element allowed to
be here, at this size, for this long". Every check is computed from the planned
manifest (mode + resolved box + window) and from the element's own reading time.

A full-screen composition is not a defect: the checks are evaluated *against the
declared mode*. Mode E is allowed to own the frame; mode B is not.
"""

from __future__ import annotations

from . import overlays as O
from .ui_director import reading_seconds

HEAVY = {"bar", "line", "donut", "ranking", "panel", "process"}


def _box(spec: dict, actors: list[dict], cast: dict):
    return O.resolve_box(spec, actors, cast)


def inspect_ui(project: dict, *, cast: dict, styles: dict) -> dict:
    style = (styles.get("styles") or {}).get(project.get("style") or styles.get("default"), {})
    budget = int((style.get("ui") or {}).get("maxPanels", 2))
    problems: list[str] = []
    warnings: list[str] = []
    shots: list[dict] = []
    modes: dict[str, int] = {}
    totals = {"overlays": 0, "problems": 0, "warnings": 0}
    previous: tuple | None = None

    for shot in project.get("shots", []):
        actors = shot.get("actors") or []
        overlays = shot.get("overlays") or []
        presentation = shot.get("presentation") or {}
        mode = presentation.get("mode") or ("A" if not overlays else "B")
        intent = shot.get("intent") or ""
        seconds = float(shot.get("seconds", 4.0))
        modes[mode] = modes.get(mode, 0) + 1
        flags: list[str] = []

        if mode not in O.PRESENTATION_MODES:
            problems.append(f"{shot.get('id')}: modo de presentación desconocido {mode!r}")
            flags.append("modo desconocido")
        if mode == "A" and overlays:
            problems.append(f"{shot.get('id')}: modo A (escena sola) con {len(overlays)} elemento(s) de UI")
            flags.append("modo A con UI")
        if mode != "A" and not overlays:
            problems.append(f"{shot.get('id')}: modo {mode} sin ningún elemento de UI")
            flags.append(f"modo {mode} vacío")
        if mode == "D" and not presentation.get("scrim"):
            problems.append(f"{shot.get('id')}: modo D sin atenuación de la escena (scrim)")
            flags.append("D sin scrim")
        if mode == "E" and not presentation.get("independent"):
            problems.append(f"{shot.get('id')}: modo E sin marcar composición independiente")
            flags.append("E sin declarar")
        if mode == "F" and not presentation.get("bridge"):
            problems.append(f"{shot.get('id')}: modo F sin marcar puente")
            flags.append("F sin declarar")
        if intent in ("accion", "emocion") and mode in ("D", "E"):
            problems.append(f"{shot.get('id')}: un plano de {intent} no debería sustituir la escena (modo {mode})")
            flags.append("modo contra la intención")
        if intent in ("accion", "emocion") and any(o.get("type") in HEAVY for o in overlays):
            problems.append(f"{shot.get('id')}: gráfico pesado sobre una {intent}")
            flags.append("gráfico sobre acción")
        if mode in ("B", "C") and len(overlays) > budget:
            warnings.append(f"{shot.get('id')}: {len(overlays)} elementos con un presupuesto de {budget}")
        if mode in ("D", "E") and len(overlays) > 1:
            warnings.append(f"{shot.get('id')}: {len(overlays)} elementos comparten una composición de foco")

        resolved = []
        for spec in overlays:
            spec_id = spec.get("id")
            totals["overlays"] += 1
            box = _box(spec, actors, cast)
            entry = {
                "id": spec_id,
                "type": spec.get("type"),
                "box": [round(v, 4) for v in box],
                "from": spec.get("from"),
                "to": spec.get("to"),
            }
            # Mode F is a full-bleed bridge: covering the captions and leaving
            # the safe area is the design, not a defect.
            if mode != "F" and (
                box[0] < O.SAFE - 1e-6 or box[1] < O.SAFE - 1e-6 or box[0] + box[2] > 1 - O.SAFE + 1e-6 or box[1] + box[3] > 1 - O.SAFE + 1e-6
            ):
                problems.append(f"{shot.get('id')}/{spec_id}: sale del área segura")
                entry["flags"] = entry.get("flags", []) + ["fuera del área segura"]
            if mode != "F" and O.intersects(box, (0, O.CAPTION_BAND[0], 1, O.CAPTION_BAND[1] - O.CAPTION_BAND[0]), pad=0.004):
                problems.append(f"{shot.get('id')}/{spec_id}: pisa la banda de subtítulos")
                entry["flags"] = entry.get("flags", []) + ["subtítulos"]
            # E has no cast on screen; F is a full-bleed bridge that covers the
            # shot for a beat, so neither can "cover a face" in a meaningful way.
            if mode not in ("E", "F"):
                for actor in actors:
                    cx, cy, radius = O.face_circle(actor, cast)
                    if O.circle_hits_box(cx, cy, radius, box):
                        problems.append(f"{shot.get('id')}/{spec_id}: tapa la cara de {actor.get('id')}")
                        entry["flags"] = entry.get("flags", []) + [f"cara:{actor.get('id')}"]
            if mode in ("B", "C"):
                for actor in actors:
                    cover = O.overlap_area(box, O.body_box(actor, cast))
                    if cover > O.BODY_TOLERANCE:
                        problems.append(f"{shot.get('id')}/{spec_id}: cubre un {cover:.1%} del cuerpo de {actor.get('id')}")
                        entry["flags"] = entry.get("flags", []) + [f"cuerpo:{actor.get('id')}"]

            start = float(spec.get("from", 0.06))
            end = float(spec.get("to", 0.94))
            window = round((end - start) * seconds, 2)
            reading = reading_seconds(spec)
            entry.update({"window_seconds": window, "reading_seconds": reading})
            if window < reading - 0.15:
                problems.append(f"{shot.get('id')}/{spec_id}: dura {window:.1f}s y necesita {reading:.1f}s de lectura")
                entry["flags"] = entry.get("flags", []) + ["demasiado breve"]
            if mode in ("B", "C") and end > 0.901:
                problems.append(f"{shot.get('id')}/{spec_id}: la UI sigue hasta {end:.2f} del plano; debe retirarse antes")
                entry["flags"] = entry.get("flags", []) + ["no se retira"]
            if mode == "F" and end < 0.98:
                problems.append(f"{shot.get('id')}/{spec_id}: el puente termina en {end:.2f} y no llega al corte")
                entry["flags"] = entry.get("flags", []) + ["puente corto"]
            if spec.get("type") in O.NUMERIC_TYPES and not spec.get("source") and not spec.get("illustrative"):
                problems.append(f"{shot.get('id')}/{spec_id}: cifra sin fuente ni marca de ilustrativo")
                entry["flags"] = entry.get("flags", []) + ["sin procedencia"]
            if not (spec.get("ui") or {}).get("reason"):
                warnings.append(f"{shot.get('id')}/{spec_id}: sin motivo narrativo registrado")
            resolved.append(entry)

        for i, a in enumerate(resolved):
            for b in resolved[i + 1 :]:
                if O.intersects(a["box"], b["box"], pad=0.004) and a["from"] < b["to"] and b["from"] < a["to"]:
                    problems.append(f"{shot.get('id')}: {a['id']} y {b['id']} se solapan")
                    flags.append("solape")
        for actor in actors:
            body = O.body_box(actor, cast)
            covered = sum(O.overlap_area(item["box"], body) for item in resolved)
            if mode in ("B", "C") and covered > O.BODY_TOLERANCE:
                problems.append(f"{shot.get('id')}: la UI ocupa {covered:.1%} del cuerpo de {actor.get('id')}")
                flags.append("oclusión")

        key = tuple((o["type"], (o.get("ui") or {}).get("intent")) for o in overlays)
        if previous and key and key == previous:
            warnings.append(f"{shot.get('id')}: repite el mismo tipo de UI que el plano anterior")
        previous = key or previous

        shots.append(
            {
                "shot": shot.get("id"),
                "mode": mode,
                "mode_reason": presentation.get("reason", ""),
                "intent": intent,
                "overlays": resolved,
                "flags": flags,
                "status": "reviewed" if flags else "clean",
            }
        )

    totals["problems"] = len(problems)
    totals["warnings"] = len(warnings)
    return {
        "ok": not problems,
        "modes": modes,
        "totals": totals,
        "shots": shots,
        "problems": problems,
        "warnings": warnings,
        "method": "geometría resuelta + ventanas del manifiesto; la lectura se estima por palabras del propio elemento",
        "limits": [
            "la caja del cuerpo es un sobre aproximado (cabeza, torso, abrigo, arco de brazos): no rastrea dedos",
            "no hay OCR ni comprensión semántica: el motivo narrativo se audita contra el campo `intent` declarado",
            "el tiempo de lectura es una estimación de 3.3 palabras/s, no una medición ocular",
        ],
    }


def measure_render(*, video: str, project: dict, project_dir: str, ffmpeg: str = "ffmpeg") -> dict:
    """Sample the real render and measure what the mode switch did to pixels.

    Geometry already proves *where* the box is; this answers whether the render
    actually behaved that way: text contrast inside the box, and how much scene
    detail survives behind it. A B shot should still show a set; an E or F frame
    is a graphic plate and must read as one.
    """
    import os
    import subprocess

    from PIL import Image, ImageFilter, ImageStat

    from .storyboard import key_frames

    if not os.path.exists(video):
        return {"status": "missing", "video": video}
    out_dir = os.path.join(project_dir, "quality", "ui_frames")
    os.makedirs(out_dir, exist_ok=True)
    fps = project["format"]["fps"]
    rows = []
    for key in key_frames(project):
        shot = next((s for s in project["shots"] if s["id"] == key["id"]), None)
        if not shot:
            continue
        mode = (shot.get("presentation") or {}).get("mode", "A")
        overlay = (shot.get("overlays") or [None])[0]
        window = ((overlay or {}).get("from", 0.06), (overlay or {}).get("to", 0.94))
        # Sample the middle of the element's own window, not the storyboard frame:
        # a bridge card that starts at 0.45 is still fading in at 0.55 and would be
        # measured (and judged) half transparent.
        sample = round((window[0] + window[1]) / 2, 3) if overlay else 0.55
        seconds = (key["from"] + key["frames"] * min(sample, 0.98)) / fps
        path = os.path.join(out_dir, f"{key['id']}.png")
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{seconds:.3f}", "-i", video, "-frames:v", "1", "-y", path],
            check=True,
        )
        image = Image.open(path).convert("L")
        width, height = image.size
        edges = round(ImageStat.Stat(image.filter(ImageFilter.FIND_EDGES)).mean[0], 2)
        placement = (overlay or {}).get("placement") or {}
        # Actor-bound labels are laid out by the renderer from the rig, not from a
        # declared box; inventing one here would report a number that was never
        # measured. Contrast stays null and the row says why.
        box = placement.get("box") if placement.get("kind") == "screen" else None
        ui_note = None if box else ("etiqueta anclada al actor: sin caja declarada" if overlay else "plano sin UI")
        ui = None
        if box:
            crop = image.crop(
                (
                    int(box["x"] * width),
                    int(box["y"] * height),
                    int((box["x"] + box["w"]) * width),
                    int((box["y"] + box["h"]) * height),
                )
            )
            values = sorted(crop.getdata())
            contrast = values[int(len(values) * 0.95)] - values[int(len(values) * 0.05)] if values else 0
            ui = {"std": round(ImageStat.Stat(crop).stddev[0], 2), "contrast": int(contrast)}
        rows.append(
            {
                "shot": key["id"],
                "mode": mode,
                "seconds": round(seconds, 2),
                "sample": sample,
                "frame": os.path.relpath(path, project_dir).replace(os.sep, "/"),
                "scene_edges": edges,
                "ui": ui,
                "ui_note": ui_note,
            }
        )

    by_mode: dict[str, dict] = {}
    for row in rows:
        bucket = by_mode.setdefault(row["mode"], {"shots": 0, "scene_edges": 0.0, "ui_contrast": 0.0, "ui_shots": 0})
        bucket["shots"] += 1
        bucket["scene_edges"] += row["scene_edges"]
        if row["ui"]:
            bucket["ui_contrast"] += row["ui"]["contrast"]
            bucket["ui_shots"] += 1
    for bucket in by_mode.values():
        bucket["scene_edges"] = round(bucket["scene_edges"] / max(1, bucket["shots"]), 2)
        bucket["ui_contrast"] = round(bucket["ui_contrast"] / bucket["ui_shots"], 1) if bucket["ui_shots"] else None
    return {
        "status": "measured",
        "video": os.path.abspath(video),
        "frames": rows,
        "by_mode": by_mode,
        "note": (
            "scene_edges es energía de bordes del frame completo; ui_contrast es el rango p95-p5 dentro de la caja, "
            "medido en el centro de la ventana del elemento. Confirma que B/C conservan escena y que E/F son placas "
            "gráficas; no puntúa gusto. Las etiquetas ancladas al actor no tienen caja declarada y no se miden."
        ),
    }


def to_markdown(report: dict) -> str:
    lines = [
        "## UI",
        "",
        f"Resultado: **{'OK' if report.get('ok') else 'FAIL'}** · {report['totals']['overlays']} elemento(s) · "
        f"{report['totals']['problems']} problema(s) · {report['totals']['warnings']} aviso(s)",
        "",
        "| plano | modo | intención | UI | ventana / lectura | estado |",
        "|---|---|---|---|---|---|",
    ]
    for shot in report.get("shots", []):
        ui = ", ".join(f"{o['id']}·{o['type']}" for o in shot["overlays"]) or "—"
        timing = ", ".join(f"{o['window_seconds']}s/{o['reading_seconds']}s" for o in shot["overlays"]) or "—"
        state = "⚠ " + "; ".join(shot["flags"]) if shot["flags"] else "clean"
        lines.append(f"| {shot['shot']} | **{shot['mode']}** | {shot.get('intent') or '—'} | {ui} | {timing} | {state} |")
    lines += ["", "### Problemas", ""]
    lines += [f"- ❌ {p}" for p in report.get("problems", [])] or ["- ninguno"]
    if report.get("warnings"):
        lines += ["", "### Avisos", ""] + [f"- ⚠ {w}" for w in report["warnings"]]
    render = report.get("render") or {}
    if render.get("status") == "measured":
        lines += ["", "### Evidencia del render", "", "| modo | planos | detalle de escena | contraste de UI |", "|---|---|---|---|"]
        for mode, bucket in sorted(render.get("by_mode", {}).items()):
            contrast = bucket["ui_contrast"] if bucket["ui_contrast"] is not None else "—"
            lines.append(f"| {mode} | {bucket['shots']} | {bucket['scene_edges']} | {contrast} |")
        lines += ["", f"> {render.get('note', '')}"]
    lines += ["", "### Límites", ""] + [f"- {item}" for item in report.get("limits", [])]
    return "\n".join(lines)
