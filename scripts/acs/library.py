"""Persistent asset library and catalogue.

The point of this module is reuse: a character, a set, a sound or a voice is
described once, gets a stable id, and every later project refers to it instead
of rebuilding it. The catalogue is *derived* from the real sources of truth
(cast.json, the scene components, the voice config, the score's event types),
so it cannot drift from what actually renders; hand-written extras live in
``assets/registry.json`` and are merged in.

Nothing here touches the network. Nothing here writes into a project.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from datetime import datetime, timezone

from . import generated as generated_mod

CATALOG_PATH = os.path.join("assets", "catalog.json")
REGISTRY_PATH = os.path.join("assets", "registry.json")

# What each asset type is allowed to depend on. Used by validate() so a broken
# dependency is reported instead of silently rendering a fallback.
ALLOWED_DEPENDENCIES = {
    "character": {"rig", "voice"},
    "rig": {"engine", "material"},
    "set": {"material", "engine", "prop"},
    "prop": {"set", "material"},
    "material": set(),
    "engine": set(),
    "sfx": set(),
    "music": set(),
    "voice": set(),
    "camera": set(),
    "transition": set(),
    "expression": {"character"},
    "motion_graphic": {"set", "material"},
    "ui": {"motion_graphic"},
}

TYPE_LABELS = {
    "character": "Cast",
    "rig": "Rig",
    "set": "Set",
    "prop": "Prop",
    "material": "Material",
    "engine": "Engine module",
    "sfx": "Sound effect",
    "music": "Music",
    "voice": "Voice",
    "camera": "Camera move",
    "transition": "Transition",
    "expression": "Expression",
    "motion_graphic": "Motion graphic",
    "ui": "UI",
}

#: Schema-2 registry assets must carry these before they can enter the catalogue.
SCHEMA2_REQUIRED = (
    "id", "name", "type", "description", "style", "resolution", "aspect", "preview",
    "license", "provenance", "compatibility", "status", "versions",
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _camel_component(value: str | None) -> str | None:
    """`BellInsert` -> `bellInsert`; the key Demo.tsx actually uses."""
    if not value:
        return None
    return value[0].lower() + value[1:]


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _version_of(path: str) -> int:
    """A cheap content version: file mtime, so a changed set reads as v+1."""
    try:
        return int(os.path.getmtime(path))
    except OSError:
        return 0


def _entry(
    *,
    asset_id: str,
    name: str,
    kind: str,
    path: str,
    description: str,
    tags=(),
    dependencies=(),
    config=None,
    license_: str = "original",
    validated: bool = True,
    root: str = ".",
) -> dict:
    return {
        "id": asset_id,
        "name": name,
        "type": kind,
        "category": TYPE_LABELS.get(kind, kind),
        "path": path.replace(os.sep, "/"),
        "description": description,
        "version": _version_of(os.path.join(root, path)) if "#" not in path else 1,
        "dependencies": list(dependencies),
        "config": config or {},
        "license": license_,
        "created": datetime.fromtimestamp(
            os.path.getmtime(os.path.join(root, path)) if os.path.exists(os.path.join(root, path)) else 0,
            tz=timezone.utc,
        ).strftime("%Y-%m-%d") if os.path.exists(os.path.join(root, path)) else None,
        "validated": bool(validated),
        "tags": [t for t in tags if t],
    }


def _cast_assets(root: str) -> list[dict]:
    cast = read_json(os.path.join(root, "studio", "src", "data", "cast.json"), {}) or {}
    out = []
    for key, char in (cast.get("characters") or {}).items():
        out.append(
            _entry(
                asset_id=f"character:{key}",
                name=char.get("name", key),
                kind="character",
                path="studio/src/data/cast.json",
                description=char.get("role", ""),
                tags=[char.get("hatStyle", ""), char.get("hairStyle", ""), "cast", key],
                dependencies=["rig:default"],
                config={
                    "coat": char.get("coat"),
                    "coatDark": char.get("coatDark"),
                    "hat": char.get("hat"),
                    "headRadius": char.get("headRadius"),
                    "height": char.get("height"),
                    "voice": char.get("voice"),
                    "wardrobe_states": list((char.get("wardrobe_states") or {}).keys()),
                },
                root=root,
            )
        )
    return out


SET_DESCRIPTIONS = {
    "townnight": "Night square: timber-framed houses, bell post, lantern, well, sledge.",
    "doorway": "Threshold: warm furnished interior seen from the snow, lamp and light spill.",
    "fielddawn": "Dawn graveyard: headstones, chapel, stone wall, open grave, low sun.",
    "bellinsert": "Insert: belfry louvres, stone arch, headstock and the bronze bell.",
    "workshop": "Interior: tailor's workroom at dawn, window, thread shelf, dress form and worktable.",
    "greenhouse": "Interior: dry glasshouse at dawn, bench, rain barrel, potted plant and watering can.",
    "facecloseup": "Close-up plate: bokeh and lattice behind the keeper's face.",
}


def _set_assets(root: str) -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(root, "studio", "src", "scenes", "*.tsx"))):
        key = os.path.splitext(os.path.basename(path))[0]
        slug = key.lower()
        out.append(
            _entry(
                asset_id=f"set:{slug}",
                name=re.sub(r"(?<!^)(?=[A-Z])", " ", key),
                kind="set",
                path=os.path.relpath(path, root),
                description=SET_DESCRIPTIONS.get(slug, "Scene component drawn in code."),
                tags=["set", slug, "svg"],
                dependencies=["engine:atmosphere", "engine:texture"],
                config={"component": key},
                root=root,
            )
        )
    return out


def _engine_assets(root: str) -> list[dict]:
    wanted = {
        "atmosphere": ("Atmosphere primitives", "Cast shadows, light shafts, fog, dust, glows, contrast veil."),
        "texture": ("Material patterns", "Procedural ashlar, planks, shingles, snow, carpet, wallpaper, frost."),
        "camera": ("Camera rig", "Camera moves and parallax groups."),
        "filmfinish": ("Film finish", "Grain, vignette, warm/cool grade, halation."),
        "math": ("Math helpers", "Deterministic easing, keyframes, PRNG and hashing."),
    }
    out = []
    for path in sorted(glob.glob(os.path.join(root, "studio", "src", "engine", "*.ts*"))):
        key = os.path.splitext(os.path.basename(path))[0].lower()
        if key not in wanted:
            continue
        name, desc = wanted[key]
        out.append(
            _entry(
                asset_id=f"engine:{key}",
                name=name,
                kind="engine",
                path=os.path.relpath(path, root),
                description=desc,
                tags=["engine", key],
                root=root,
            )
        )
    return out


def _rig_assets(root: str) -> list[dict]:
    path = "studio/src/characters/Character.tsx"
    if not os.path.exists(os.path.join(root, path)):
        return []
    return [
        _entry(
            asset_id="rig:default",
            name="Procedural character rig",
            kind="rig",
            path=path,
            description="Two-segment arms with elbow, volume-shaded coat, brows, boots, head lead.",
            tags=["rig", "character", "procedural"],
            dependencies=["engine:math"],
            config={"props": ["hold", "brow", "blink", "gait", "phase"]},
            root=root,
        )
    ]


def _voice_assets(root: str) -> list[dict]:
    config = read_json(os.path.join(root, "config", "voices.json"), {}) or {}
    out = []
    for key, voice in (config.get("voices") or {}).items():
        out.append(
            _entry(
                asset_id=f"voice:{key}",
                name=voice.get("name", key),
                kind="voice",
                path="config/voices.json",
                description=voice.get("style", ""),
                tags=["voice", key, voice.get("provider", "")],
                config={
                    "provider": voice.get("provider"),
                    "voice_id": voice.get("voice_id"),
                    "language": voice.get("language"),
                    "configured": bool(voice.get("voice_id")),
                    "settings": voice.get("settings", {}),
                },
                license_="user-provided (ElevenLabs terms)",
                root=root,
            )
        )
    return out


def _sfx_assets(root: str) -> list[dict]:
    """The score's event vocabulary, taken from the generator itself."""
    try:
        import sys

        sys.path.insert(0, os.path.join(root, "scripts"))
        from acs import audio_gen  # noqa: WPS433 (local import, keeps this module standalone)

        project = read_json(os.path.join(root, "studio", "src", "data", "project.json"), {}) or {}
        spec = audio_gen.spec_from_project(project)
        kinds = sorted({e["type"] for e in spec.get("events", [])})
    except Exception:  # the catalogue must still build if the score cannot
        kinds = []
    out = []
    for kind in kinds:
        out.append(
            _entry(
                asset_id=f"sfx:{_slug(kind)}",
                name=kind.replace("_", " "),
                kind="sfx",
                path="scripts/acs/audio_gen.py",
                description="Synthesised on demand (deterministic, LOCAL mode, no credits).",
                tags=["sfx", "procedural", kind],
                config={"generator": "audio_gen", "event": kind},
                root=root,
            )
        )
    return out


