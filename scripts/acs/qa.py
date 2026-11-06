"""Quality gates for a finished cut.

Each check is a measurement with an explicit threshold. Thresholds here are
*calibrated against this engine's own output* (see TEST_REPORT.md); they are
gates that catch regressions, not an objective quality score of cinema.
"""

from __future__ import annotations

import json
import os
import re

from . import audio as audio_mod
from . import motion as motion_mod
from .ffmpeg import FFmpegError, Tools, run, summarize


def _black_ratio(tools: Tools, path: str, *, threshold: float = 0.10) -> float:
    proc = run(
        [tools.ffmpeg, "-hide_banner", "-nostats", "-i", path,
         "-vf", f"blackdetect=d=0.1:pix_th={threshold}", "-an", "-f", "null", "-"]
    )
    text = proc.stderr.decode("utf-8", "replace")
    total = 0.0
    for start, end in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", text):
        total += float(end) - float(start)
    duration = summarize(tools, path)["duration"] or 1.0
    return round(total / duration, 4)


def _freeze_ratio(tools: Tools, path: str, *, noise_db: float = -50.0, min_dur: float = 0.4) -> float:
    proc = run(
        [tools.ffmpeg, "-hide_banner", "-nostats", "-i", path,
         "-vf", f"freezedetect=n={noise_db}dB:d={min_dur}", "-an", "-f", "null", "-"]
    )
    text = proc.stderr.decode("utf-8", "replace")
    total = 0.0
    for start, dur in re.findall(r"freeze_start: ([0-9.]+).*?freeze_duration: ([0-9.]+)", text, flags=re.S):
        total += float(dur)
    duration = summarize(tools, path)["duration"] or 1.0
    return round(total / duration, 4)


def caption_coverage(project: dict, *, transition_frames: int, fps: int) -> dict:
    """Measure how much of the film carries captions, from the project data.

    This does not read the rendered pixels (no OCR); it verifies that the cue
    plan itself leaves no long dead air, which is the failure mode that matters
    for the burned-in caption system.
    """
    shots = project["shots"]
    cursor = 0.0
    covered = 0.0
    total = 0.0
    gaps = []
    for i, shot in enumerate(shots):
        # A dissolve overlaps the previous shot by `transitionIn` frames, so only
        # the visible part counts; a cut (transitionIn = 0) counts in full.
        trans = (shot.get("transitionIn", transition_frames) / fps) if i > 0 else 0.0
        effective = float(shot["seconds"]) - trans
        total += effective
        if str(shot["line"]).strip():
            covered += effective
        else:
            gaps.append({"shot": shot["id"], "from": round(cursor, 2), "to": round(cursor + effective, 2)})
        cursor += effective
    return {
        "coverage": round(covered / total, 3) if total else 0.0,
        "total_seconds": round(total, 2),
        "uncovered": gaps,
        "method": "computed from the cue plan (shot lines), not from OCR of the render",
    }


