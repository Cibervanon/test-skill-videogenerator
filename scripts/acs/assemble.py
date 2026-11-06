"""Assembly and delivery: mux picture + soundtrack, normalise loudness, export.

Source files are never modified: every step writes a new file and the input
paths are checked against the output path.
"""

from __future__ import annotations

import json
import os
import re
import subprocess

from .ffmpeg import FFmpegError, Tools, run, summarize


def measure_loudness(tools: Tools, audio: str, target_lufs: float, true_peak_db: float) -> dict | None:
    """First loudnorm pass: measure, so the second pass can run in linear mode.

    Single-pass loudnorm is dynamic and pumps on a score with quiet gaps; the
    two-pass linear mode (borrowed from the external repo's master.py) holds the
    gain steady. Returns None if measurement fails, and the caller falls back.
    """
    result = subprocess.run(
        [
            tools.ffmpeg, "-hide_banner", "-nostats", "-i", audio,
            "-af", f"loudnorm=I={target_lufs}:TP={true_peak_db}:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    text = result.stderr
    match = re.search(r"\{[^{}]*\}", text[text.rfind("{") - 1200 :] if "{" in text else text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if "input_i" not in data:
        return None
    return data



def assemble(
    tools: Tools,
    *,
    video: str,
    audio: str | None,
    out: str,
    target_lufs: float = -16.0,
    true_peak_db: float = -1.5,
    crf: int = 18,
    preset: str = "medium",
    fade_seconds: float = 0.6,
    require_full_audio: bool = True,
) -> dict:
    if os.path.abspath(out) in {os.path.abspath(video), os.path.abspath(audio or "")}:
        raise FFmpegError("refusing to overwrite an input file with the assembled output")
    if not os.path.exists(video):
        raise FFmpegError(f"missing render: {video}")
    if audio and not os.path.exists(audio):
        raise FFmpegError(f"missing soundtrack: {audio}")

    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    duration = summarize(tools, video)["duration"]
    if audio:
        audio_duration = summarize(tools, audio)["duration"]
        if require_full_audio and audio_duration + 0.05 < duration:
            raise FFmpegError(
                f"soundtrack is {audio_duration:.3f}s but picture is {duration:.3f}s; "
                "refusing to truncate the film or leave the ending silent. "
                "Regenerate the narration/mix or pass --allow-short-audio deliberately."
            )
    fade_out_start = max(0.0, duration - fade_seconds)

    cmd = [tools.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", video]
    if audio:
        cmd += ["-i", audio]
        measured = measure_loudness(tools, audio, target_lufs, true_peak_db)
        if measured:
            loudnorm = (
                f"loudnorm=I={target_lufs}:TP={true_peak_db}:LRA=11"
                f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
                f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
                f":offset={measured['target_offset']}:linear=true"
            )
            mode = "two-pass linear loudnorm"
        else:
            loudnorm = f"loudnorm=I={target_lufs}:TP={true_peak_db}:LRA=11"
            mode = "single-pass loudnorm (measurement unavailable)"
        audio_filter = (
            f"{loudnorm},"
            f"afade=t=in:st=0:d={fade_seconds},"
            f"afade=t=out:st={fade_out_start:.2f}:d={fade_seconds},"
            f"atrim=0:{duration:.3f}"
        )
        cmd += [
            "-filter_complex", f"[1:a]{audio_filter}[a]",
            "-map", "0:v:0", "-map", "[a]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        ]
    cmd += [
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-shortest", out,
    ]
    run(cmd)

    info = summarize(tools, out)
    return {
        "output": os.path.abspath(out),
        "duration": info["duration"],
        "size_bytes": info["size_bytes"],
        "video": info["video"],
        "audio": info["audio"],
        "source": os.path.abspath(video),
        "soundtrack": os.path.abspath(audio) if audio else None,
        "target_lufs": target_lufs,
        "audio_duration": round(summarize(tools, audio)["duration"], 3) if audio else None,
        "note": f"{mode}; verify with qa.py",
    }


def make_preview(tools: Tools, *, source: str, out: str, width: int = 540, crf: int = 26) -> dict:
    if os.path.abspath(out) == os.path.abspath(source):
        raise FFmpegError("preview path must differ from the source")
    run(
        [
            tools.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", source,
            "-vf", f"scale={width}:-2:flags=lanczos",
            "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", out,
        ]
    )
    return summarize(tools, out)
