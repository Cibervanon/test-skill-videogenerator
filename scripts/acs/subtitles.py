"""SRT from real word timings.

Captions follow the same clock the cut uses. When the timings come from Kokoro's
duration predictor, they are the model's own numbers; when they come from the
LOCAL plan they are estimates. Either way this module does not invent a time:
it groups words and writes their first start and last end.
"""

from __future__ import annotations


def _stamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def group_words(words: list[dict], max_words: int = 3, max_chars: int = 42, min_seconds: float = 0.5) -> list[dict]:
    cues: list[dict] = []
    current: list[dict] = []
    for word in words:
        candidate = current + [word]
        text = " ".join(w["w"] for w in candidate)
        if current and (len(candidate) > max_words or len(text) > max_chars):
            cues.append(_cue(current, min_seconds))
            current = [word]
        else:
            current = candidate
    if current:
        cues.append(_cue(current, min_seconds))
    return cues


def _cue(group: list[dict], min_seconds: float) -> dict:
    start = float(group[0]["s"])
    end = max(float(group[-1]["e"]), start + min_seconds)
    return {"start": round(start, 3), "end": round(end, 3), "text": " ".join(w["w"] for w in group)}


def to_srt(cues: list[dict]) -> str:
    blocks = []
    for i, cue in enumerate(cues, 1):
        blocks.append(f"{i}\n{_stamp(cue['start'])} --> {_stamp(cue['end'])}\n{cue['text']}\n")
    return "\n".join(blocks)


def from_plan(plan: dict, **kwargs) -> list[dict]:
    """Cues for the spoken lines only, sorted by start; gaps stay gaps."""
    words = []
    for line in plan.get("lines", []):
        words.extend(line.get("words") or [])
    words.sort(key=lambda w: float(w["s"]))
    return group_words(words, **kwargs)
