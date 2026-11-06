"""Is the dialogue clear of the score? (Port of the external repo's mixcheck idea.)

Computes 0.4 s windows over the stems and flags the moments where music or
effects come within ``margin`` dB of the voice. In LOCAL mode there is no
speech stem, so the check reports itself as not applicable instead of passing
silently: a gate that cannot run must say so.
"""

from __future__ import annotations

import os
import subprocess
import wave

import numpy as np

SR = 44100


def _decode(path: str) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def _db(x: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(x**2)) + 1e-9)


def find_voice_stem(project_dir: str) -> str | None:
    for name in ("voice.wav", "voice.mp3"):
        path = os.path.join(project_dir, "generation", "voice", name)
        if os.path.exists(path):
            return path
    return None


def find_bed_stem(project_dir: str) -> str:
    """The music the voice has to sit on: the ducked bed if it exists.

    Never the final mix: that contains the voice, and comparing the voice with
    itself would flag every window.
    """
    ducked = os.path.join(project_dir, "generation", "audio", "music_ducked.wav")
    return ducked if os.path.exists(ducked) else os.path.join(project_dir, "generation", "audio", "score.wav")


def check(project_dir: str, *, margin: float = 3.0, window: float = 0.4) -> dict:
    voice_path = find_voice_stem(project_dir)
    score_path = find_bed_stem(project_dir)
    if not voice_path:
        return {
            "applicable": False,
            "reason": "no speech stem: LOCAL mode writes word timings only (see generation/voice/voice_plan.json)",
            "flags": [],
        }
    if not os.path.exists(score_path):
        return {"applicable": False, "reason": "no score to compare against", "flags": []}
    bed = os.path.basename(score_path)

    voice, score = _decode(voice_path), _decode(score_path)
    n = min(len(voice), len(score))
    w = int(window * SR)
    if n < w:
        return {"applicable": False, "reason": "stems shorter than one window", "flags": []}

    flags = []
    levels = [(_db(voice[i : i + w]), i) for i in range(0, n - w, w // 2)]
    audible = [lv for lv, _ in levels if lv > -60]
    speaking = (float(np.percentile(audible, 70)) - 8) if audible else -60.0
    for level, i in levels:
        if level < speaking:
            continue
        other = _db(score[i : i + w])
        if other > level - margin:
            flags.append({"at": round(i / SR, 2), "stem": "score", "db_over_voice": round(other - level, 1)})
    return {
        "applicable": True,
        "bed": bed,
        "margin_db": margin,
        "speaking_threshold_db": round(speaking, 1),
        "flags": flags,
        "peak": round(float(np.abs(voice[:n] + score[:n]).max()), 3),
    }


def to_markdown(result: dict) -> str:
    if not result.get("applicable"):
        return f"# Mix check\n\nNot applicable: {result.get('reason')}\n"
    rows = "\n".join(
        f"| {f['at']:.1f} | {f['stem']} | {f['db_over_voice']:+.1f} |" for f in result["flags"][:40]
    ) or "| — | — | — |"
    return (
        "# Mix check\n\n"
        f"Bed analysed: {result.get('bed', 'score.wav')}. "
        f"Windows where it comes within {result['margin_db']:g} dB of the voice: "
        f"{len(result['flags'])}\n\n"
        "| time (s) | stem | dB over the voice |\n|---|---|---|\n" + rows + "\n"
    )
