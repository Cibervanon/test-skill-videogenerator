"""External provider adapters (HYBRID / PREMIUM).

These classes define the *contract* for paid generation. Only adapters whose
HTTP contract has actually been verified should set `implemented = True` and
perform network calls. In this build none are verified, so every adapter:

  * reports `is_available()` based on the presence of its API key,
  * refuses to run with `ProviderUnavailable`/`ProviderError` instead of
    returning invented output or silently falling back.

That is deliberate: a stubbed adapter that pretends to generate is worse than
no adapter at all. Each entry documents the env var to set and what has to be
verified before it can be enabled.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .base import CostModel, CostGuard, Provider, ProviderError, ProviderRequest, ProviderResult


@dataclass(frozen=True)
class ExternalSpec:
    key: str
    name: str
    capability: str
    env_var: str
    docs: str
    pricing_note: str
    verified: bool = False
    implemented: bool = False


CATALOG: dict[str, ExternalSpec] = {
    "image.flux": ExternalSpec(
        key="image.flux",
        name="FLUX (via a hosted endpoint or local ComfyUI)",
        capability="image.still",
        env_var="FLUX_API_KEY",
        docs="https://github.com/black-forest-labs/flux",
        pricing_note="self-hosted (GPU cost) or per-image via a hosting provider",
        verified=False,
        implemented=False,
    ),
    "video.generic": ExternalSpec(
        key="video.generic",
        name="Image-to-video model (Wan / LTX / Kling / Runway / Veo — one adapter each)",
        capability="video.clip",
        env_var="VIDEO_API_KEY",
        docs="https://github.com/Wan-Video/Wan2.1",
        pricing_note="model dependent; per-second billing on hosted APIs",
        verified=False,
        implemented=False,
    ),
    "tts.generic": ExternalSpec(
        key="tts.generic",
        name="TTS / voice-cloning provider (ElevenLabs, XTTS, Piper locally)",
        capability="audio.voice",
        env_var="TTS_API_KEY",
        docs="https://github.com/coqui-ai/TTS",
        pricing_note="per character on hosted APIs; free when self-hosted",
        verified=False,
        implemented=False,
    ),
}


class ExternalProvider(Provider):
    """Base class for a paid adapter. Must be subclassed and verified."""

    is_external = True
    spec: ExternalSpec

    def __init__(self):
        self.name = self.spec.key
        self.capability = self.spec.capability
        self.min_mode = "hybrid"

    def is_available(self) -> tuple[bool, str]:
        if not self.spec.implemented:
            return False, (
                f"adapter not implemented in this build (contract unverified). "
                f"Set {self.spec.env_var} and implement the HTTP contract before enabling."
            )
        if not os.environ.get(self.spec.env_var):
            return False, f"missing environment variable {self.spec.env_var}"
        return True, "ready"

    def run(self, request: ProviderRequest, guard: CostGuard) -> ProviderResult:
        available, reason = self.is_available()
        if not available:
            raise ProviderError(f"{self.name}: {reason}")
        raise ProviderError(
            "External adapters are disabled in this build. Implement the verified HTTP "
            "contract in providers/external.py and record it in MODEL_COMPARISON.md first."
        )


class FluxImageProvider(ExternalProvider):
    spec = CATALOG["image.flux"]
    cost_model = CostModel("image", 0.04, "example estimate; verify with the provider's current pricing")


class GenericVideoProvider(ExternalProvider):
    spec = CATALOG["video.generic"]
    cost_model = CostModel("clip", 0.35, "example estimate; verify per model and duration")


class GenericTTSProvider(ExternalProvider):
    spec = CATALOG["tts.generic"]
    cost_model = CostModel("1000_chars", 0.15, "example estimate; verify with the provider")


def register(registry) -> None:
    for provider in (FluxImageProvider(), GenericVideoProvider(), GenericTTSProvider()):
        registry.add(provider)


def catalog_report() -> list[dict]:
    return [
        {
            "key": s.key,
            "name": s.name,
            "capability": s.capability,
            "env_var": s.env_var,
            "docs": s.docs,
            "pricing_note": s.pricing_note,
            "verified": s.verified,
            "implemented": s.implemented,
        }
        for s in CATALOG.values()
    ]
