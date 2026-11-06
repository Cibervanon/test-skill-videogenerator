"""Audio measurements: loudness, RMS envelope, speech/voice activity, silence.

Uses FFmpeg for decoding and the standard library for the maths, so results are
reproducible and require no numpy/scipy.
"""

from __future__ import annotations

import array
import math

from .ffmpeg import Tools, read_pcm, run


def loudness(tools: Tools, path: str) -> dict:
    proc = run([tools.ffmpeg, "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    text = proc.stderr.decode("utf-8", "replace")
    out = {}
    for key in ("mean_volume", "max_volume"):
        for line in text.splitlines():
            if key in line:
                try:
                    out[key + "_db"] = float(line.split(key + ":")[1].split("dB")[0].strip())
                except (IndexError, ValueError):
                    pass
    return out


def rms_envelope(tools: Tools, path: str, *, sample_rate: int = 8000, block: float = 0.25) -> list[dict]:
    raw = read_pcm(tools, path, sample_rate=sample_rate)
    samples = array.array("h")
    samples.frombytes(raw[: len(raw) - (len(raw) % 2)])
    step = max(1, int(sample_rate * block))
    env = []
    for start in range(0, len(samples) - step + 1, step):
        chunk = samples[start: start + step]
        acc = 0
        for s in chunk:
            acc += s * s
        rms = math.sqrt(acc / len(chunk)) / 32768.0
        db = 20 * math.log10(rms) if rms > 0 else -90.0
        env.append({"t": round(start / sample_rate, 2), "rms_db": round(db, 1)})
    return env


def voice_activity(env: list[dict], *, floor_db: float = -42.0, margin_db: float = 8.0) -> dict:
    """Heuristic voice/music activity detector.

    A block counts as 'active' when it is above an absolute noise floor AND
    above (median + margin). This separates continuous music beds from the
    louder, dynamic dialogue band, but it cannot *identify* a speaker: it is a
    level-based heuristic and is reported as such.
    """
    levels = sorted(b["rms_db"] for b in env)
    if not levels:
        return {"segments": [], "active_ratio": 0.0, "median_db": None, "note": "no audio"}
    median = levels[len(levels) // 2]
    p90 = levels[int(len(levels) * 0.9)]
    # Relative gate: an absolute dBFS threshold cannot separate speech from a
    # loud music bed, and a fixed median+offset gate climbs above the peaks the
    # moment the mix is compressed. Anchor on the 90th percentile instead and
    # keep a hard ceiling just under it.
    threshold = max(floor_db, median + (p90 - median) * 0.45)
    threshold = min(threshold, max(floor_db, p90 - 1.0))
    segments = []
    current = None
    for b in env:
        active = b["rms_db"] >= threshold
        if active and current is None:
            current = {"start": b["t"], "end": b["t"]}
        elif active and current is not None:
            current["end"] = b["t"]
        elif not active and current is not None:
            if current["end"] - current["start"] >= 0.5:
                segments.append({k: round(v, 2) for k, v in current.items()})
            current = None
    if current and current["end"] - current["start"] >= 0.5:
        segments.append({k: round(v, 2) for k, v in current.items()})
    total = max(1e-6, env[-1]["t"] - env[0]["t"] + 0.25)
    active_time = sum(s["end"] - s["start"] for s in segments)
    gaps = [
        {"start": segments[i]["end"], "end": segments[i + 1]["start"]}
        for i in range(len(segments) - 1)
        if segments[i + 1]["start"] - segments[i]["end"] >= 0.35
    ]
    return {
        "method": "rms envelope @8kHz, gate = median + 0.45*(p90-median), clamped under p90",
        "median_db": round(median, 1),
        "gate_db": round(threshold, 1),
        "active_ratio": round(active_time / total, 3),
        "segments": segments,
        "gaps": gaps,
        "note": "level-based heuristic: detects activity, not speaker identity or language",
    }


def analyze(tools: Tools, path: str) -> dict:
    env = rms_envelope(tools, path)
    return {
        "loudness": loudness(tools, path),
        "envelope_blocks": len(env),
        "envelope": env,
        "activity": voice_activity(env),
    }