def _camera_assets(root: str) -> list[dict]:
    path = "studio/src/engine/CameraRig.tsx"
    if not os.path.exists(os.path.join(root, path)):
        return []
    moves = [
        "static", "drift", "dollyIn", "dollyOut", "panLeft", "panRight",
        "tiltUp", "craneDown", "pushInSlow", "trackLeft", "trackRight", "reframe",
        "handheld",
    ]
    return [
        _entry(
            asset_id=f"camera:{_slug(m)}",
            name=m,
            kind="camera",
            path=path,
            description="Named camera intent expressed as a transform curve.",
            tags=["camera", m],
            root=root,
        )
        for m in moves
    ]


def _transition_assets(root: str) -> list[dict]:
    path = "studio/src/composition/Demo.tsx"
    if not os.path.exists(os.path.join(root, path)):
        return []
    specs = {
        "cut": "0 frames of overlap: subject continues, framing changes.",
        "dissolve": "Overlap of the next shot's transitionIn frames: different setup.",
    }
    return [
        _entry(asset_id=f"transition:{k}", name=k, kind="transition", path=path, description=v,
               tags=["transition", k, "edit"], root=root)
        for k, v in specs.items()
    ]


def collect(root: str = ".") -> dict:
    """Scan the project and return the catalogue (without writing it)."""
    assets: list[dict] = []
    for builder in (
        _cast_assets,
        _rig_assets,
        _set_assets,
        _engine_assets,
        _voice_assets,
        _sfx_assets,
        _camera_assets,
        _transition_assets,
    ):
        assets.extend(builder(root))

    registry = read_json(os.path.join(root, REGISTRY_PATH), {}) or {}
    for raw in registry.get("assets", []):
        entry = _normalise_registry_entry(raw, root)
        assets.append(entry)

    assets.sort(key=lambda a: (a["type"], a["id"]))
    return {
        "version": 1,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "derived from cast.json, scenes, engine, voices.json, audio_gen and assets/registry.json (schema 2: generated assets, versions, previews, provenance)",
        "counts": _counts(assets),
        "assets": assets,
    }


