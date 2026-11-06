"""Local, deterministic asset forge.

A prompt is parsed into an asset intent, the intent is built from local SVG
primitives, the result gets a preview, a version directory and a registry entry,
and its active render data is written for Remotion.  No network, no model
credits, no second catalog and no second renderer.

The forge deliberately supports a small, explicit primitive vocabulary.  That is
what makes a forged asset *renderable* rather than just a file on disk.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone

from . import generated as generated_mod
from . import references as references_mod

PREFIX = {
    "set": "set",
    "character": "character",
    "expression": "expression",
    "prop": "prop",
    "motion_graphic": "graphic",
    "ui": "ui",
}

STYLE = "cinematic"
LICENSE = "CC0-1.0"
AUTHOR = "asset_forge / local deterministic primitives"
SOURCE = "generated locally from a prompt; no external model, image or asset was used"
EXPRESSION_WORDS = {
    "sorpresa": "surprise",
    "sorprendido": "surprise",
    "sorprendida": "surprise",
    "miedo": "fear",
    "asustado": "fear",
    "asustada": "fear",
    "enfado": "anger",
    "enfadado": "anger",
    "ira": "anger",
    "triste": "sadness",
    "tristeza": "sadness",
    "alegria": "joy",
    "feliz": "joy",
}
EXPRESSION_VALUES = {
    "surprise": {"brow": 0.45, "mouth": 0.92, "headTilt": -4.0, "yaw": 0.0, "blink": 0.0},
    "fear": {"brow": -0.85, "mouth": 0.42, "headTilt": 5.0, "yaw": -0.22, "blink": 0.15},
    "anger": {"brow": 0.95, "mouth": 0.28, "headTilt": 1.0, "yaw": 0.0, "blink": 0.0},
    "sadness": {"brow": -0.9, "mouth": 0.0, "headTilt": 7.0, "yaw": -0.12, "blink": 0.35},
    "joy": {"brow": -0.15, "mouth": 0.88, "headTilt": -2.0, "yaw": 0.0, "blink": 0.0},
}
PALETTES = {
    "night": {
        "base": "#0b0f18",
        "wall": "#1c2a3d",
        "wallDark": "#111a28",
        "floor": "#151b24",
        "accent": "#69d5cf",
        "warm": "#ffb45c",
        "paper": "#dce8eb",
        "ink": "#070a10",
        "sky": "#0a1222",
    },
    "day": {
        "base": "#dfe7e3",
        "wall": "#b9c8c6",
        "wallDark": "#819795",
        "floor": "#8a8174",
        "accent": "#258f8a",
        "warm": "#e9a44f",
        "paper": "#f6f2e7",
        "ink": "#182024",
        "sky": "#b9d9e8",
    },
    "warm": {
        "base": "#211611",
        "wall": "#5a3529",
        "wallDark": "#2d1b17",
        "floor": "#2a1c17",
        "accent": "#f0b45c",
        "warm": "#ffcf82",
        "paper": "#f2dfc4",
        "ink": "#120a08",
        "sky": "#3c241e",
    },
}


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str) -> str:
    text = text.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    text = text.replace("ñ", "n")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("-", "_").split("_") if part)


def _rect(x, y, w, h, fill, **kw):
    return {"kind": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, **kw}


def _circle(cx, cy, r, fill, **kw):
    return {"kind": "circle", "cx": cx, "cy": cy, "r": r, "fill": fill, **kw}


def _ellipse(cx, cy, rx, ry, fill, **kw):
    return {"kind": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry, "fill": fill, **kw}


def _path(d, fill="none", **kw):
    return {"kind": "path", "d": d, "fill": fill, **kw}


def _polygon(points, fill, **kw):
    return {"kind": "polygon", "points": points, "fill": fill, **kw}


def _line(x1, y1, x2, y2, stroke, **kw):
    return {"kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke, **kw}


def _layer(layer_id: str, depth: float, elements: list[dict], **kw):
    return {"id": layer_id, "depth": depth, "elements": elements, **kw}


def _set_spec(subject: str, palette: dict, *, night: bool, detail: str = "medium") -> dict:
    """A recurring laboratory/workshop set built from coordinated layers.

    The same element coordinates are used by the night variation: only palette,
    lighting and atmosphere change, so the location keeps its identity.
    """
    p = palette
    gradients = [
        {"id": "wallwash", "x1": 0, "y1": 0, "x2": 0, "y2": 1, "stops": [[0, p["wall"]], [1, p["wallDark"]]]},
        {"id": "floorwash", "x1": 0, "y1": 0, "x2": 0, "y2": 1, "stops": [[0, p["floor"]], [1, p["base"]]]},
        {"id": "skyglass", "x1": 0, "y1": 0, "x2": 0, "y2": 1, "stops": [[0, p["sky"]], [1, p["wallDark"]]]},
    ]
    if night:
        gradients.append({"id": "windowlight", "x1": 0, "y1": 0, "x2": 1, "y2": 1, "stops": [[0, "#7ca7c9"], [1, "#233d63"]]})
    else:
        gradients.append({"id": "windowlight", "x1": 0, "y1": 0, "x2": 0, "y2": 1, "stops": [[0, "#d9ecf2"], [1, p["sky"]]]})

    background = _layer(
        "background",
        0.035,
        [
            _rect(0, 0, 1080, 1920, p["base"]),
            _rect(0, 0, 1080, 1260, "url(#wallwash)"),
            _rect(0, 1260, 1080, 660, "url(#floorwash)"),
            _rect(0, 0, 1080, 28, p["ink"], opacity=0.6),
            _rect(0, 1238, 1080, 10, p["ink"], opacity=0.65),
            _circle(540, 1040, 330, p["accent"], opacity=0.035),
        ],
        description="Wall, floor and base tone.",
    )

    midground = _layer(
        "midground",
        0.11,
        [
            # window with night sky, mullions and a moon
            _rect(92, 246, 430, 532, p["ink"], rx=8),
            _rect(104, 258, 406, 508, "url(#windowlight)", rx=4),
            _circle(356, 390, 58, p["paper"], opacity=0.82 if night else 0.45),
            _path("M 104 620 C 205 540 310 650 510 548 L 510 766 L 104 766 Z", p["wallDark"], opacity=0.6),
            _rect(299, 258, 14, 508, p["ink"], opacity=0.9),
            _rect(104, 496, 406, 12, p["ink"], opacity=0.9),
            _rect(92, 246, 430, 16, p["wallDark"]),
            _rect(92, 766, 430, 22, p["wallDark"]),
            # shelving
            _rect(620, 330, 350, 30, p["ink"], opacity=0.8),
            _rect(620, 548, 350, 30, p["ink"], opacity=0.8),
            _rect(620, 774, 350, 30, p["ink"], opacity=0.8),
            _rect(620, 330, 16, 474, p["ink"], opacity=0.7),
            _rect(954, 330, 16, 474, p["ink"], opacity=0.7),
            # jars and books on shelves
            _rect(660, 244, 38, 86, p["accent"], opacity=0.72, rx=5),
            _rect(712, 260, 28, 70, p["paper"], opacity=0.72, rx=4),
            _rect(760, 222, 42, 108, p["warm"], opacity=0.64, rx=6),
            _rect(840, 260, 22, 70, p["accent"], opacity=0.55, rx=3),
            _rect(878, 238, 48, 92, p["paper"], opacity=0.45, rx=4),
            _rect(652, 466, 44, 82, p["warm"], opacity=0.62, rx=5),
            _rect(712, 480, 30, 68, p["accent"], opacity=0.72, rx=4),
            _rect(778, 456, 58, 92, p["paper"], opacity=0.42, rx=5),
            _rect(870, 474, 32, 74, p["accent"], opacity=0.55, rx=4),
            # chalkboard / pinned diagram
            _rect(620, 862, 334, 216, p["ink"], rx=6, opacity=0.86),
            _rect(632, 874, 310, 192, p["wallDark"], rx=4, opacity=0.78),
            _line(664, 936, 910, 936, p["paper"], strokeWidth=3, opacity=0.38),
            _line(690, 980, 880, 980, p["accent"], strokeWidth=3, opacity=0.55),
            _line(720, 1022, 850, 1022, p["warm"], strokeWidth=2, opacity=0.42),
            _circle(882, 928, 9, p["accent"], opacity=0.65),
            _circle(844, 1014, 6, p["warm"], opacity=0.6),
            # pipes and conduit
            _line(70, 194, 70, 1210, p["wallDark"], strokeWidth=14, opacity=0.85),
            _line(70, 194, 1010, 194, p["wallDark"], strokeWidth=14, opacity=0.85),
            _rect(52, 194, 34, 18, p["ink"], opacity=0.7),
            _rect(990, 194, 34, 18, p["ink"], opacity=0.7),
        ],
        description="Window, shelving, instruments and wall structure.",
    )

    foreground = _layer(
        "foreground",
        0.22,
        [
            _rect(54, 1230, 972, 272, p["wallDark"], stroke=p["ink"], strokeWidth=8, rx=8),
            _rect(80, 1252, 920, 34, p["paper"], opacity=0.18, rx=6),
            # bench top and front
            _rect(54, 1434, 972, 70, p["ink"], opacity=0.9),
            _rect(84, 1504, 36, 304, p["wallDark"], opacity=0.95),
            _rect(960, 1504, 36, 304, p["wallDark"], opacity=0.95),
            _rect(84, 1504, 912, 18, p["ink"], opacity=0.8),
            # glassware
            _rect(220, 1280, 26, 150, p["paper"], opacity=0.28, rx=8),
            _rect(232, 1280, 4, 150, p["paper"], opacity=0.6),
            _path("M 206 1434 Q 206 1478 246 1478 Q 286 1478 286 1434 Z", p["accent"], opacity=0.34),
            _path("M 322 1340 Q 322 1478 382 1478 Q 442 1478 442 1340", p["paper"], opacity=0.2),
            _rect(318, 1332, 128, 10, p["paper"], opacity=0.4, rx=5),
            _path("M 350 1438 Q 350 1468 382 1468 Q 414 1468 414 1438 Z", p["accent"], opacity=0.3),
            # microscope
            _rect(610, 1380, 86, 22, p["ink"], rx=7),
            _rect(640, 1288, 18, 100, p["wallDark"], rx=6),
            _ellipse(650, 1276, 30, 16, p["warm"], opacity=0.65),
            _path("M 650 1290 L 720 1210", p["ink"], strokeWidth=14, strokeLinecap="round"),
            _rect(702, 1180, 42, 46, p["wallDark"], rx=9, stroke=p["ink"], strokeWidth=4),
            _circle(723, 1202, 12, p["accent"], opacity=0.85),
            # stool and crate
            _ellipse(850, 1510, 82, 24, p["ink"], opacity=0.55),
            _rect(798, 1510, 16, 230, p["wallDark"], rx=4),
            _rect(886, 1510, 16, 230, p["wallDark"], rx=4),
            _rect(760, 1754, 300, 92, p["wallDark"], rx=5, stroke=p["ink"], strokeWidth=5),
            _line(790, 1782, 1030, 1782, p["accent"], strokeWidth=3, opacity=0.25),
        ],
        description="Bench, glassware, microscope and floor objects.",
    )

    lighting = _layer(
        "lighting",
        0.16,
        [
            _polygon([[540, 0], [470, 900], [730, 900]], p["warm"], opacity=0.075),
            _rect(500, 0, 80, 18, p["warm"], opacity=0.65),
            _ellipse(540, 50, 180, 62, p["warm"], opacity=0.12),
            _ellipse(540, 1300, 300, 80, p["warm"], opacity=0.08),
            _circle(130, 900, 190, p["accent"], opacity=0.05),
            _circle(970, 720, 220, p["accent"], opacity=0.035),
        ],
        blend="screen",
        description="Practical lamp, window spill and accent glows.",
    )

    atmosphere = _layer(
        "atmosphere",
        0.28,
        [
            _circle(190, 860, 4, p["paper"], opacity=0.42, motion={"type": "float", "amplitude": 18, "speed": 0.7}),
            _circle(360, 720, 2.5, p["paper"], opacity=0.32, motion={"type": "float", "amplitude": 12, "speed": 0.9}),
            _circle(780, 690, 3.5, p["paper"], opacity=0.28, motion={"type": "float", "amplitude": 22, "speed": 0.55}),
            _circle(910, 880, 2, p["paper"], opacity=0.3, motion={"type": "float", "amplitude": 14, "speed": 0.8}),
            _circle(480, 620, 2, p["paper"], opacity=0.24, motion={"type": "float", "amplitude": 10, "speed": 1.1}),
        ],
        description="Dust motes and a restrained haze band.",
    )

    return {
        "renderer": "generated-set-v1",
        "viewBox": [0, 0, 1080, 1920],
        "background": p["base"],
        "transparent": False,
        "gradients": gradients,
        "layers": [background, midground, foreground, lighting, atmosphere],
        "subject": subject,
        "detail": detail,
    }


def _prop_spec(subject: str, palette: dict) -> dict:
    p = palette
    if "lampara" in subject or "lamp" in subject:
        elements = [
            _path("M 100 30 L 100 300", p["ink"], strokeWidth=7),
            _path("M 34 34 L 166 34", p["ink"], strokeWidth=7, strokeLinecap="round"),
            _polygon([[54, 34], [146, 34], [174, 158], [26, 158]], p["warm"], stroke=p["ink"], strokeWidth=5),
            _path("M 32 158 L 168 158", p["ink"], strokeWidth=6),
            _ellipse(100, 160, 74, 18, p["warm"], opacity=0.55),
            _circle(100, 175, 54, p["warm"], opacity=0.12),
            _rect(76, 300, 48, 24, p["wallDark"], rx=6, stroke=p["ink"], strokeWidth=4),
        ]
    else:
        elements = [
            _rect(30, 170, 140, 180, p["wallDark"], rx=8, stroke=p["ink"], strokeWidth=5),
            _rect(48, 192, 104, 92, p["accent"], opacity=0.35, rx=4),
            _circle(100, 142, 54, p["paper"], opacity=0.4, stroke=p["ink"], strokeWidth=4),
            _rect(18, 336, 164, 24, p["ink"], rx=5),
            _rect(64, 340, 72, 48, p["wallDark"], opacity=0.9),
        ]
    return {
        "renderer": "generated-prop-v1",
        "viewBox": [0, 0, 200, 400],
        "pivot": [100, 400],
        "elements": elements,
        "subject": subject,
    }


def _character_spec(subject: str, palette: dict) -> dict:
    p = palette
    return {
        "id": f"char_{_slug(subject)}",
        "name": _title(subject),
        "coat": p["paper"],
        "coatDark": p["wallDark"],
        "hat": p["accent"],
        "hatBand": p["wallDark"],
        "height": 1.0,
        "headRadius": 46,
        "hatStyle": "bald",
        "hairStyle": "curls",
        "facialHair": "none",
        "voice": "clear, curious, mid-range",
        "role": "researcher built for the generated laboratory set",
        "silhouette": "white lab coat, dark curls, compact silhouette",
        "palette": [p["paper"], p["wallDark"], p["accent"], p["warm"]],
        "gestures": ["holds a sample up to the light", "tilts her head before answering"],
        "wardrobe_states": {"default": "white lab coat over dark clothes"},
    }


def _graphic_overlay(subject: str, palette: dict) -> dict:
    numeric = "comparacion" in subject or "comparación" in subject or "grafico" in subject or "gráfico" in subject
    if numeric:
        return {
            "id": "generated-comparison",
            "type": "bar",
            "placement": {"kind": "screen"},
            "anchor": "top-left",
            "box": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.22},
            "from": 0.08,
            "to": 0.92,
            "data": {
                "title": "Comparación de laboratorio",
                "caption": "Lectura de dos muestras",
                "unit": "%",
                "series": [
                    {"label": "Muestra A", "value": 72, "tone": "accent"},
                    {"label": "Muestra B", "value": 48, "tone": "accentAlt"},
                ],
            },
            "source": "generated sample data; illustrative",
            "illustrative": True,
        }
    return {
        "id": "generated-callout",
        "type": "callout",
        "placement": {"kind": "screen"},
        "anchor": "top-left",
        "box": {"x": 0.06, "y": 0.1, "w": 0.82, "h": 0.16},
        "from": 0.1,
        "to": 0.9,
        "data": {"title": _title(subject), "caption": "Elemento de interfaz generado"},
        "illustrative": True,
    }


def _preview_svg_set(spec: dict, width: int = 1080, height: int = 1920) -> str:
    defs = []
    for gradient in spec.get("gradients", []):
        stops = "".join(
            f'<stop offset="{float(stop[0]) * 100:g}%" stop-color="{stop[1]}"/>' for stop in gradient.get("stops", [])
        )
        defs.append(
            f'<linearGradient id="{gradient["id"]}" x1="{gradient.get("x1", 0)}" y1="{gradient.get("y1", 0)}" '
            f'x2="{gradient.get("x2", 0)}" y2="{gradient.get("y2", 1)}">{stops}</linearGradient>'
        )
    body = []
    for layer in spec.get("layers", []):
        body.append(f'<g opacity="{layer.get("opacity", 1)}">')
        for el in layer.get("elements", []):
            body.append(_svg_element(el))
        body.append("</g>")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f"<defs>{''.join(defs)}</defs><rect width=\"{width}\" height=\"{height}\" fill=\"{spec.get('background', '#08060d')}\"/>"
        + "".join(body)
        + "</svg>"
    )


def _svg_element(el: dict) -> str:
    kind = el.get("kind", "rect")
    common = []
    if el.get("opacity") is not None:
        common.append(f'opacity="{el["opacity"]}"')
    if el.get("stroke"):
        common.append(f'stroke="{el["stroke"]}"')
    if el.get("strokeWidth"):
        common.append(f'stroke-width="{el["strokeWidth"]}"')
    if el.get("strokeLinecap"):
        common.append(f'stroke-linecap="{el["strokeLinecap"]}"')
    attrs = " ".join(common)
    if kind == "rect":
        rx = f' rx="{el["rx"]}"' if el.get("rx") else ""
        return f'<rect x="{el["x"]}" y="{el["y"]}" width="{el["w"]}" height="{el["h"]}" fill="{el["fill"]}"{rx} {attrs}/>'
    if kind == "circle":
        return f'<circle cx="{el["cx"]}" cy="{el["cy"]}" r="{el["r"]}" fill="{el["fill"]}" {attrs}/>'
    if kind == "ellipse":
        return f'<ellipse cx="{el["cx"]}" cy="{el["cy"]}" rx="{el["rx"]}" ry="{el["ry"]}" fill="{el["fill"]}" {attrs}/>'
    if kind == "path":
        return f'<path d="{el["d"]}" fill="{el.get("fill", "none")}" {attrs}/>'
    if kind == "polygon":
        points = " ".join(f"{x},{y}" for x, y in el["points"])
        return f'<polygon points="{points}" fill="{el["fill"]}" {attrs}/>'
    if kind == "line":
        return (
            f'<line x1="{el["x1"]}" y1="{el["y1"]}" x2="{el["x2"]}" y2="{el["y2"]}" '
            f'stroke="{el["stroke"]}" stroke-width="{el.get("strokeWidth", 2)}" {attrs}/>'
        )
    return ""


def _preview_svg_character(spec: dict) -> str:
    p = spec.get("palette") or ["#e8edf2", "#9fb0c2", "#69d5cf", "#ffb45c"]
    coat, dark, accent, warm = (p + p[-1:] * 4)[:4]
    hair = spec.get("hairStyle", "curls")
    curls = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{dark}"/>'
        for cx, cy, r in ((70, 68, 28), (102, 48, 34), (136, 68, 28), (86, 92, 20), (118, 92, 20))
    ) if hair == "curls" else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="720" viewBox="0 0 540 720">
<rect width="540" height="720" rx="22" fill="#0e0c16"/>
<text x="36" y="54" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="24" font-weight="700">{_escape(spec.get('name', 'Generated character'))}</text>
<text x="36" y="82" fill="#69d5cf" font-family="Segoe UI, sans-serif" font-size="14">GENERATED CAST · IDENTITY PREVIEW</text>
<g transform="translate(270 400) scale(1.5)">
  <path d="M -64 -132 C -82 -38 -74 118 -52 218 L 52 218 C 74 118 82 -38 64 -132 Z" fill="{coat}" stroke="#1a1626" stroke-width="4"/>
  <path d="M -38 -132 C -56 -50 -54 90 -40 200" stroke="{dark}" stroke-width="3" fill="none" opacity=".55"/>
  <path d="M -26 -130 L 0 -100 L 26 -130" stroke="{dark}" stroke-width="7" fill="none" stroke-linecap="round"/>
  {curls}
  <circle cx="0" cy="0" r="58" fill="{warm}" stroke="#1a1626" stroke-width="4"/>
  <path d="M -30 -14 q 12 -9 24 0 M 6 -14 q 12 -9 24 0" stroke="#1a1626" stroke-width="4" fill="none" stroke-linecap="round"/>
  <ellipse cx="-19" cy="-2" rx="5" ry="7" fill="#1a1626"/><ellipse cx="19" cy="-2" rx="5" ry="7" fill="#1a1626"/>
  <path d="M -10 23 Q 0 30 10 23" stroke="#1a1626" stroke-width="4" fill="none" stroke-linecap="round"/>
  <rect x="-12" y="-104" width="24" height="20" rx="7" fill="{dark}"/>
</g>
<g transform="translate(36 598)">
  <rect width="468" height="82" rx="12" fill="#171320"/>
  <text x="18" y="28" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="15">{_escape(spec.get('role', ''))}</text>
  <text x="18" y="54" fill="#a79fb8" font-family="Segoe UI, sans-serif" font-size="13">head r{spec.get('headRadius', 46)} · height {spec.get('height', 1)} · {_escape(spec.get('hatStyle', 'bald'))}</text>
</g>
<rect x="36" y="696" width="64" height="10" fill="{coat}"/><rect x="106" y="696" width="64" height="10" fill="{dark}"/><rect x="176" y="696" width="64" height="10" fill="{accent}"/><rect x="246" y="696" width="64" height="10" fill="{warm}"/>
</svg>"""


