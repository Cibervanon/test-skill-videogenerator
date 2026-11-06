"""Generated-asset bridge.

The catalogue has one source of truth: ``assets/catalog.json``, rebuilt from the
real render sources.  Assets created through ``asset_forge`` live in
``assets/registry.json`` (versioned) and expose their active render data through
``studio/src/data/generated_assets.json``.  This module is the only place that
knows that bridge, so Python and Remotion cannot drift into two catalogs.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy

DATA_PATH = os.path.join("studio", "src", "data", "generated_assets.json")
REGISTRY_PATH = os.path.join("assets", "registry.json")


def empty() -> dict:
    return {
        "schema": 2,
        "note": "Active render data for assets created by scripts/acs/asset_forge.py. Metadata/versions live in assets/registry.json.",
        "sets": {},
        "characters": {},
        "expressions": {},
        "props": {},
        "graphics": {},
    }


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def load(root: str = ".") -> dict:
    data = read_json(os.path.join(root, DATA_PATH), {}) or {}
    base = empty()
    base.update(data)
    for key in ("sets", "characters", "expressions", "props", "graphics"):
        base[key] = base.get(key) or {}
    return base


def save(root: str, data: dict) -> None:
    write_json(os.path.join(root, DATA_PATH), data)


def merge_cast(root: str, base: dict) -> dict:
    """Return a copy of a cast file with generated characters merged in.

    Canonical characters always win on an id collision: generated assets may add
    identities, but they can never silently replace the existing cast.
    """
    merged = deepcopy(base or {})
    characters = dict(merged.get("characters") or {})
    generated = load(root).get("characters") or {}
    for key, spec in generated.items():
        characters.setdefault(key, spec)
    merged["characters"] = characters
    return merged


def empty_registry() -> dict:
    return {
        "schema": 2,
        "note": "Versioned metadata for hand-authored and forged assets. The derived catalogue merges these entries; it never replaces them.",
        "assets": [],
    }


def load_registry(root: str = ".") -> dict:
    data = read_json(os.path.join(root, REGISTRY_PATH), {}) or empty_registry()
    data.setdefault("schema", 2)
    data.setdefault("assets", [])
    return data


def save_registry(root: str, data: dict) -> None:
    write_json(os.path.join(root, REGISTRY_PATH), data)