def _normalise_registry_entry(raw: dict, root: str) -> dict:
    """One metadata shape for hand-authored and forged assets.

    Existing schemas stay readable; schema-2 entries get the full fields the
    asset workflow promises. Missing values are normalised, not invented as
    validation passes.
    """
    entry = dict(raw)
    entry.setdefault("validated", os.path.exists(os.path.join(root, entry.get("path", ""))))
    entry.setdefault("version", 1)
    entry.setdefault("category", TYPE_LABELS.get(entry.get("type", ""), entry.get("type", "")))
    entry.setdefault("dependencies", [])
    entry.setdefault("config", {})
    entry.setdefault("tags", [])
    entry.setdefault("license", "unspecified")
    entry.setdefault("style", "inherited")
    entry.setdefault("resolution", {"width": 1080, "height": 1920})
    entry.setdefault("aspect", "9:16")
    entry.setdefault("preview", None)
    entry.setdefault("compatibility", {"engine": "remotion", "renderer": "inherited"})
    entry.setdefault("status", "validated" if entry.get("validated") else "unvalidated")
    entry.setdefault("usage", [])
    entry.setdefault("character", None)
    entry.setdefault("scene", None)
    entry.setdefault("layers", [])
    entry.setdefault("transparent", False)
    entry.setdefault("versions", [])
    entry.setdefault(
        "provenance",
        {
            "origin": "project-source" if entry.get("license") == "original" else "registry",
            "author": None,
            "source": entry.get("path"),
            "date": entry.get("created"),
            "restrictions": [],
        },
    )
    entry.setdefault("author", (entry.get("provenance") or {}).get("author"))
    entry.setdefault("source", (entry.get("provenance") or {}).get("source"))
    entry.setdefault("created", (entry.get("provenance") or {}).get("date"))
    return entry