def _preview_svg_expression(spec: dict) -> str:
    values = spec.get("values", {})
    brow = float(values.get("brow", 0))
    mouth = float(values.get("mouth", 0.2))
    tilt = brow * 4
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="620" viewBox="0 0 540 620">
<rect width="540" height="620" rx="22" fill="#0e0c16"/>
<text x="36" y="54" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="24" font-weight="700">{_escape(spec.get('name', 'Expression'))}</text>
<text x="36" y="82" fill="#69d5cf" font-family="Segoe UI, sans-serif" font-size="14">GENERATED EXPRESSION · FACE PREVIEW</text>
<g transform="translate(270 320) rotate({-tilt})">
  <circle r="118" fill="#f0cfae" stroke="#1a1626" stroke-width="6"/>
  <path d="M -54 -26 q 22 -18 44 0 M 10 -26 q 22 -18 44 0" stroke="#1a1626" stroke-width="7" fill="none" stroke-linecap="round"/>
  <ellipse cx="-34" cy="2" rx="9" ry="13" fill="#1a1626"/><ellipse cx="34" cy="2" rx="9" ry="13" fill="#1a1626"/>
  <path d="M -34 {44 + mouth * 26} Q 0 {44 + mouth * 46} 34 {44 + mouth * 26}" stroke="#1a1626" stroke-width="6" fill="{ '#1a1626' if mouth > 0.6 else 'none'}" stroke-linecap="round"/>
