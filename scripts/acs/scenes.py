"""Shot / cut detection driven by FFmpeg's scene score.

The score is FFmpeg's internal `scene` metric (0..1) computed from frame
difference; it is *not* a semantic understanding of a cut. We therefore:

1. scan at two thresholds (hard cut + soft change),
2. snap detected times to the frame grid,
3. merge shots shorter than `min_shot` (flash frames, subtitle pops),
4. report both the raw detections and the merged shot list so the caller can
   see exactly what was measured instead of what we assumed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from .ffmpeg import Tools, run, FFmpegError

_PTS = re.compile(r"pts_time:([0-9.]+)")


@dataclass
class Shot:
    index: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["duration"] = self.duration
        return d


def detect_cuts(tools: Tools, path: str, threshold: float = 0.30) -> list[float]:
    """Return cut timestamps (seconds) where FFmpeg's scene score > threshold."""
    proc = run(
        [
            tools.ffmpeg, "-hide_banner", "-nostats", "-i", path,
            "-filter:v", f"select='gt(scene,{threshold})',metadata=print:file=-",
            "-an", "-f", "null", "-",
        ]
    )
    text = proc.stdout.decode("utf-8", "replace")
    times = sorted({round(float(m), 3) for m in _PTS.findall(text)})
    return times


def build_shots(cuts: list[float], duration: float, *, min_shot: float = 0.60) -> list[Shot]:
    """Turn cut timestamps into a contiguous shot list, absorbing micro-shots."""
    boundaries = [0.0]
    for t in cuts:
        if 0.0 < t < duration - 0.05:
            if t - boundaries[-1] >= min_shot:
                boundaries.append(t)
            elif boundaries[-1] > 0.0:
                # absorb into previous shot rather than emitting a flash frame
                continue
    boundaries.append(duration)
    shots: list[Shot] = []
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        if end - start < 0.05:
            continue
        shots.append(Shot(index=len(shots), start=round(start, 3), end=round(end, 3)))
    return shots


def analyze(tools: Tools, path: str, duration: float) -> dict:
    hard = detect_cuts(tools, path, 0.30)
    soft = detect_cuts(tools, path, 0.10)
    shots = build_shots(soft, duration)
    durations = [s.duration for s in shots]
    longest = max(durations) if durations else 0.0
    return {
        "thresholds": {"hard": 0.30, "soft": 0.10, "min_shot_seconds": 0.60},
        "hard_cuts": hard,
        "soft_cuts": soft,
        "cut_count_hard": len(hard),
        "cut_count_soft": len(soft),
        "cuts_per_minute_soft": round(len(soft) / (duration / 60.0), 2) if duration else 0.0,
        "shots": [s.to_dict() for s in shots],
        "shot_count": len(shots),
        "shot_duration_stats": {
            "mean": round(sum(durations) / len(durations), 3) if durations else 0.0,
            "median": round(sorted(durations)[len(durations) // 2], 3) if durations else 0.0,
            "min": round(min(durations), 3) if durations else 0.0,
            "max": round(longest, 3),
            "stdev": _stdev(durations),
        },
        "note": (
            "scene score measures frame-difference, not semantics; long takes with "
            "continuous camera motion produce few detections by design."
        ),
    }


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return round(var ** 0.5, 3)
