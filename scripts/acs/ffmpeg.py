"""Thin, explicit wrappers around FFmpeg / FFprobe.

Every helper raises FFmpegError with the real stderr tail so that failures are
diagnosable instead of silently returning empty data.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Iterable, Sequence


class FFmpegError(RuntimeError):
    pass


@dataclass(frozen=True)
class Tools:
    ffmpeg: str
    ffprobe: str

    @classmethod
    def detect(cls) -> "Tools":
        ffmpeg = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
        ffprobe = os.environ.get("FFPROBE_BIN") or shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise FFmpegError(
                "FFmpeg/FFprobe not found in PATH. Install FFmpeg and re-run "
                "(winget install Gyan.FFmpeg / brew install ffmpeg / apt install ffmpeg)."
            )
        return cls(ffmpeg=ffmpeg, ffprobe=ffprobe)


def run(cmd: Sequence[str], *, binary: bool = False) -> subprocess.CompletedProcess:
    """Run a command, raising FFmpegError with a stderr tail on failure."""
    proc = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-12:]
        raise FFmpegError(
            "Command failed (%d): %s\n%s"
            % (proc.returncode, " ".join(cmd[:6]) + " ...", "\n".join(tail))
        )
    return proc


def probe(tools: Tools, path: str) -> dict:
    """Full ffprobe JSON (format + streams)."""
    proc = run(
        [
            tools.ffprobe,
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-print_format", "json",
            path,
        ]
    )
    return json.loads(proc.stdout.decode("utf-8", "replace"))


def _fraction(value: str) -> float:
    if not value or value in ("0/0", "N/A"):
        return 0.0
    if "/" in value:
        num, den = value.split("/", 1)
        try:
            return float(num) / float(den) if float(den) else 0.0
        except ValueError:
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def summarize(tools: Tools, path: str) -> dict:
    """Compact, stable description of a media file used by every other module."""
    data = probe(tools, path)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = [s for s in streams if s.get("codec_type") == "audio"]

    duration = float(fmt.get("duration") or 0.0)
    if not duration and video:
        duration = float(video.get("duration") or 0.0)

    out = {
        "path": os.path.abspath(path),
        "file": os.path.basename(path),
        "duration": round(duration, 3),
        "size_bytes": int(fmt.get("size") or 0),
        "bitrate": int(fmt.get("bit_rate") or 0),
        "container": fmt.get("format_name", ""),
        "video": None,
        "audio": None,
    }
    if video:
        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
        out["video"] = {
            "codec": video.get("codec_name"),
            "width": width,
            "height": height,
            "fps": round(_fraction(video.get("r_frame_rate", "0/1")), 3),
            "fps_avg": round(_fraction(video.get("avg_frame_rate", "0/1")), 3),
            "pix_fmt": video.get("pix_fmt"),
            "frames": int(video.get("nb_frames") or 0) or None,
            "aspect": round(width / height, 4) if height else None,
            "orientation": (
                "vertical" if height > width else "horizontal" if width > height else "square"
            ),
        }
    if audio:
        a = audio[0]
        out["audio"] = {
            "codec": a.get("codec_name"),
            "channels": int(a.get("channels") or 0),
            "sample_rate": int(a.get("sample_rate") or 0),
            "bitrate": int(a.get("bit_rate") or 0),
            "duration": round(float(a.get("duration") or duration or 0.0), 3),
            "streams": len(audio),
        }
    return out


def read_pcm(tools: Tools, path: str, *, sample_rate: int = 8000, channels: int = 1) -> bytes:
    """Decode audio to signed 16-bit little-endian PCM for measurements."""
    proc = run(
        [
            tools.ffmpeg, "-v", "error", "-i", path,
            "-vn", "-ac", str(channels), "-ar", str(sample_rate),
            "-f", "s16le", "-",
        ],
        binary=True,
    )
    return proc.stdout


def read_video(tools: Tools, path: str, *, fps: float, width: int, height: int | None = None) -> bytes:
    """Decode video to rgb24 at a reduced size; used for palette/energy math."""
    if height is None:
        height = max(2, int(round(width * 9 / 16)))
    # Force even dimensions, FFmpeg requires it for rawvideo rgb24? (not strictly, but keep tidy)
    width -= width % 2
    height -= height % 2
    proc = run(
        [
            tools.ffmpeg, "-v", "error", "-i", path,
            "-an", "-vf", f"fps={fps},scale={width}:{height}:flags=area",
            "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
        ],
        binary=True,
    )
    return proc.stdout


def iter_frames(raw: bytes, width: int, height: int) -> Iterable[bytes]:
    frame_size = width * height * 3
    for offset in range(0, len(raw) - frame_size + 1, frame_size):
        yield raw[offset: offset + frame_size]
