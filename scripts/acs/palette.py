"""Dominant colour extraction (k-means, deterministic seed, stdlib only)."""

from __future__ import annotations

import colorsys
import random

from .ffmpeg import Tools, read_video, iter_frames


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _kmeans(pixels: list[tuple[int, int, int]], k: int, *, iterations: int = 14, seed: int = 7):
    rng = random.Random(seed)
    centers = [pixels[rng.randrange(len(pixels))] for _ in range(k)]
    for _ in range(iterations):
        buckets: list[list[tuple[int, int, int]]] = [[] for _ in range(k)]
        for p in pixels:
            best, best_d = 0, 1 << 30
            for i, c in enumerate(centers):
                d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                if d < best_d:
                    best, best_d = i, d
            buckets[best].append(p)
        moved = False
        for i, bucket in enumerate(buckets):
            if not bucket:
                continue
            r = sum(p[0] for p in bucket) / len(bucket)
            g = sum(p[1] for p in bucket) / len(bucket)
            b = sum(p[2] for p in bucket) / len(bucket)
            new = (int(r), int(g), int(b))
            if new != centers[i]:
                moved = True
            centers[i] = new
        if not moved:
            break
    counts = [0] * k
    for p in pixels:
        best, best_d = 0, 1 << 30
        for i, c in enumerate(centers):
            d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
            if d < best_d:
                best, best_d = i, d
        counts[best] += 1
    total = max(1, len(pixels))
    out = []
    for c, n in zip(centers, counts):
        h, l, s = colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)
        out.append(
            {
                "hex": _hex(c),
                "share": round(n / total, 4),
                "hue": round(h * 360, 1),
                "lightness": round(l, 3),
                "saturation": round(s, 3),
            }
        )
    out.sort(key=lambda d: d["share"], reverse=True)
    return out


def extract(tools: Tools, path: str, *, fps: float = 1.0, width: int = 48, k: int = 6) -> dict:
    height = int(round(width * 16 / 9))
    raw = read_video(tools, path, fps=fps, width=width, height=height)
    pixels: list[tuple[int, int, int]] = []
    for frame in iter_frames(raw, width - width % 2, height - height % 2):
        # stride sampling keeps k-means fast without changing the distribution much
        for i in range(0, len(frame), 3 * 5):
            pixels.append((frame[i], frame[i + 1], frame[i + 2]))
    if not pixels:
        return {"palette": [], "samples": 0}
    palette = _kmeans(pixels, k)
    mean = tuple(int(sum(p[i] for p in pixels) / len(pixels)) for i in range(3))
    return {
        "palette": palette,
        "mean_hex": _hex(mean),
        "samples": len(pixels),
        "method": f"kmeans(k={k}) on {fps}fps {width}x{height} rgb24 decode, deterministic seed",
    }


def contrast_profile(palette: list[dict]) -> dict:
    """Rough tonal spread: how much of the frame is dark / mid / light."""
    buckets = {"shadow": 0.0, "mid": 0.0, "highlight": 0.0}
    for entry in palette:
        l = entry["lightness"]
        key = "shadow" if l < 0.32 else "highlight" if l > 0.66 else "mid"
        buckets[key] += entry["share"]
    return {k: round(v, 4) for k, v in buckets.items()}
