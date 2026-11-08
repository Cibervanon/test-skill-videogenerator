"""Duck the score under the voice and print one mixed track.

The earlier implementation expressed the whole mix as a single FFmpeg
``filter_complex``. In practice the graph could emit the score only: the voice
was used as a sidechain and then re-used as an ``amix`` input, and
``sidechaincompress``/``alimiter`` made the result hard to audit. A delivered
MP4 with music but no narration is exactly the failure this module exists to
prevent, so the mix is now computed explicitly in numpy:

* decode both stems to float stereo at 48 kHz;
* follow the voice RMS envelope (20 ms window, 10 ms hop);
* smooth it with a 20 ms attack and a 250 ms release;
* attenuate the score while the voice is speaking;
* sum voice + ducked score, then scale (never clip) to the delivery ceiling.

The result is deterministic, inspectable and testable without decoding FFmpeg
filter semantics.
"""

from __future__ import annotations

import os
import subprocess
import wave

import numpy as np

from .ffmpeg import FFmpegError, Tools, summarize

SAMPLE_RATE = 48000


def _decode_stereo(path: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", path,
            "-vn", "-ac", "2", "-ar", str(sample_rate),
            "-f", "f32le", "-",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-6:]
        raise FFmpegError(f"could not decode {path}: " + " / ".join(tail))
    data = np.frombuffer(proc.stdout, dtype="<f4").astype(np.float32)
    if data.size % 2:
        data = data[:-1]
    return data.reshape(-1, 2)


def _rms_envelope(mono: np.ndarray, sample_rate: int, *, window: float = 0.02, hop: float = 0.01) -> np.ndarray:
    win = max(1, int(window * sample_rate))
    step = max(1, int(hop * sample_rate))
    count = max(1, (len(mono) - win) // step + 1)
    values = np.empty(count, dtype=np.float32)
    for index in range(count):
        chunk = mono[index * step : index * step + win]
        values[index] = float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) else 0.0
    centres = (np.arange(count) * step + win / 2) / sample_rate
    return np.interp(np.arange(len(mono)) / sample_rate, centres, values).astype(np.float32)


def _smooth(values: np.ndarray, sample_rate: int, *, hop: float = 0.01, attack: float = 0.02, release: float = 0.25) -> np.ndarray:
    """One-pole follower over the envelope frames (cheap, deterministic)."""
    attack_coef = float(np.exp(-hop / max(1e-6, attack)))
    release_coef = float(np.exp(-hop / max(1e-6, release)))
    out = np.empty_like(values)
    previous = 0.0
    for index, value in enumerate(values):
        coef = attack_coef if value > previous else release_coef
        previous = coef * previous + (1.0 - coef) * float(value)
        out[index] = previous
    return out


def _write_wav(path: str, data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    clipped = np.clip(data, -1.0, 1.0)
    with wave.open(path, "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(sample_rate)
        fh.writeframes((clipped * 32767.0).astype("<i2").tobytes())


def duck(
    tools: Tools,
    *,
    score: str,
    voice: str,
    out: str,
    ducked_out: str | None = None,
    music_gain: float = 0.45,
    voice_gain: float = 1.0,
    duck_depth: float = 0.72,
    ceiling: float = 0.89,
    fade_in: float = 0.08,
    fade_out: float = 0.12,
) -> dict:
    if os.path.abspath(out) in {os.path.abspath(score), os.path.abspath(voice)}:
        raise FFmpegError("refusing to overwrite an input stem with the mixdown")
    ducked_out = ducked_out or os.path.join(os.path.dirname(out), "music_ducked.wav")
    for path, label in ((score, "score"), (voice, "voice")):
        if not os.path.exists(path):
            raise FFmpegError(f"missing {label} stem: {path}")

    bed = _decode_stereo(score)
    vox = _decode_stereo(voice)
    length = max(len(bed), len(vox))
    bed = np.pad(bed, ((0, length - len(bed)), (0, 0)))
    vox = np.pad(vox, ((0, length - len(vox)), (0, 0)))

    # The voice is the key: its envelope decides how far the score drops.
    envelope = _rms_envelope(vox.mean(axis=1), SAMPLE_RATE)
    peak = float(envelope.max()) if len(envelope) else 0.0
    speaking = (envelope > max(1e-4, peak * 0.03)).astype(np.float32)
    frame_hop = 0.01
    duck_curve = 1.0 - duck_depth * _smooth(speaking, SAMPLE_RATE, hop=frame_hop)

    ducked = bed * (music_gain * duck_curve[:, None])
    mixed = ducked + vox * voice_gain

    measured_peak = float(np.abs(mixed).max()) if mixed.size else 0.0
    if measured_peak > ceiling:
        mixed *= ceiling / measured_peak

    # A hard start/end on a WAV becomes an audible click after AAC muxing.
    # Fade only the edges; the narration itself is untouched.
    def _edge_fade(data: np.ndarray, seconds_in: float, seconds_out: float) -> np.ndarray:
        result = data.copy()
        n_in = min(len(result), max(0, int(seconds_in * SAMPLE_RATE)))
        n_out = min(len(result), max(0, int(seconds_out * SAMPLE_RATE)))
        if n_in:
            result[:n_in] *= np.linspace(0.0, 1.0, n_in, dtype=np.float32)[:, None]
        if n_out:
            result[-n_out:] *= np.linspace(1.0, 0.0, n_out, dtype=np.float32)[:, None]
        return result

    mixed = _edge_fade(mixed, fade_in, fade_out)
    ducked = _edge_fade(ducked, fade_in, fade_out)
    _write_wav(out, mixed)
    _write_wav(ducked_out, ducked)

    info = summarize(tools, out)
    active = float(np.mean(duck_curve < 0.9)) if len(duck_curve) else 0.0
    return {
        "output": os.path.abspath(out),
        "ducked_bed": os.path.abspath(ducked_out),
        "duration": info["duration"],
        "size_bytes": info["size_bytes"],
        "music_gain": music_gain,
        "voice_gain": voice_gain,
        "duck_depth": duck_depth,
        "ducked_ratio": round(active, 3),
        "peak": round(min(1.0, measured_peak), 4),
        "fade_in": fade_in,
        "fade_out": fade_out,
        "ducking": (
            "numpy envelope follower on the voice (20 ms RMS, 20 ms attack, 250 ms release); "
            "score attenuated while speaking, linear ceiling — no sidechain filter graph"
        ),
    }