</g>
<g transform="translate(36 516)">
  <rect width="468" height="66" rx="12" fill="#171320"/>
  <text x="18" y="28" fill="#a79fb8" font-family="Segoe UI, sans-serif" font-size="14">brow {brow:+.2f} · mouth {mouth:.2f} · head tilt {values.get('headTilt', 0):+.1f}°</text>
  <text x="18" y="51" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="13">compatible with the procedural rig</text>
</g>
</svg>"""


def _preview_svg_prop(spec: dict) -> str:
    elements = "".join(_svg_element(el) for el in spec.get("elements", []))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="540" height="620" viewBox="0 0 200 400">'
        '<rect width="540" height="620" fill="#0e0c16"/><g transform="translate(70 40) scale(2.0)">'
        + elements
        + "</g></svg>"
    )


def _preview_svg_graphic(spec: dict) -> str:
    overlay = spec.get("overlay", {})
    data = overlay.get("data", {})
    title = _escape(str(data.get("title", overlay.get("type", "Graphic"))))
    rows = data.get("series") or []
    bars = []
    for i, row in enumerate(rows[:4]):
        value = float(row.get("value", 0))
        y = 190 + i * 78
        bars.append(
            f'<text x="54" y="{y - 12}" fill="#c9bda9" font-family="Segoe UI, sans-serif" font-size="18">{_escape(str(row.get("label", "")))}</text>'
            f'<rect x="54" y="{y}" width="{max(2, value * 4.4):.0f}" height="26" rx="8" fill="{"#69d5cf" if i == 0 else "#c8892f"}"/>'
            f'<text x="{64 + value * 4.4:.0f}" y="{y + 20}" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="17">{value:g}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="720" viewBox="0 0 640 720">
<rect width="640" height="720" rx="22" fill="#0e0c16"/>
<text x="36" y="54" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="24" font-weight="700">{title}</text>
<text x="36" y="82" fill="#69d5cf" font-family="Segoe UI, sans-serif" font-size="14">GENERATED MOTION GRAPHIC · STATIC PREVIEW</text>
<rect x="40" y="120" width="560" height="380" rx="18" fill="#171320" stroke="#2c2536" stroke-width="2"/>
{''.join(bars)}
<g transform="translate(36 548)">
  <rect width="568" height="116" rx="12" fill="#171320"/>
  <text x="18" y="30" fill="#a79fb8" font-family="Segoe UI, sans-serif" font-size="14">type: {_escape(str(overlay.get('type', '')))} · from {overlay.get('from', 0):.2f} to {overlay.get('to', 1):.2f}</text>
  <text x="18" y="57" fill="#f6efe3" font-family="Segoe UI, sans-serif" font-size="13">renders through motion-graphics/OverlayLayer.tsx</text>
  <text x="18" y="84" fill="#ffb765" font-family="Segoe UI, sans-serif" font-size="13">source: {_escape(str(spec.get('description', '')))}</text>
</g>
</svg>"""


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _signature(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _detect(prompt: str) -> dict:
    text = prompt.lower()
    expression_hint = None
    for word, key in EXPRESSION_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            expression_hint = key
            break
    kind = None
    if re.search(r"\b(expresi[oó]n|expression|rostro|face)\b", text) and not re.search(r"\bpersonaje\b", text):
        kind = "expression"
    elif re.search(r"\b(personaje|character|cient[ií]fic[oa]|scientist|cast)\b", text):
        kind = "character"
    elif re.search(r"\b(gr[aá]fico|grafico|gr[aá]fica|chart|comparaci[oó]n|motion graphic)\b", text):
        kind = "motion_graphic"
    elif re.search(r"\b(ui|interfaz|interface|hud|panel)\b", text):
        kind = "ui"
    elif re.search(r"\b(l[aá]mpara|prop|objeto|object|silla|mesa|herramienta)\b", text):
        # A prop request often mentions the set it must be compatible with;
        # "lámpara compatible con el escenario" is still a prop, not a set.
        kind = "prop"
    elif re.search(r"\b(fondo|escenario|set|background|decorado)\b", text):
        kind = "set"
    else:
        kind = "set"

    subject = "laboratorio" if re.search(r"\blaborator|lab\b", text) else ""
    if not subject:
        words = re.findall(r"[a-záéíóúñ]+", text)
        stop = {
            "genera", "generar", "crea", "crear", "un", "una", "el", "la", "de", "del", "con", "en", "para",
            "fondo", "personaje", "escenario", "versión", "version", "nocturno", "nocturna", "basado", "existente",
            "expresión", "expresion", "sorpresa", "miedo", "gráfico", "grafico", "animado", "lámpara", "prop",
            "nuevo", "nueva", "estilo", "que", "por", "favor", "científico", "cientifico", "científica", "cientifica",
        }
        candidates = [w for w in words if w not in stop]
        subject = candidates[0] if candidates else kind.replace("_", " ")
    subject = _slug(subject)
    night = bool(re.search(r"\b(noche|nocturn\w*|night|oscuro|oscura)\b", text))
    warm = bool(re.search(r"\b(c[aá]lid\w*|warm|atardecer)\b", text))
    variation = bool(re.search(r"\b(versi[oó]n|variaci[oó]n|basado|existente|mismo|misma)\b", text))
    detail = "high" if re.search(r"\b(detall\w*|high|rico)\b", text) else "medium"
    flat = bool(re.search(r"\b(plano|flat|sin capas|sin profundidad)\b", text))
    return {
        "kind": kind,
        "subject": subject,
        "expression": expression_hint,
        "night": night,
        "warm": warm,
        "variation": variation,
        "detail": detail,
        "flat": flat,
        "prompt": prompt,
    }


def _palette(intent: dict) -> dict:
    if intent["warm"]:
        return dict(PALETTES["warm"])
    if intent["night"]:
        return dict(PALETTES["night"])
    return dict(PALETTES["day"])


def _generated_rel(kind: str, slug: str, version: int, name: str) -> str:
    return f"assets/generated/{kind}/{slug}/v{version}/{name}"


def _asset_entry(*, asset_id: str, kind: str, subject: str, spec: dict, preview: str, description: str,
                 tags: list[str], dependencies: list[str], usage: list[str], version: int,
                 versions: list[dict], config: dict, created: str) -> dict:
    return {
        "schema": 2,
        "id": asset_id,
        "name": _title(subject),
        "type": kind,
        "category": {
            "set": "Set", "character": "Cast", "expression": "Expression",
            "prop": "Prop", "motion_graphic": "Motion graphic", "ui": "UI",
        }.get(kind, kind),
        "style": STYLE,
        "description": description,
        "resolution": {"width": 1080, "height": 1920},
        "aspect": "9:16",
        "transparent": bool(spec.get("transparent", False)),
        "path": f"assets/generated/{kind}/{subject}/v{version}/asset.json",
        "preview": preview,
        "version": version,
        "versions": versions,
        "dependencies": dependencies,
        "tags": sorted(set([kind, subject, *tags])),
        "usage": usage,
        "character": subject if kind == "character" else None,
        "scene": subject if kind == "set" else None,
        "config": config,
        "license": LICENSE,
        "provenance": {
            "origin": "generated-locally",
            "author": AUTHOR,
            "source": SOURCE,
            "date": created,
            "restrictions": ["No external model or reference asset was used."],
        },
        "compatibility": {"engine": "remotion", "renderer": spec.get("renderer") or f"generated-{kind}-v1"},
        "status": "validated",
        "validated": True,
        "created": created,
        "layers": [layer["id"] for layer in spec.get("layers", [])],
        "signature": _signature(spec),
    }


def _preview_for(kind: str, spec: dict) -> str:
    if kind == "set":
        return _preview_svg_set(spec)
    if kind == "character":
        return _preview_svg_character(spec)
    if kind == "expression":
        return _preview_svg_expression(spec)
    if kind == "prop":
        return _preview_svg_prop(spec)
    return _preview_svg_graphic(spec)


def _write_preview(root: str, rel: str, svg: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)


def _value(text: str | None, default):
    return text if text not in (None, "") else default


def create_bundle(
    prompt: str,
    root: str = ".",
    *,
    asset_id: str | None = None,
    style: str | None = None,
    resolution: str | None = None,
    aspect: str | None = None,
    license_: str | None = None,
    source: str | None = None,
    force: bool = False,
    reference_ids: list[str] | None = None,
) -> dict:
    """Create an asset (and a paired expression when the prompt asks for one)."""
    intent = _detect(prompt)
    if style:
        intent["style"] = style
    if resolution:
        match = re.match(r"^\s*(\d+)\s*[x×]\s*(\d+)\s*$", resolution)
        if not match:
            return {"ok": False, "problems": [f"invalid resolution {resolution!r}; use WIDTHxHEIGHT"], "asset": None, "related": []}
        intent["resolution"] = {"width": int(match.group(1)), "height": int(match.group(2))}
    if aspect:
        intent["aspect"] = aspect
    if license_:
        intent["license"] = license_
    if source:
        intent["source"] = source

    # The generated assets draw in the renderer's 1080x1920 scene space. Do not
    # record a resolution/aspect the current renderer cannot actually compose.
    target = intent.get("resolution") or {"width": 1080, "height": 1920}
    if target != {"width": 1080, "height": 1920}:
        return {
            "ok": False,
            "problems": ["generated assets currently render at 1080x1920 only; resize in a format pass before changing metadata"],
            "asset": None,
            "related": [],
        }
    if intent.get("aspect") not in (None, "9:16"):
        return {
            "ok": False,
            "problems": ["generated assets currently render at 9:16 only; other aspect ratios need a format pass"],
            "asset": None,
            "related": [],
        }

    if asset_id:
        intent = {**intent, "subject": _slug(asset_id.split(":", 1)[-1])}

    reference_data = references_mod.load(root)
    known_refs = {r["id"] for r in reference_data.get("references", [])}
    if reference_ids:
        unknown = [rid for rid in reference_ids if rid not in known_refs]
        if unknown:
            return {"ok": False, "problems": [f"unknown reference(s): {', '.join(unknown)}"], "asset": None, "related": []}
        selected_refs = list(reference_ids)
    else:
        purpose = {"set": "background", "character": "character", "expression": "character",
                   "prop": "visual", "motion_graphic": "movement", "ui": "visual"}.get(intent["kind"], "visual")
        selected_refs = [r["id"] for r in references_mod.select(
            reference_data, purposes=(purpose, "style", "composition"), tags=(intent["subject"],), limit=2
        )]

    created = []
    primary = _create_one(prompt, intent, root, asset_id=asset_id, force=force, reference_ids=selected_refs)
    if not primary.get("ok"):
        return primary
    created.append(primary["asset"])
    if primary.get("duplicate"):
        return {"ok": True, "duplicate": True, "asset": primary["asset"], "related": [], "problems": []}

    # "personaje con expresión de sorpresa" is two compatible assets, not a
    # special case in the rig: the character identity plus a reusable expression.
    if intent["kind"] == "character" and intent.get("expression"):
        expression_prompt = f"expresión de {intent['expression']} para {intent['subject']}"
        expression_id = f"expression:{_slug(intent['expression'])}_{intent['subject']}"
        expr = _create_one(
            expression_prompt,
            {
                **intent,
                "kind": "expression",
                "subject": _slug(f"{intent['expression']}_{intent['subject']}"),
                "expression": intent["expression"],
                "character_ref": intent["subject"],
            },
            root,
            asset_id=expression_id,
            force=force,
            reference_ids=selected_refs,
        )
        if not expr.get("ok"):
            return {"ok": False, "problems": [f"character created, expression failed: {p}" for p in expr.get("problems", [])], "asset": primary["asset"], "related": []}
        created.append(expr["asset"])

    return {"ok": True, "duplicate": False, "asset": created[0], "related": created[1:], "problems": []}


def _create_one(prompt: str, intent: dict, root: str, *, asset_id: str | None = None, force: bool = False, reference_ids=()) -> dict:
    registry = generated_mod.load_registry(root)
    kind = intent["kind"]
    subject = _slug(intent["subject"]) or "asset"
    prefix = PREFIX.get(kind, kind)
    if asset_id:
        aid = asset_id if ":" in asset_id else f"{prefix}:{_slug(asset_id)}"
        subject = aid.split(":", 1)[1]
    else:
        aid = f"{prefix}:{subject}"

    existing = next((a for a in registry["assets"] if a.get("id") == aid), None)
    version = 1 + max([int(v.get("version", 0)) for v in (existing or {}).get("versions", [])] or [0]) if existing else 1
    palette = _palette(intent)
    created = _now()
    dependencies: list[str] = []
    usage: list[str] = []
    tag_extra: list[str] = []
    config: dict = {}

    if kind == "set":
        spec = _set_spec(subject, palette, night=bool(intent.get("night")), detail=str(intent.get("detail", "medium")))
        if intent.get("variation") and existing:
            old = generated_mod.load(root).get("sets", {}).get(subject)
            if old:
                # Preserve geometry and identity; change atmosphere/lighting only.
                spec = json.loads(json.dumps(old))
                spec["palette_name"] = "night" if intent.get("night") else "day"
                spec["variation_of"] = subject
                spec["flat"] = False
                spec["background"] = palette["base"]
                for layer in spec.get("layers", []):
                    if layer["id"] in ("lighting", "atmosphere"):
                        continue
                    for el in layer.get("elements", []):
                        for key in ("fill", "stroke"):
                            value = el.get(key)
                            if isinstance(value, str) and value.startswith("#"):
                                el[key] = _recolor(value, palette)
                spec["gradients"] = _regradient(spec.get("gradients", []), palette)
        if intent.get("flat"):
            flat_elements = [el for layer in spec.get("layers", []) for el in layer.get("elements", [])]
            spec = {**spec, "flat": True, "layers": [_layer("background", 0.0, flat_elements, description="Flat background, no parallax layers.")]}
        description = f"Generated {('night ' if intent.get('night') else '')}laboratory set with coordinated background, midground, foreground, lighting and atmosphere layers."
        dependencies = ["engine:atmosphere", "engine:texture"]
        usage = ["background", "scene", "reusable"]
        tag_extra = ["laboratory", "svg", "layered", "night" if intent.get("night") else "day"]
        config = {"renderer": "GeneratedScene", "sceneKey": subject, "layerOrder": [l["id"] for l in spec["layers"]]}
        generated_key = "sets"
        render_value = spec
    elif kind == "character":
        spec = _character_spec(subject, palette)
        description = f"Generated character identity '{_title(subject)}' built for the procedural rig, with palette, proportions, wardrobe and expression metadata."
        dependencies = ["rig:default"]
        usage = ["cast", "actor"]
        tag_extra = ["cast", "rig", "identity"]
        config = {"castKey": subject, "rig": "rig:default"}
        generated_key = "characters"
        render_value = spec
    elif kind == "expression":
        name = intent.get("expression") or "surprise"
        values = dict(EXPRESSION_VALUES.get(name, EXPRESSION_VALUES["surprise"]))
        char_ref = intent.get("character_ref") or subject.replace(f"{_slug(name)}_", "")
        spec = {
            "renderer": "generated-expression-v1",
            "name": _title(name),
            "expression": name,
            "values": values,
            "character_ref": f"character:{char_ref}" if char_ref else None,
            "viewBox": [0, 0, 540, 620],
        }
        description = f"Reusable expression '{name}' for the procedural character rig; identity-changing fields are prohibited."
        dependencies = [f"character:{char_ref}"] if char_ref else []
        usage = ["expression", "actor"]
        tag_extra = ["expression", name]
        config = {"castKey": char_ref or None, "expression": name, "values": values}
        generated_key = "expressions"
        render_value = {"name": _title(name), "values": values, "character_ref": char_ref or None}
    elif kind == "prop":
        spec = _prop_spec(subject, palette)
        description = f"Generated reusable prop '{_title(subject)}' drawn from coordinated SVG primitives."
        if existing and existing.get("dependencies"):
            dependencies = list(existing["dependencies"])
        if not dependencies:
            dependencies = ["set:laboratorio"] if "laboratorio" in subject else []
        usage = ["prop", "foreground", "reusable"]
        tag_extra = ["prop", "svg"]
        config = {"renderer": "PropLayer", "propKey": subject, "pivot": [100, 400]}
        generated_key = "props"
        render_value = spec
    else:
        overlay = _graphic_overlay(subject, palette)
        spec = {
            "renderer": "generated-graphic-v1",
            "overlay": overlay,
            "description": "Illustrative generated data; every numeric value is explicitly marked illustrative.",
            "viewBox": [0, 0, 640, 720],
        }
        description = f"Generated {'motion graphic' if kind == 'motion_graphic' else 'UI asset'} '{_title(subject)}' using the existing overlay renderer."
        dependencies = []
        usage = ["motion-graphic" if kind == "motion_graphic" else "ui", "overlay"]
        tag_extra = ["motion-graphic", "chart", "overlay"]
        config = {"renderer": "OverlayLayer", "graphicKey": subject, "overlay": overlay}
        generated_key = "graphics"
        render_value = overlay

    # duplicates: same id + identical signature is a no-op, not a new version
    if existing and not force and existing.get("signature") == _signature(spec):
        return {"ok": True, "duplicate": True, "asset": existing, "related": [], "problems": []}

    # validation happens before anything is written into the library
    problems = _validate_spec(kind, spec, preview=None)
    if problems:
        return {"ok": False, "asset": None, "related": [], "problems": problems}

    asset_path = _generated_rel(kind, subject, version, "asset.json")
    preview_path = _generated_rel(kind, subject, version, "preview.svg")
    _write_preview(root, preview_path, _preview_for(kind, spec))
    generated_mod.write_json(os.path.join(root, asset_path), spec)

    versions = list((existing or {}).get("versions") or [])
    versions.append({
        "version": version,
        "path": asset_path,
        "preview": preview_path,
        "created": created,
        "signature": _signature(spec),
        "status": "validated",
    })
    entry = _asset_entry(
        asset_id=aid,
        kind=kind,
        subject=subject,
        spec=spec,
        preview=preview_path,
        description=description,
        tags=tag_extra,
        dependencies=dependencies,
        usage=usage,
        version=version,
        versions=versions,
        config=config,
        created=created,
    )
    entry["license"] = intent.get("license", LICENSE)
    entry["references"] = list(reference_ids)
    if intent.get("source"):
        entry["provenance"]["source"] = intent["source"]
    if intent.get("resolution"):
        entry["resolution"] = intent["resolution"]
    if intent.get("aspect"):
        entry["aspect"] = intent["aspect"]

    reg = [a for a in registry["assets"] if a.get("id") != aid]
    reg.append(entry)
    registry["assets"] = sorted(reg, key=lambda a: a["id"])
    generated_mod.save_registry(root, registry)

    data = generated_mod.load(root)
    data[generated_key][subject] = render_value
    generated_mod.save(root, data)
    return {"ok": True, "duplicate": False, "asset": entry, "related": [], "problems": []}


def _recolor(hex_color: str, palette: dict) -> str:
    """Map a daylight token colour into the variation palette without changing geometry."""
    value = hex_color.lower()
    tokens = {
        "#dfe7e3": "base", "#b9c8c6": "wall", "#819795": "wallDark", "#8a8174": "floor",
        "#258f8a": "accent", "#e9a44f": "warm", "#f6f2e7": "paper", "#182024": "ink",
        "#b9d9e8": "sky", "#ffffff": "paper", "#f0cfae": "paper", "#69d5cf": "accent",
        "#47a6a0": "accent", "#ffb45c": "warm", "#ffcf82": "warm", "#1a2030": "ink",
        "#111a28": "ink", "#070a10": "ink",
    }
    return palette.get(tokens.get(value, "wall"), palette["wall"])


def _regradient(gradients: list[dict], palette: dict) -> list[dict]:
    out = []
    for gradient in gradients:
        copy = json.loads(json.dumps(gradient))
        copy["stops"] = [[stop[0], _recolor(stop[1], palette)] for stop in copy.get("stops", [])]
        out.append(copy)
    return out


def _validate_spec(kind: str, spec: dict, *, preview: str | None) -> list[str]:
    problems: list[str] = []
    if kind == "set":
        if spec.get("renderer") != "generated-set-v1":
            problems.append("set: wrong renderer")
        if not spec.get("layers"):
            problems.append("set: no layers")
        if spec.get("viewBox") != [0, 0, 1080, 1920]:
            problems.append("set: viewBox must be 1080x1920")
        ids = [layer.get("id") for layer in spec.get("layers", [])]
        expected = ["background"] if spec.get("flat") else ["background", "midground", "foreground", "lighting", "atmosphere"]
        if ids != expected:
            problems.append(f"set: layers must be {', '.join(expected)}")
        for layer in spec.get("layers", []):
            if not layer.get("elements"):
                problems.append(f"set: layer {layer.get('id')} has no elements")
    elif kind == "character":
        required = ("id", "name", "coat", "coatDark", "hat", "hatBand", "height", "headRadius", "hatStyle", "hairStyle", "facialHair")
        missing = [field for field in required if spec.get(field) in (None, "")]
        if missing:
            problems.append(f"character: missing {', '.join(missing)}")
        if not 24 <= float(spec.get("headRadius", 0)) <= 72:
            problems.append("character: headRadius outside 24-72")
        if not 0.75 <= float(spec.get("height", 0)) <= 1.25:
            problems.append("character: height outside 0.75-1.25")
    elif kind == "expression":
        if spec.get("renderer") != "generated-expression-v1":
            problems.append("expression: wrong renderer")
        values = spec.get("values") or {}
        for key in ("brow", "mouth", "headTilt", "yaw", "blink"):
            if key not in values:
                problems.append(f"expression: missing {key}")
        if values and not -1 <= float(values.get("brow", 0)) <= 1:
            problems.append("expression: brow outside -1..1")
    elif kind == "prop":
        if spec.get("renderer") != "generated-prop-v1":
            problems.append("prop: wrong renderer")
        if not spec.get("elements"):
            problems.append("prop: no elements")
        if spec.get("viewBox") != [0, 0, 200, 400]:
            problems.append("prop: viewBox must be 200x400")
    else:
        if spec.get("renderer") != "generated-graphic-v1":
            problems.append("graphic: wrong renderer")
        overlay = spec.get("overlay") or {}
        if not overlay.get("type"):
            problems.append("graphic: overlay has no type")
        if overlay.get("type") in {"counter", "bar", "donut", "line", "ranking"} and not overlay.get("source") and not overlay.get("illustrative"):
            problems.append("graphic: numeric overlay needs a source or illustrative=true")
    if preview is not None and not os.path.exists(preview):
        problems.append("preview: missing")
    return problems
