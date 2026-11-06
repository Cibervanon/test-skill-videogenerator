"""Representative frame extraction + contact sheets."""

from __future__ import annotations

import os
import subprocess

from .ffmpeg import Tools, run


def grab(tools: Tools, source: str, timestamp: float, dest: str) -> str:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    run(
        [
            tools.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{timestamp:.3f}", "-i", source,
            "-frames:v", "1", "-q:v", "3", dest,
        ]
    )
    return dest


def shot_frames(tools: Tools, source: str, shots: list[dict], out_dir: str, *, per_shot: int = 3) -> list[dict]:
    """Grab `per_shot` frames inside each shot (head / middle / tail).

    Sampling inside the shot rather than on a fixed global grid is what makes
    this 'smart': shot-relative frames always land inside the take, so a 12s
    shot is represented by 3 real moments instead of one arbitrary instant.
    """
    frames = []
    for shot in shots:
        start, end = shot["start"], shot["end"]
        span = max(0.001, end - start)
        positions = [0.12, 0.5, 0.88][:per_shot] if per_shot <= 3 else [
            (i + 1) / (per_shot + 1) for i in range(per_shot)
        ]
        for p in positions:
            t = start + span * p
            name = f"shot{shot['index']:03d}_{int(round(p * 100)):02d}.jpg"
            path = os.path.join(out_dir, name)
            grab(tools, source, t, path)
            frames.append({"shot": shot["index"], "t": round(t, 3), "file": name})
    return frames


def contact_sheet(tools: Tools, frames_dir: str, dest: str, *, columns: int = 4, tile_width: int = 220) -> bool:
    """Tile all extracted frames into a single review sheet (FFmpeg tile filter)."""
    pattern = os.path.join(frames_dir, "shot%03d_%02d.jpg")
    if not os.path.exists(frames_dir):
        return False
    cmd = [
        tools.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-pattern_type", "glob", "-i", pattern,
        "-vf", f"scale={tile_width}:-1,tile={columns}x0:padding=4:margin=4:color=0x101014",
        "-frames:v", "1", dest,
    ]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True)
        return proc.returncode == 0 and os.path.exists(dest)
    except OSError:
        return False