def run_qa(
    tools: Tools,
    *,
    output: str,
    project: dict,
    expected_duration: float | None = None,
    thresholds: dict | None = None,
    out_dir: str | None = None,
) -> dict:
    th = {
        "duration_tolerance_s": 0.25,
        "min_motion_energy": 1.0,
        "max_black_ratio": 0.02,
        "max_freeze_ratio": 0.55,
        "loudness_range_lufs": [-22.0, -11.0],
        "caption_coverage_min": 0.5,
        **(thresholds or {}),
    }

    checks: list[dict] = []
    if not os.path.exists(output):
        return {"ok": False, "checks": [{"id": "exists", "pass": False, "detail": f"missing {output}"}], "output": output}

    info = summarize(tools, output)
    checks.append({"id": "readable", "pass": True, "value": info["container"], "detail": "ffprobe parsed the file"})
    checks.append(
        {
            "id": "has_video",
            "pass": bool(info["video"]),
            "value": info["video"],
            "detail": "video stream present",
        }
    )
    checks.append(
        {
            "id": "has_audio",
            "pass": bool(info["audio"]),
            "value": info["audio"],
            "detail": "audio stream present" if info["audio"] else "no audio stream: the cut is silent",
        }
    )

    expected = expected_duration if expected_duration is not None else caption_coverage(project, transition_frames=project.get("transitionFrames", 0), fps=project["format"]["fps"])["total_seconds"]
    delta = abs(info["duration"] - expected)
    checks.append(
        {
            "id": "duration",
            "pass": delta <= th["duration_tolerance_s"],
            "value": round(info["duration"], 3),
            "expected": round(expected, 3),
            "detail": f"delta {delta:.3f}s (tolerance {th['duration_tolerance_s']}s)",
        }
    )

    res_ok = (
        info["video"]
        and info["video"]["width"] == project["format"]["width"]
        and info["video"]["height"] == project["format"]["height"]
        and abs(info["video"]["fps"] - project["format"]["fps"]) < 0.05
    )
    checks.append({"id": "format", "pass": bool(res_ok), "value": info["video"], "detail": "to spec"})

    motion = motion_mod.analyze(tools, output, fps=2.0)
    checks.append(
        {
            "id": "motion",
            "pass": motion.get("mean_motion_energy", 0) >= th["min_motion_energy"],
            "value": motion.get("mean_motion_energy"),
            "detail": f"min {th['min_motion_energy']} — guards against a slideshow of stills",
        }
    )

    black = _black_ratio(tools, output)
    checks.append(
        {
            "id": "black_frames",
            "pass": black <= th["max_black_ratio"],
            "value": black,
            "detail": f"max {th['max_black_ratio']} — a black render must never pass",
        }
    )

    freeze = _freeze_ratio(tools, output)
    checks.append({"id": "freeze", "pass": freeze <= th["max_freeze_ratio"], "value": freeze, "detail": "static-frame budget"})

    if info["audio"]:
        audio_duration = info["audio"].get("duration") or info["duration"]
        audio_delta = abs(info["duration"] - audio_duration)
        checks.append(
            {
                "id": "audio_duration",
                "pass": audio_delta <= th["duration_tolerance_s"],
                "value": round(audio_duration, 3),
                "expected": round(info["duration"], 3),
                "detail": f"audio covers the picture; delta {audio_delta:.3f}s",
            }
        )
        loud = audio_mod.loudness(tools, output)
        mean = loud.get("mean_volume_db")
        low, high = th["loudness_range_lufs"]
        checks.append(
            {
                "id": "loudness",
                "pass": mean is not None and low <= mean <= high,
                "value": mean,
                "detail": f"acceptable band {low}..{high} dB (mean volume, not LUFS)",
            }
        )
        env = audio_mod.rms_envelope(tools, output)
        activity = audio_mod.voice_activity(env)
        checks.append(
            {
                "id": "audio_activity",
                "pass": activity["active_ratio"] > 0.05,
                "value": activity["active_ratio"],
                "detail": "the soundtrack is not near-silence",
            }
        )
    else:
        checks.append({"id": "loudness", "pass": False, "value": None, "detail": "no audio to measure"})

    cov = caption_coverage(project, transition_frames=project.get("transitionFrames", 0), fps=project["format"]["fps"])
    checks.append(
        {
            "id": "caption_plan",
            "pass": cov["coverage"] >= th["caption_coverage_min"],
            "value": cov["coverage"],
            "detail": cov["method"],
        }
    )

    ok = all(c["pass"] for c in checks)
    report = {
        "ok": ok,
        "output": os.path.abspath(output),
        "file": info,
        "checks": checks,
        "captions": cov,
        "motion": {k: v for k, v in motion.items() if k != "shift_samples"},
        "thresholds": th,
        "note": "heuristic gates calibrated on this engine's renders; not an aesthetic judgement",
    }
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "final_quality_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        with open(os.path.join(out_dir, "final_quality_report.md"), "w", encoding="utf-8") as fh:
            fh.write(render_markdown(report))
    return report


def render_markdown(report: dict) -> str:
    lines = [
        "# Final quality report",
        "",
        f"Output: `{report.get('output')}`",
        f"Result: **{'PASS' if report.get('ok') else 'FAIL'}**",
        "",
        "| check | pass | value | detail |",
        "|---|---|---|---|",
    ]
    for check in report.get("checks", []):
        lines.append(
            f"| {check['id']} | {'✅' if check['pass'] else '❌'} | `{check.get('value')}` | {check.get('detail', '')} |"
        )
    lines += [
        "",
        "> " + report.get("note", ""),
        "",
    ]
    return "\n".join(lines)
