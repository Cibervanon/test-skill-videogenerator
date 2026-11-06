"""Global motion estimation (pan / tilt magnitude) without OpenCV.

Method: decode at low resolution, convert to 8-bit luma, then search the best
integer shift (-R..R) minimising SAD between consecutive frames. This recovers
dominant camera translation (pan/tilt) and residual motion energy (subject and
ambient animation). It is a *translation* model: it does not recover zoom,
rotation or parallax depth, and is reported as a heuristic.
"""

from __future__ import annotations

from .ffmpeg import Tools, read_video, iter_frames

RADIUS = 6


def _luma(frame: bytes, width: int, height: int) -> list[int]:
    out = [0] * (width * height)
    for i in range(width * height):
        j = i * 3
        out[i] = (frame[j] * 299 + frame[j + 1] * 587 + frame[j + 2] * 114) // 1000
    return out


def _sad(a: list[int], b: list[int], width: int, height: int, dx: int, dy: int) -> float:
    total = 0
    count = 0
    for y in range(RADIUS, height - RADIUS):
        for x in range(RADIUS, width - RADIUS):
            total += abs(a[y * width + x] - b[(y + dy) * width + (x + dx)])
            count += 1
    return total / max(1, count)


def _mean_diff(a: list[int], b: list[int]) -> float:
    if not a:
        return 0.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def analyze(tools: Tools, path: str, *, fps: float = 3.0, width: int = 72) -> dict:
    width -= width % 2
    height = int(round(width * 16 / 9))
    height -= height % 2
    raw = read_video(tools, path, fps=fps, width=width, height=height)
    frames = [_luma(f, width, height) for f in iter_frames(raw, width, height)]
    if len(frames) < 2:
        return {"samples": len(frames), "note": "not enough frames"}

    shifts = []
    energies = []
    for prev, cur in zip(frames, frames[1:]):
        energy = _mean_diff(prev, cur)
        energies.append(energy)
        best = (0, 0, 1e9)
        for dy in range(-RADIUS, RADIUS + 1):
            for dx in range(-RADIUS, RADIUS + 1):
                if abs(dx) + abs(dy) > RADIUS:
                    continue
                score = _sad(prev, cur, width, height, dx, dy)
                if score < best[2]:
                    best = (dx, dy, score)
        shifts.append({"dx": best[0], "dy": best[1]})

    pan = sum(1 for s in shifts if s["dx"] != 0)
    tilt = sum(1 for s in shifts if s["dy"] != 0)
    moving = sum(1 for e in energies if e > 2.0)
    abs_pan = sorted(abs(s["dx"]) for s in shifts)
    abs_tilt = sorted(abs(s["dy"]) for s in shifts)

    return {
        "method": f"SAD translation search ±{RADIUS}px on {width}x{height} luma @{fps}fps",
        "samples": len(frames),
        "pairs": len(shifts),
        "mean_motion_energy": round(sum(energies) / len(energies), 3),
        "median_motion_energy": round(sorted(energies)[len(energies) // 2], 3),
        "moving_ratio": round(moving / len(energies), 3),
        "pan_ratio": round(pan / len(shifts), 3),
        "tilt_ratio": round(tilt / len(shifts), 3),
        "median_abs_pan_px": abs_pan[len(abs_pan) // 2],
        "median_abs_tilt_px": abs_tilt[len(abs_tilt) // 2],
        "shift_samples": shifts[:120],
        "limits": "translation-only model; zoom/rotation/parallax not measured",
    }
