"""LOCAL providers: real, deterministic, zero-cost implementations.

These are not placeholders for a paid service — they *are* the production path
in LOCAL mode. Nothing here performs network I/O, and nothing claims to create
photographic imagery.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

from .base import CostModel, Provider, ProviderError, ProviderRequest, ProviderResult, CostGuard


class LocalVectorArtProvider(Provider):
    """Renders a deterministic SVG art card (title card / prop reference).

    This is genuinely useful (style frames, title plates, colour keys) and it is
    honest: the output is vector typography and shapes, not generated imagery.
    """

    name = "local-vector-art"
    capability = "image.still"
    min_mode = "local"
    is_external = False
    cost_model = CostModel("image", 0.0, "procedural SVG, no network")

    def is_available(self) -> tuple[bool, str]:
        return True, "always available"

    def run(self, request: ProviderRequest, guard: CostGuard) -> ProviderResult:
        guard.check(0.0, is_external=False)
        dest = request.destination
        if not dest:
            raise ProviderError("local-vector-art requires request.destination")
        width = int(request.params.get("width", 1080))
        height = int(request.params.get("height", 1920))
        title = (request.params.get("title") or request.prompt or "UNTITLED").upper()
        palette = request.params.get("palette") or ["#101733", "#3b3f74", "#ffb765"]
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{palette[0]}"/><stop offset="100%" stop-color="{palette[1]}"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect x="{width * 0.08:.0f}" y="{height * 0.42:.0f}" width="{width * 0.84:.0f}" height="2" fill="{palette[2]}" opacity="0.7"/>
  <text x="50%" y="{height * 0.5:.0f}" text-anchor="middle"
        font-family="Georgia, serif" font-size="{int(width * 0.085)}" fill="#fdf6ea"
        letter-spacing="{int(width * 0.006)}">{title}</text>
  <text x="50%" y="{height * 0.55:.0f}" text-anchor="middle"
        font-family="Trebuchet MS, sans-serif" font-size="{int(width * 0.026)}" fill="#c9d3e8"
        opacity="0.8">AI CINEMATIC STUDIO · LOCAL MODE</text>
</svg>
"""
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(svg)
        return ProviderResult(
            provider=self.name,
            capability=self.capability,
            ok=True,
            outputs=[dest],
            meta={"format": "svg", "procedural": True, "bytes": len(svg)},
        )


class LocalProceduralAudioProvider(Provider):
    """Procedural score / ambience / foley, synthesised in-process."""

    name = "local-procedural-audio"
    capability = "audio.score"
    min_mode = "local"
    is_external = False
    cost_model = CostModel("track", 0.0, "additive synthesis, no samples, no network")

    def is_available(self) -> tuple[bool, str]:
        return True, "always available (stdlib synthesis)"

    def run(self, request: ProviderRequest, guard: CostGuard) -> ProviderResult:
        from .. import audio_gen

        dest = request.destination
        if not dest:
            raise ProviderError("local-procedural-audio requires request.destination")
        spec = request.params.get("spec")
        if not spec:
            project_path = request.params.get("project")
            if not project_path:
                raise ProviderError("provide params.spec or params.project")
            with open(project_path, "r", encoding="utf-8") as fh:
                spec = audio_gen.spec_from_project(json.load(fh))
        track, report = audio_gen.build(spec, seed=int(request.params.get("seed", 20261103)))
        track.write(dest)
        return ProviderResult(
            provider=self.name,
            capability=self.capability,
            ok=True,
            outputs=[dest],
            meta=report,
        )


class LocalRemotionRenderProvider(Provider):
    """Renders the Remotion composition to MP4 with the project's own toolchain."""

    name = "local-remotion"
    capability = "video.render"
    min_mode = "local"
    is_external = False
    cost_model = CostModel("render", 0.0, "local CPU render via Remotion + headless Chrome")

    def __init__(self, studio_dir: str):
        self.studio_dir = studio_dir

    def is_available(self) -> tuple[bool, str]:
        if not os.path.isdir(self.studio_dir):
            return False, f"studio directory not found: {self.studio_dir}"
        if not os.path.isdir(os.path.join(self.studio_dir, "node_modules")):
            return False, "studio dependencies not installed (run: cd studio && npm install)"
        return True, "ready"

    def run(self, request: ProviderRequest, guard: CostGuard) -> ProviderResult:
        dest = request.destination
        if not dest:
            raise ProviderError("local-remotion requires request.destination")
        entry = request.params.get("entry", "src/index.ts")
        comp = request.params.get("composition", "CinematicDemo")
        extra = request.params.get("args", [])
        log_path = request.params.get("log")
        cmd = ["npx", "remotion", "render", entry, comp, os.path.abspath(dest), "--log=warn", *extra]
        started = time.time()
        if log_path:
            # Remotion can take tens of minutes. Keep its progress on disk while
            # it runs instead of hiding everything in an in-memory pipe; otherwise
            # a slow render and a hung render look identical to the caller.
            log_path = os.path.abspath(log_path)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w", encoding="utf-8", errors="replace") as log:
                log.write(f"$ {' '.join(cmd)}\n")
                log.flush()
                proc = subprocess.run(
                    cmd,
                    cwd=self.studio_dir,
                    shell=(os.name == "nt"),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
        else:
            proc = subprocess.run(
                cmd,
                cwd=self.studio_dir,
                shell=(os.name == "nt"),
                capture_output=True,
                text=True,
            )
        if proc.returncode != 0:
            if log_path and os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
                    tail = "\n".join(fh.read().strip().splitlines()[-12:])
            else:
                tail = "\n".join((proc.stderr or proc.stdout or "").strip().splitlines()[-12:])
            raise ProviderError(f"remotion render failed ({proc.returncode}):\n{tail}")
        return ProviderResult(
            provider=self.name,
            capability=self.capability,
            ok=True,
            outputs=[dest],
            meta={"seconds": round(time.time() - started, 2), "composition": comp, "entry": entry, "log": log_path},
        )


def register(registry) -> None:
    """Register every local provider into a Registry."""
    registry.add(LocalVectorArtProvider())
    registry.add(LocalProceduralAudioProvider())
    registry.add(LocalRemotionRenderProvider(registry.config.get("studio_dir", "studio")))
    if sys.platform == "win32":
        # Kept explicit: rendering works on Windows, only the shell quirk differs.
        registry.note("local-remotion", "Windows: command is executed through the shell")
