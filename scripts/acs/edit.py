"""Word-guided editing, without a voice provider.

The external repository cuts the picture on the spoken word. That needs real
timings; we have them either from an ElevenLabs alignment (not called here) or
from the LOCAL plan in `generation/voice/words.json`. This module does the part
that does not need audio:

* `cues(words)`            — the timeline of spoken words, in seconds and frames
* `align_manifest(project, words)` — stretches or trims each shot so its caption
  starts on a word, and reports the drift it had to absorb
* `caption_cues(project)`  — per-shot caption windows derived from the aligned
  manifest, so the burned-in text and the narration cannot disagree

The alignment never changes the number of shots: it moves the boundaries the
script already justifies. A shot that would have to move more than `tolerance`
seconds is reported instead of silently rewritten.
"""

from __future__ import annotations

import json
import os


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cues(words: list[dict], fps: int = 30) -> list[dict]:
    return [
        {"w": w["w"], "s": float(w["s"]), "e": float(w["e"]), "frame": round(float(w["s"]) * fps)}
        for w in words
    ]


def shot_windows(project: dict) -> list[dict]:
    fps = project["format"]["fps"]
    default = project.get("transitionFrames", 0)
    shots = project["shots"]
    cursor = 0
    out = []
    for i, shot in enumerate(shots):
        frames = round(shot["seconds"] * fps)
        nxt = shots[i + 1].get("transitionIn", default) if i + 1 < len(shots) else 0
        out.append({"id": shot["id"], "from": cursor, "frames": frames, "start": cursor / fps, "end": (cursor + frames) / fps})
        cursor += frames - nxt
    return out


def first_word_after(words: list[dict], t: float) -> dict | None:
    for word in words:
        if float(word["s"]) + 0.001 >= t:
            return word
    return None


def align_manifest(project: dict, words: list[dict], *, tolerance: float = 0.45) -> dict:
    """Nudge each shot boundary so its first word lands at the cut.

    Returns a copy of the project plus a report. `seconds` is adjusted by the
    drift between the authored cut and the word that should open the shot; the
    total duration is preserved by giving the difference back to the last shot.
    """
    fps = project["format"]["fps"]
    shots = [dict(s) for s in project["shots"]]
    windows = shot_windows(project)
    shifts: list[dict] = []
    total_shift = 0.0

    for i in range(1, len(shots)):
        window = windows[i]
        word = first_word_after(words, window["start"])
        if not word:
            continue
        drift = float(word["s"]) - window["start"]
        if abs(drift) <= 0.02:
            shifts.append({"shot": shots[i]["id"], "drift": 0.0, "applied": 0.0})
            continue
        applied = max(-tolerance, min(tolerance, drift))
        # growing shot i-1 pushes shot i later, which is exactly the drift sign
        shots[i - 1]["seconds"] = round(shots[i - 1]["seconds"] + applied, 3)
        total_shift += applied
        shifts.append(
            {
                "shot": shots[i]["id"],
                "word": word["w"],
                "drift": round(drift, 3),
                "applied": round(applied, 3),
                "within_tolerance": abs(drift) <= tolerance,
            }
        )

    if abs(total_shift) > 0.001:
        shots[-1]["seconds"] = round(shots[-1]["seconds"] - total_shift, 3)
    aligned = {**project, "shots": shots}
    return {
        "project": aligned,
        "shifts": shifts,
        "total_shift": round(total_shift, 3),
        "tolerance": tolerance,
        "ok": all(s["within_tolerance"] for s in shifts),
    }


def caption_cues(project: dict) -> list[dict]:
    """Caption windows per shot: start, end and the line, in the aligned clock."""
    windows = shot_windows(project)
    shots = {s["id"]: s for s in project["shots"]}
    out = []
    for window in windows:
        shot = shots[window["id"]]
        line = (shot.get("line") or "").strip()
        if not line:
            continue
        out.append(
            {
                "shot": window["id"],
                "start": round(window["start"], 3),
                "end": round(window["end"], 3),
                "line": line,
                "words": len(line.split()),
            }
        )
    return out
