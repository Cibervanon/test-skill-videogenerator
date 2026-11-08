"""Word-timed burned-in captions.

The SRT is timed from the take. The renderer used to ignore that clock and
distribute caption chunks by character weight, so a three-word chunk could
appear before its first word was spoken. This module carries the same word
timings into the manifest, in shot-local seconds, so `Subtitles.buildCues` can
reveal each chunk on the word that actually opens it.

It is deliberately a data transform: it does not synthesise, does not guess a
missing timing and refuses a stale plan whose text no longer matches the shot.
"""

from __future__ import annotations

import copy

from . import edit, subtitles


def attach(project: dict, plan: dict, *, max_words: int = 3) -> dict:
    """Return a copy of `project` with `shot.captions` from the take clock.

    Cue times are shot-local seconds. The shot window is computed with the same
    timeline rule as `composition/Demo.tsx` (`edit.shot_windows`), so a cue is
    not shifted by the renderer's dissolve overlap.
    """
    result = copy.deepcopy(project)
    windows = {window["id"]: window for window in edit.shot_windows(project)}
    shots = {shot["id"]: shot for shot in result.get("shots") or []}
    problems: list[str] = []
    warnings: list[str] = []
    timed_shots = 0
    cue_count = 0

    for line in plan.get("lines") or []:
        shot_id = line.get("shot")
        shot = shots.get(shot_id)
        if shot is None:
            problems.append(f"{shot_id}: voice plan references a shot that is not in the manifest")
            continue
        words = sorted(line.get("words") or [], key=lambda word: float(word["s"]))
        if not words:
            warnings.append(f"{shot_id}: no word timings; the caption keeps the character-weighted fallback")
            continue
        text = str(line.get("text") or "").strip()
        manifest_line = str(shot.get("line") or "").strip()
        if text != manifest_line:
            problems.append(
                f"{shot_id}: voice plan text does not match the manifest line; regenerate the plan or the manifest"
            )
            continue

        window = windows.get(shot_id)
        if window is None:
            problems.append(f"{shot_id}: shot window is missing from the timeline")
            continue
        shot_start = float(window["start"])
        duration = float(shot["seconds"])
        cues = []
        for cue in subtitles.group_words(words, max_words=max_words):
            start = float(cue["start"]) - shot_start
            end = float(cue["end"]) - shot_start
            # A cue that starts before the shot is clipped, not moved: the word
            # is already sounding under the previous picture.
            start = max(0.0, start)
            end = min(duration, end)
            if end <= start:
                continue
            cues.append({"text": cue["text"], "start": round(start, 3), "end": round(end, 3)})
        if not cues:
            problems.append(f"{shot_id}: word timings fall outside the shot window")
            continue
        shot["captions"] = cues
        timed_shots += 1
        cue_count += len(cues)

    return {
        "ok": not problems,
        "project": result,
        "shots": timed_shots,
        "cues": cue_count,
        "problems": problems,
        "warnings": warnings,
        "method": (
            "voice_plan word timings -> subtitles.group_words -> shot-local seconds, using the "
            "renderer's own shot timeline. No estimated times are invented."
        ),
    }


def max_reveal_error(project: dict, plan: dict) -> float:
    """Largest gap between a cue's first word and its rendered reveal, in seconds.

    This is the acceptance measurement for the 120 ms gate: it compares the
    manifest cue start with the take's real word start, not with another copy of
    the same estimate.
    """
    windows = {window["id"]: window for window in edit.shot_windows(project)}
    shots = {shot["id"]: shot for shot in project.get("shots") or []}
    worst = 0.0
    for line in plan.get("lines") or []:
        shot = shots.get(line.get("shot"))
        window = windows.get(line.get("shot"))
        if not shot or not window or not shot.get("captions"):
            continue
        words = [float(word["s"]) for word in line.get("words") or []]
        if not words:
            continue
        cues = shot["captions"]
        manifest_cues = " ".join(cue["text"] for cue in cues).split()
        plan_words = [str(word["w"]) for word in line.get("words") or []]
        if manifest_cues != plan_words:
            continue
        cursor = 0
        for cue in cues:
            count = len(cue["text"].split())
            word_start = words[cursor] - float(window["start"])
            worst = max(worst, abs(float(cue["start"]) - max(0.0, word_start)))
            cursor += count
    return round(worst, 4)