def _counts(assets: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for a in assets:
        counts[a["type"]] = counts.get(a["type"], 0) + 1
    return counts


def build(root: str = ".") -> dict:
    catalog = collect(root)
    write_json(os.path.join(root, CATALOG_PATH), catalog)
    return catalog


def load(root: str = ".") -> dict:
    path = os.path.join(root, CATALOG_PATH)
    catalog = read_json(path)
    if not catalog:
        catalog = build(root)
    return catalog


def search(
    catalog: dict,
    *,
    query: str | None = None,
    type_: str | None = None,
    tag: str | None = None,
    style: str | None = None,
    scene: str | None = None,
    character: str | None = None,
    usage: str | None = None,
    compatible: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Search the one catalogue. Case-insensitive; all filters are AND-ed.

    Free text covers id, name, description, tags, style, scene, character,
    usage and compatibility, so an agent can look up "night laboratory" or
    "character:elder" without knowing the asset id.
    """
    q = (query or "").lower().strip()
    out = []
    for a in catalog.get("assets", []):
        if type_ and a["type"] != type_:
            continue
        if tag and tag.lower() not in [str(t).lower() for t in a.get("tags", [])]:
            continue
        if style and str(a.get("style", "")).lower() != style.lower():
            continue
        if scene and str(a.get("scene") or "").lower() != scene.lower():
            continue
        if character and str(a.get("character") or "").lower() != character.lower():
            continue
        if usage and usage.lower() not in [str(u).lower() for u in a.get("usage", [])]:
            continue
        compat = a.get("compatibility") or {}
        if compatible and compatible.lower() not in json.dumps(compat).lower():
            continue
        if q:
            haystack = " ".join(
                [
                    str(a.get("id", "")), str(a.get("name", "")), str(a.get("description", "")),
                    " ".join(map(str, a.get("tags", []))), str(a.get("style", "")),
                    str(a.get("scene") or ""), str(a.get("character") or ""),
                    " ".join(map(str, a.get("usage", []))), json.dumps(compat),
                ]
            ).lower()
            if q not in haystack:
                continue
        out.append(a)
    out.sort(key=lambda a: (a["type"], a["id"]))
    return out[:limit] if limit else out


def get(catalog: dict, asset_id: str, *, version: int | None = None) -> dict | None:
    """Resolve an id to its latest version, or one explicit archived version."""
    for a in catalog.get("assets", []):
        if a["id"] != asset_id:
            continue
        if version is None:
            return a
        for v in a.get("versions", []):
            if int(v.get("version", 0)) == int(version):
                archived = dict(a)
                archived.update(v)
                archived["version"] = int(version)
                archived["archived"] = True
                return archived
        return None
    return None


def similar(catalog: dict, asset_id: str, *, limit: int = 5) -> list[dict]:
    """Rank nearby assets so a creator reuses or varies instead of duplicating."""
    base = get(catalog, asset_id)
    if not base:
        return []
    base_tags = {str(t).lower() for t in base.get("tags", [])}
    out = []
    for asset in catalog.get("assets", []):
        if asset["id"] == asset_id:
            continue
        tags = {str(t).lower() for t in asset.get("tags", [])}
        score = 0.0
        if asset.get("type") == base.get("type"):
            score += 3.0
        if asset.get("style") and asset.get("style") == base.get("style"):
            score += 1.5
        if base_tags and tags:
            score += 3.0 * len(base_tags & tags) / len(base_tags | tags)
        if base.get("scene") and base.get("scene") == asset.get("scene"):
            score += 1.5
        if base.get("character") and base.get("character") == asset.get("character"):
            score += 1.5
        if score > 0:
            out.append({**asset, "similarity": round(score, 3)})
    out.sort(key=lambda a: (-a["similarity"], a["id"]))
    return out[:limit]


def validate(catalog: dict, root: str = ".") -> dict:
    """Ids unique, files present, dependencies resolvable and of an allowed type."""
    problems: list[str] = []
    ids = [a.get("id") for a in catalog.get("assets", [])]
    dupes = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dupes):
        problems.append(f"duplicate id: {d}")
    known = set(ids)
    for a in catalog.get("assets", []):
        path = a.get("path", "")
        file_part = path.split("#")[0]
        if file_part and not os.path.exists(os.path.join(root, file_part)):
            problems.append(f"{a['id']}: missing file {file_part}")
        if not a.get("license") or a.get("license") == "unspecified":
            problems.append(f"{a['id']}: no licence recorded")
        if a.get("schema") == 2:
            for field in SCHEMA2_REQUIRED:
                if a.get(field) in (None, "", [], {}):
                    problems.append(f"{a['id']}: schema-2 asset has no {field}")
            preview = a.get("preview")
            if preview and not os.path.exists(os.path.join(root, preview)):
                problems.append(f"{a['id']}: missing preview {preview}")
            provenance = a.get("provenance") or {}
            for field in ("origin", "source", "date"):
                if not provenance.get(field):
                    problems.append(f"{a['id']}: provenance has no {field}")
            versions = a.get("versions") or []
            numbers = [int(v.get("version", 0)) for v in versions]
            if numbers != sorted(numbers) or len(set(numbers)) != len(numbers):
                problems.append(f"{a['id']}: versions are not unique and ordered")
            if versions and int(a.get("version", 0)) != max(numbers):
                problems.append(f"{a['id']}: latest version pointer is not the highest version")
            for version in versions:
                vpath = version.get("path")
                if vpath and not os.path.exists(os.path.join(root, vpath)):
                    problems.append(f"{a['id']}: archived v{version.get('version')} file is missing")
            compatibility = a.get("compatibility") or {}
            if compatibility.get("engine") not in (None, "remotion"):
                problems.append(f"{a['id']}: unsupported engine {compatibility.get('engine')}")
            if a.get("status") != "validated":
                problems.append(f"{a['id']}: status is {a.get('status')!r}, not validated")
            if a.get("type") == "set":
                spec_path = os.path.join(root, file_part)
                try:
                    spec = read_json(spec_path, {}) or {}
                except (OSError, ValueError) as exc:
                    problems.append(f"{a['id']}: unreadable set spec ({exc})")
                    spec = {}
                if spec.get("renderer") != "generated-set-v1" or not spec.get("layers"):
                    problems.append(f"{a['id']}: set spec is not renderable")
        allowed = ALLOWED_DEPENDENCIES.get(a["type"], set())
        for dep in a.get("dependencies", []):
            dep_asset = get(catalog, dep)
            if not dep_asset:
                problems.append(f"{a['id']}: unknown dependency {dep}")
                continue
            if dep_asset["type"] not in allowed:
                problems.append(f"{a['id']}: dependency {dep} of type {dep_asset['type']} is not allowed")
    return {"ok": not problems, "checked": len(ids), "problems": problems}


def compose(spec: dict, catalog: dict, *, default_fps: int = 30) -> dict:
    """Build a renderable manifest from asset ids.

    The catalogue is not a list of files: a project is assembled *through* it, and
    composition fails on an id that does not exist instead of rendering a blank
    shot. `spec` mirrors project.json but may name shots by asset id.
    """
    problems: list[str] = []
    shots = []
    for i, shot in enumerate(spec.get("shots", [])):
        shot_id = shot.get("id", i)
        scene = shot.get("scene", "")
        scene_hint = scene.split(":", 1)[1] if str(scene).startswith("set:") else scene
        scene_asset = get(catalog, f"set:{_slug(scene_hint)}")
        if not scene_asset:
            problems.append(f"shot {shot_id}: unknown set {scene}")
            scene_key = _slug(scene_hint)
        else:
            # The catalogue id is a stable slug (`bellinsert`), while the
            # renderer's scene map is camelCase (`bellInsert`). Keep the
            # renderer-facing key; lowering it here used to make a composed
            # manifest unreachable by Demo.tsx.
            scene_key = (
                (scene_asset.get("config") or {}).get("sceneKey")
                or _camel_component((scene_asset.get("config") or {}).get("component"))
                or str(scene_hint)
            )
        camera = shot.get("camera", "static")
        if not get(catalog, f"camera:{_slug(camera)}"):
            problems.append(f"shot {shot_id}: unknown camera {camera}")
        actors = []
        for actor in shot.get("actors", []) or []:
            char_key = actor.get("id", "")
            char_key = char_key.split(":", 1)[1] if str(char_key).startswith("character:") else char_key
            if not get(catalog, f"character:{char_key}"):
                problems.append(f"shot {shot_id}: unknown character {actor.get('id')}")
            expression = actor.get("expression")
            if expression:
                expr_id = expression if str(expression).startswith("expression:") else f"expression:{expression}"
                expr_asset = get(catalog, expr_id)
                if not expr_asset:
                    problems.append(f"shot {shot_id}: unknown expression {expression}")
                elif expr_asset.get("type") != "expression":
                    problems.append(f"shot {shot_id}: {expression} is not an expression asset")
            actors.append({**actor, "id": char_key, "preset": actor.get("preset", "idle"), "scale": actor.get("scale", 1.5)})

        props = []
        for prop in shot.get("props", []) or []:
            prop_id = prop.get("id", "")
            prop_id = prop_id if str(prop_id).startswith("prop:") else f"prop:{prop_id}"
            prop_asset = get(catalog, prop_id)
            if not prop_asset:
                problems.append(f"shot {shot_id}: unknown prop {prop_id}")
            elif prop_asset.get("type") != "prop":
                problems.append(f"shot {shot_id}: {prop_id} is not a prop asset")
            props.append({**prop, "id": prop_id})

        overlays = list(shot.get("overlays") or [])
        for graphic in shot.get("graphics", []) or []:
            graphic = graphic.get("id") if isinstance(graphic, dict) else graphic
            graphic_id = graphic if str(graphic).startswith(("graphic:", "ui:")) else f"graphic:{graphic}"
            asset = get(catalog, graphic_id)
            if not asset:
                problems.append(f"shot {shot_id}: unknown graphic {graphic_id}")
                continue
            if asset.get("type") not in ("motion_graphic", "ui"):
                problems.append(f"shot {shot_id}: {graphic_id} is not a graphic asset")
                continue
            overlay = (asset.get("config") or {}).get("overlay")
            if not isinstance(overlay, dict):
                problems.append(f"shot {shot_id}: {graphic_id} has no renderable overlay")
                continue
            overlays.append({**overlay, "asset": graphic_id})

        shots.append(
            {
                **shot,
                "scene": scene_key,
                "seconds": float(shot.get("seconds", 4)),
                "transitionIn": int(shot.get("transitionIn", spec.get("transitionFrames", 14))),
                "offsetY": shot.get("offsetY", 0),
                "actors": actors,
                "props": props,
                "overlays": overlays,
            }
        )
    if problems:
        return {"ok": False, "problems": problems, "project": None}
    manifest = {
        "id": spec.get("id", "project"),
        "title": spec.get("title", spec.get("id", "project")),
        "logline": spec.get("logline", ""),
        "mode": "LOCAL",
        "style": spec.get("style", "cinematic"),
        "format": {"width": 1080, "height": 1920, "fps": spec.get("fps", default_fps), "aspect": "9:16"},
        "transitionFrames": spec.get("transitionFrames", 14),
        "narration": bool(spec.get("narration", False)),
        "library": spec.get("library", []),
        "shots": shots,
    }
    # The continuity ledger is planning evidence, not render input. Preserve it
    # through catalogue composition so avqa can audit the same manifest that
    # the renderer will consume.
    if "continuity" in spec:
        manifest["continuity"] = spec["continuity"]
    return {"ok": True, "problems": [], "project": manifest}


def fingerprint(catalog: dict, asset_id: str) -> str:
    """Stable short hash of an asset's identity + version, for reuse decisions."""
    a = get(catalog, asset_id)
    if not a:
        return ""
    raw = json.dumps([a["id"], a.get("version"), a.get("config")], sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def reuse_report(project: dict, catalog: dict, root: str = ".") -> dict:
    """Which assets a project refers to, and whether they can be reused as-is."""
    used: list[dict] = []
    missing: list[str] = []
    for shot in project.get("shots", []):
        scene = shot.get("scene", "")
        set_id = f"set:{_slug(scene)}"
        if get(catalog, set_id):
            used.append({"shot": shot["id"], "asset": set_id, "role": "set"})
        else:
            missing.append(f"{shot['id']}: {set_id}")
        for actor in shot.get("actors", []) or []:
            char_key = str(actor.get("id", "")).split(":", 1)[-1]
            char_id = f"character:{char_key}"
            if get(catalog, char_id):
                used.append({"shot": shot["id"], "asset": char_id, "role": "actor"})
            else:
                missing.append(f"{shot['id']}: {char_id}")
            expression = actor.get("expression")
            if expression:
                expr_id = expression if str(expression).startswith("expression:") else f"expression:{expression}"
                if get(catalog, expr_id):
                    used.append({"shot": shot["id"], "asset": expr_id, "role": "expression"})
                else:
                    missing.append(f"{shot['id']}: {expr_id}")
        for prop in shot.get("props", []) or []:
            prop_id = str(prop.get("id", ""))
            prop_id = prop_id if prop_id.startswith("prop:") else f"prop:{prop_id}"
            if get(catalog, prop_id):
                used.append({"shot": shot["id"], "asset": prop_id, "role": "prop"})
            else:
                missing.append(f"{shot['id']}: {prop_id}")
        for graphic in shot.get("graphics", []) or []:
            graphic = graphic.get("id") if isinstance(graphic, dict) else graphic
            graphic_id = str(graphic)
            graphic_id = graphic_id if graphic_id.startswith(("graphic:", "ui:")) else f"graphic:{graphic_id}"
            if get(catalog, graphic_id):
                used.append({"shot": shot["id"], "asset": graphic_id, "role": "graphic"})
            else:
                missing.append(f"{shot['id']}: {graphic_id}")
    uniq = {u["asset"] for u in used}
    return {
        "ok": not missing,
        "reused": sorted(uniq),
        "references": used,
        "missing": missing,
        "new_assets_needed": len(missing),
    }
