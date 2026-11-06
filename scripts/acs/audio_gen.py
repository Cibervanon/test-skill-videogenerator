#!/usr/bin/env python3
"""Procedural soundtrack for a shot list: ambience, foley and score, by code.

No model, no API, no sample library: everything is synthesised with the
standard library and written as 44.1 kHz / 16-bit / stereo WAV. The result is
deterministic for a given project (seeded PRNG), so re-renders are identical.

Design intent is cinematic and *sparse*: the reference tracks are narration over
a quiet bed, so the bed is built from wind, a low drone, a few bell hits and
footsteps on snow — not a wall of music.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import struct
import wave
from dataclasses import dataclass

SAMPLE_RATE = 44100


@dataclass
class Note:
    start: float
    dur: float
    freq: float
    amp: float
    kind: str = "pluck"


def _soft_clip(x: float) -> float:
    return math.tanh(x * 1.2) * 0.85


class Track:
    """Stereo float buffer with mixing helpers."""

    def __init__(self, seconds: float, sr: int = SAMPLE_RATE):
        self.sr = sr
        self.n = int(seconds * sr)
        self.left = [0.0] * self.n
        self.right = [0.0] * self.n

    def add(self, index: int, value: float, pan: float = 0.0) -> None:
        if 0 <= index < self.n:
            l = value * (1 - max(0.0, pan))
            r = value * (1 + min(0.0, pan))
            self.left[index] += l
            self.right[index] += r

    def mix_mono(self, samples: list[float], offset: int, gain: float = 1.0) -> None:
        for i, s in enumerate(samples):
            self.add(offset + i, s * gain)

    def normalize(self, peak_target: float = 0.89, rms_target_db: float = -18.0) -> dict:
        peak = max(1e-9, max(abs(v) for v in self.left + self.right))
        gain = peak_target / peak
        self.left = [_soft_clip(v * gain) for v in self.left]
        self.right = [_soft_clip(v * gain) for v in self.right]
        rms = math.sqrt(sum(v * v for v in self.left) / max(1, self.n))
        rms_db = 20 * math.log10(max(rms, 1e-9))
        return {"peak_before": round(peak, 4), "gain": round(gain, 4), "rms_db": round(rms_db, 2)}

    def write(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with wave.open(path, "wb") as fh:
            fh.setnchannels(2)
            fh.setsampwidth(2)
            fh.setframerate(self.sr)
            frames = bytearray()
            for l, r in zip(self.left, self.right):
                frames += struct.pack("<hh", int(max(-1, min(1, l)) * 32767), int(max(-1, min(1, r)) * 32767))
            fh.writeframes(bytes(frames))


def wind(seconds: float, sr: int, rnd: random.Random, gain: float = 0.22) -> list[float]:
    """Brown-ish noise through a one-pole low-pass, slowly modulated."""
    out = []
    lp = 0.0
    lp2 = 0.0
    phase = rnd.random() * 6.28
    for i in range(int(seconds * sr)):
        white = rnd.uniform(-1, 1)
        lp += 0.02 * (white - lp)
        lp2 += 0.006 * (lp - lp2)
        t = i / sr
        gust = 0.55 + 0.45 * math.sin(phase + t * 0.55) * math.sin(phase * 0.6 + t * 0.19)
        out.append(lp2 * 14.0 * gust * gain)
    return out


def drone(seconds: float, sr: int, base: float = 55.0) -> list[float]:
    """Low sustained pad: root, fifth, octave, slow beating."""
    out = []
    partials = [(1.0, 0.5), (1.5, 0.18), (2.0, 0.22), (3.0, 0.06)]
    for i in range(int(seconds * sr)):
        t = i / sr
        env = min(1.0, t / 2.5) * min(1.0, (seconds - t) / 3.0)
        v = 0.0
        for mult, amp in partials:
            v += math.sin(2 * math.pi * base * mult * t + mult) * amp
        out.append(v * env * 0.06)
    return out


def bell(seconds: float, sr: int, base: float = 392.0, amp: float = 0.5) -> list[float]:
    """Inharmonic bell: partials with exponential decay (additive synthesis)."""
    partials = [(1.0, 1.0, 2.6), (2.01, 0.6, 1.9), (2.98, 0.4, 1.5), (4.16, 0.25, 1.1), (5.43, 0.16, 0.8), (6.79, 0.09, 0.6)]
    out = []
    for i in range(int(seconds * sr)):
        t = i / sr
        v = 0.0
        for mult, pamp, decay in partials:
            v += math.sin(2 * math.pi * base * mult * t) * pamp * math.exp(-decay * t)
        out.append(v * amp * 0.25)
    return out


def footstep(seconds: float, sr: int, rnd: random.Random, gain: float = 0.35) -> list[float]:
    """Snow crunch: short noise burst with a fast decay and a low thump."""
    out = []
    n = int(seconds * sr)
    for i in range(n):
        t = i / sr
        env = math.exp(-9.0 * t)
        noise = rnd.uniform(-1, 1) * env * 0.5
        thump = math.sin(2 * math.pi * 78 * t) * math.exp(-14 * t) * 0.5
        out.append((noise + thump) * gain)
    return out


def pluck(seconds: float, sr: int, freq: float, amp: float = 0.2, rnd: random.Random | None = None) -> list[float]:
    """Karplus-Strong-ish pluck: short noise excitation + comb decay."""
    rnd = rnd or random.Random(0)
    out = [0.0] * int(seconds * sr)
    period = max(2, int(sr / freq))
    buffer = [rnd.uniform(-1, 1) for _ in range(period)]
    idx = 0
    for i in range(len(out)):
        v = buffer[idx]
        nxt = (idx + 1) % period
        buffer[idx] = (v + buffer[nxt]) * 0.5 * 0.996
        idx = nxt
        out[i] = v * amp * math.exp(-2.2 * (i / sr))
    return out


def build(spec: dict, *, seed: int = 20261103) -> tuple[Track, dict]:
    """spec: {duration, bpm?, key_hz?, events:[{type,at,dur?,gain?,pan?,freq?}], music:bool}"""
    rnd = random.Random(seed)
    duration = float(spec["duration"])
    track = Track(duration)
    sr = track.sr
    report: dict = {"duration": duration, "layers": []}

    amb = spec.get("ambience", "wind")
    if amb == "wind":
        track.mix_mono(wind(duration, sr, rnd), 0, gain=0.9)
        report["layers"].append("wind bed (low-pass noise, gust modulation)")
    track.mix_mono(drone(duration, sr, spec.get("drone_hz", 55.0)), 0, gain=1.0)
    report["layers"].append("low drone pad (additive, 4 partials)")

    if spec.get("music", True):
        bpm = float(spec.get("bpm", 72))
        beat = 60.0 / bpm
        root = float(spec.get("key_hz", 110.0))
        scale = [1.0, 1.1225, 1.3348, 1.4983, 1.7820, 2.0]  # minor-ish pentatonic
        pattern = [0, 2, 4, 3, 1, 2, 0, 3]
        for bar in range(int(duration / (beat * 2))):
            step = pattern[bar % len(pattern)]
            t = bar * beat * 2 + rnd.uniform(0.0, 0.02)
            if rnd.random() < 0.72:
                note = pluck(min(1.6, duration - t), sr, root * scale[step % len(scale)], amp=0.12, rnd=rnd)
                track.mix_mono(note, int(t * sr), gain=1.0)
        report["layers"].append(f"sparse plucked motif @ {bpm:.0f} bpm, root {root:.1f} Hz")

    for event in spec.get("events", []):
        at = float(event["at"])
        kind = event["type"]
        pan = float(event.get("pan", 0.0))
        if kind == "bell":
            samples = bell(float(event.get("dur", 6.0)), sr, float(event.get("freq", 392.0)), float(event.get("gain", 0.55)))
        elif kind == "footstep":
            samples = footstep(float(event.get("dur", 0.3)), sr, rnd, float(event.get("gain", 0.3)))
        elif kind == "dig":
            samples = footstep(0.22, sr, rnd, float(event.get("gain", 0.22)))
        else:
            report.setdefault("skipped", []).append(kind)
            continue
        track.mix_mono(samples, int(at * sr), gain=1.0)
        if pan:
            # apply a simple pan by scaling one channel after mixing
            start = int(at * sr)
            for i in range(min(len(samples), track.n - start)):
                l = samples[i]
                track.left[start + i] += l * (1 - max(0.0, pan)) - l
                track.right[start + i] += l * (1 + min(0.0, pan)) - l
        report.setdefault("events", []).append({"type": kind, "at": at, "pan": pan})

    stats = track.normalize(peak_target=0.88)
    report.update(stats)
    report["sample_rate"] = sr
    return track, report


def spec_from_project(project: dict) -> dict:
    """Derive the sound design from the shot list, so audio follows the edit."""
    fps = project["format"]["fps"]
    fade = project.get("transitionFrames", 0) / fps
    events = []
    music_notes = True
    cursor = 0.0
    for i, shot in enumerate(project["shots"]):
        dur = shot["seconds"]
        scene = shot["scene"]
        # transitions are per-boundary (cuts where the subject continues), so the
        # soundtrack timeline must follow the same arithmetic as the renderer
        this_fade = shot.get("transitionIn", project.get("transitionFrames", 0)) / fps
        if scene in ("doorway", "faceCloseup"):
            music_notes = False
        # An explicit cue list owns the shot's sound design, including an empty
        # list (intentional silence). Legacy manifests keep the scene-derived
        # effects, so old projects render and sound exactly as before.
        if "sound" in shot:
            for cue in shot.get("sound") or []:
                events.append({**cue, "at": round(cursor + float(cue.get("at", 0.0)), 3)})
        else:
            if scene == "bellInsert":
                events.append({"type": "bell", "at": cursor + 0.4, "dur": 8.0, "freq": 392.0, "gain": 0.6})
            if scene == "fieldDawn":
                for k in range(5):
                    events.append({"type": "dig", "at": cursor + 1.2 + k * 1.35, "pan": -0.25, "gain": 0.2})
            if scene == "townNight":
                for k in range(8):
                    events.append({"type": "footstep", "at": cursor + 0.8 + k * 0.62, "pan": 0.2, "gain": 0.16})
        if i > 0:
            cursor += dur - this_fade
        else:
            cursor += dur
    total = cursor
    return {
        "duration": round(total, 3),
        "bpm": 68,
        "key_hz": 98.0,
        "music": True,
        "ambience": "wind",
        "events": sorted(events, key=lambda e: e["at"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the procedural soundtrack for a project.")
    parser.add_argument("--project", required=True, help="project.json")
    parser.add_argument("--out", required=True, help="output .wav")
    parser.add_argument("--report", help="write a JSON report of the synthesis")
    args = parser.parse_args(argv)

    import json

    with open(args.project, "r", encoding="utf-8") as fh:
        project = json.load(fh)
    spec = spec_from_project(project)
    track, report = build(spec)
    track.write(args.out)
    report["spec"] = {k: v for k, v in spec.items() if k != "events"}
    report["written"] = os.path.abspath(args.out)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    print(f"[audio] {args.out} ({report['duration']:.2f}s, rms {report['rms_db']} dBFS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
