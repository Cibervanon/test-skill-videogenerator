"""Persistent visual-reference library.

References are *not* renderable assets and therefore do not belong in the asset
catalogue.  They are metadata records that explain why a palette, composition,
lighting choice or motion rule exists, and where it came from.  The forge can
attach selected reference ids to a generated asset; it never loads every
reference for every request.

The library is local-only and provenance/licence checked before a record is
written.  Existing references are never overwritten: a revised reference gets a
new id (or an explicit version field in its metadata).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

PATH = "assets/references.json"
REQUIRED = ("id", "name", "purpose", "source", "license", "provenance")
PURPOSES = {"visual", "character", "background", "movement", "composition", "lighting", "style"}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _read(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def empty() -> dict:
    return {
        "schema": 1,
        "note": "Persistent references, selected per request. Not assets: no reference is rendered directly.",
        "references": [],
    }


def load(root: str = ".") -> dict:
    data = _read(os.path.join(root, PATH), {}) or empty()
    data.setdefault("references", [])
    return data


def save(root: str, data: dict) -> None:
    _write(os.path.join(root, PATH), data)


def add(
    root: str,
    *,
    name: str,
    purpose: str,
    source: str,
    license_: str,
    origin: str = "user-provided",
    tags=(),
    applies_to=(),
    notes: str = "",
    reference_id: str | None = None,
) -> dict:
    if purpose not in PURPOSES:
        raise ValueError(f"reference purpose must be one of {sorted(PURPOSES)}")
    if not license_ or license_ == "unspecified":
        raise ValueError("a reference needs a known licence")
    if not source or not os.path.exists(os.path.join(root, source)):
        raise ValueError(f"reference source does not exist: {source!r}")
    data = load(root)
    rid = reference_id or f"ref:{_slug(name)}"
    if any(r.get("id") == rid for r in data["references"]):
        raise ValueError(f"reference {rid} already exists; use a new id or a new version record")
    record = {
        "id": rid,
        "name": name,
        "purpose": purpose,
        "source": source.replace(os.sep, "/"),
        "license": license_,
        "provenance": {"origin": origin, "date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")},
        "tags": sorted({str(t) for t in tags if t}),
        "applies_to": sorted({str(t) for t in applies_to if t}),
        "notes": notes,
        "status": "active",
    }
    data["references"].append(record)
    save(root, data)
    return record


def search(data: dict, *, query: str | None = None, purpose: str | None = None, tag: str | None = None) -> list[dict]:
    q = (query or "").lower().strip()
    out = []
    for ref in data.get("references", []):
        if purpose and ref.get("purpose") != purpose:
            continue
        if tag and tag.lower() not in [str(t).lower() for t in ref.get("tags", [])]:
            continue
        haystack = " ".join(
            [str(ref.get("id", "")), str(ref.get("name", "")), str(ref.get("purpose", "")),
             str(ref.get("notes", "")), " ".join(map(str, ref.get("tags", [])))]
        ).lower()
        if q and q not in haystack:
            continue
        out.append(ref)
    return out


def select(data: dict, *, purposes=(), tags=(), limit: int = 4) -> list[dict]:
    """Select only relevant references; never attach the whole library."""
    scored = []
    for ref in data.get("references", []):
        if ref.get("status", "active") != "active":
            continue
        score = 0
        if ref.get("purpose") in purposes:
            score += 3
        score += len(set(tags) & set(ref.get("tags", [])))
        if score:
            scored.append((score, ref))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [ref for _, ref in scored[:limit]]


def validate(data: dict, root: str = ".") -> dict:
    problems = []
    ids = [r.get("id") for r in data.get("references", [])]
    for rid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"duplicate reference id: {rid}")
    for ref in data.get("references", []):
        for field in REQUIRED:
            if ref.get(field) in (None, "", [], {}):
                problems.append(f"{ref.get('id')}: missing {field}")
        if ref.get("purpose") not in PURPOSES:
            problems.append(f"{ref.get('id')}: unknown purpose {ref.get('purpose')!r}")
        source = ref.get("source")
        if source and not os.path.exists(os.path.join(root, source)):
            problems.append(f"{ref.get('id')}: missing source {source}")
        if ref.get("license") == "unspecified":
            problems.append(f"{ref.get('id')}: no licence")
    return {"ok": not problems, "checked": len(ids), "problems": problems}
