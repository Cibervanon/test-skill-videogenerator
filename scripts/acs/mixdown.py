"""Duck the score under the voice and print one mixed track.

The score was written for films without narration, so it sits where a voice
needs to be. This is a real sidechain duck (the voice is the key), not a static
volume drop: the music breathes back in the gaps between lines.
"""

from __future__ import annotations

import os
import subprocess

from .ffmpeg import FFmpegError, Tools, run, summarize

CHAIN = (
    "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={music}[music];"
    "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={voice}[vox];"
    "[music][vox]sidechaincompress=threshold=0.04:ratio=10:attack=12:release=300:makeup=1[ducked];"
    "[ducked]anull[bed];"
    "[ducked][vox]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.89:attack=1:release=50:level=false,volume=0.9[a]"
)


def duck(
    tools: Tools,
    *,
    score: str,
    voice: str,
    out: str,
    ducked_out: str | None = None,
    music_gain: float = 0.45,
    voice_gain: float = 1.0,
) -> dict:
    if os.path.abspath(out) in {os.path.abspath(score), os.path.abspath(voice)}:
        raise FFmpegError("refusing to overwrite an input stem with the mixdown")
    ducked_out = ducked_out or os.path.join(os.path.dirname(out), "music_ducked.wav")
    for path, label in ((score, "score"), (voice, "voice")):
        if not os.path.exists(path):
            raise FFmpegError(f"missing {label} stem: {path}")
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    run(
        [
            tools.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", score, "-i", voice,
            "-filter_complex", CHAIN.format(music=music_gain, voice=voice_gain),
            "-map", "[a]", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out,
            "-map", "[bed]", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", ducked_out,
        ]
    )
    info = summarize(tools, out)
    return {
        "output": os.path.abspath(out),
        "ducked_bed": os.path.abspath(ducked_out),
        "duration": info["duration"],
        "size_bytes": info["size_bytes"],
        "music_gain": music_gain,
        "voice_gain": voice_gain,
        "ducking": "sidechaincompress threshold 0.04 · ratio 10 · attack 12 ms · release 300 ms",
    }
