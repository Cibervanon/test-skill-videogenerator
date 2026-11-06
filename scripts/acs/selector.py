"""Automatic production-strategy selection.

For every element of the film the engine must answer one question:
    can this be produced by code, reused from an existing asset, or does it
    genuinely need external generation?

The rules are explicit, auditable and deterministic. External generation is
only ever selected when the mode allows it *and* the element cannot be
expressed procedurally within quality limits.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any

MODES = ("local", "hybrid", "premium")

#: Elements the LOCAL engine can produce end-to-end with code.
CODE_NATIVE = {
    "character": "vector rig (SVG) + procedural performance presets",
    "environment": "vector set + parallax layers + procedural atmosphere",
    "prop": "vector shape drawn from the project bible",
    "camera": "transform curves (dolly/pan/tilt/crane/drift)",
    "motion": "frame-driven acting presets (idle, walk, dig, blink, breath)",
    "caption": "burned-in typographic layer, word-chunked",
    "transition": "frame-accurate crossfade / cut",
    "title": "typographic layout",
    "music": "procedural score (additive synthesis, deterministic)",
    "ambience": "filtered noise beds + event foley (deterministic)",
    "edit": "FFmpeg assembly + loudness normalisation",
}

#: Elements where code alone cannot reach photographic fidelity.
EXTERNAL_ONLY = {
    "photoreal_face": "needs a trained generator or real footage",
    "photoreal_human_motion": "needs performance capture or a video model",
    "licensed_voice": "needs a TTS/voice-cloning provider with a licence",
    "photoreal_environment": "needs photography or a diffusion model",
    "archive_footage": "needs a licensed footage source",
}


@dataclass
class Decision:
    element: str
    kind: str
    strategy: str  # code | reuse | external
    reason: str
    provider: str | None = None
    estimated_cost_usd: float = 0.0
    quality_risk: str = "low"

    def to_dict(self) -> dict:
        return asdict(self)


def _asset_index(assets_dir: str) -> dict[str, str]:
    """Map fingerprint -> path for reusable assets (identity is the fingerprint)."""
    index: dict[str, str] = {}
    if not assets_dir or not os.path.isdir(assets_dir):
        return index
    for root, _dirs, files in os.walk(assets_dir):
        for name in files:
            if name.endswith(".json"):
                try:
                    with open(os.path.join(root, name), "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except (OSError, json.JSONDecodeError):
                    continue
                fingerprint = data.get("fingerprint")
                if fingerprint:
                    index[fingerprint] = os.path.join(root, name)
    return index


def choose(
    *,
    element: str,
    kind: str,
    mode: str,
    spec: dict[str, Any] | None = None,
    assets_dir: str | None = None,
    provider: str | None = None,
    provider_cost_usd: float = 0.0,
    allow_external: bool = False,
) -> Decision:
    """Decide how one element will be produced."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    spec = spec or {}

    # 1. Reuse always wins: a correct existing asset is cheaper and more
    #    consistent than regenerating anything.
    fingerprint = spec.get("fingerprint")
    if fingerprint:
        found = _asset_index(assets_dir or "").get(fingerprint)
        if found:
            return Decision(
                element=element,
                kind=kind,
                strategy="reuse",
                reason=f"asset with matching fingerprint already exists ({found})",
                quality_risk="low",
            )

    # 2. Local code production whenever the capability exists.
    if kind in CODE_NATIVE:
        return Decision(
            element=element,
            kind=kind,
            strategy="code",
            reason=f"producible procedurally: {CODE_NATIVE[kind]}",
            quality_risk="low",
        )

    # 3. External-only elements.
    if kind in EXTERNAL_ONLY:
        if mode == "local":
            return Decision(
                element=element,
                kind=kind,
                strategy="code",
                reason=(
                    "LOCAL mode: external generation disabled by configuration. "
                    f"Fallback is a stylised procedural stand-in; fidelity ceiling: {EXTERNAL_ONLY[kind]}"
                ),
                quality_risk="high",
            )
        if not allow_external:
            return Decision(
                element=element,
                kind=kind,
                strategy="code",
                reason="external generation available but not authorised for this run",
                quality_risk="high",
            )
        return Decision(
            element=element,
            kind=kind,
            strategy="external",
            reason=f"requires external generation: {EXTERNAL_ONLY[kind]}",
            provider=provider,
            estimated_cost_usd=provider_cost_usd,
            quality_risk="medium",
        )

    # 4. Unknown kinds are never silently upgraded to a paid provider.
    return Decision(
        element=element,
        kind=kind,
        strategy="code",
        reason="unknown element kind: defaulting to procedural output (no external spend)",
        quality_risk="medium",
    )


def plan_project(
    project: dict, *, mode: str, assets_dir: str | None = None, allow_external: bool = False
) -> tuple[list[dict], dict]:
    """Derive the strategy for every shot of a project manifest."""
    decisions: list[Decision] = []
    for shot in project.get("shots", []):
        decisions.append(
            choose(element=f"{shot['id']}.environment", kind="environment", mode=mode, assets_dir=assets_dir, allow_external=allow_external)
        )
        for actor in shot.get("actors", []):
            decisions.append(
                choose(
                    element=f"{shot['id']}.{actor['id']}",
                    kind="character",
                    mode=mode,
                    spec={"fingerprint": actor.get("fingerprint")},
                    assets_dir=assets_dir,
                    allow_external=allow_external,
                )
            )
        decisions.append(choose(element=f"{shot['id']}.camera", kind="camera", mode=mode, allow_external=allow_external))
        decisions.append(choose(element=f"{shot['id']}.caption", kind="caption", mode=mode, allow_external=allow_external))
    decisions.append(choose(element="film.music", kind="music", mode=mode, allow_external=allow_external))
    decisions.append(choose(element="film.ambience", kind="ambience", mode=mode, allow_external=allow_external))
    decisions.append(choose(element="film.edit", kind="edit", mode=mode, allow_external=allow_external))

    counts: dict[str, int] = {}
    for d in decisions:
        counts[d.strategy] = counts.get(d.strategy, 0) + 1
    return [d.to_dict() for d in decisions], counts
