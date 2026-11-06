"""Narration validation: prove the voice is real, audible and in the mix.

It reads the generated takes, the timeline stem and the final mix, and checks
the claims that matter before calling a render narrated:

* every line has a WAV take;
* the stem is not silent at the line's slot;
* the mix carries the voice, not only the score;
* starts are ordered, no phrase is duplicated.

It does not understand words and it is not an ASR alignment: word timing still
comes from Kokoro's `pred_dur` (see LIMITATIONS.md).
"""

from __future__ import annotations

import os
import wave

import numpy as np


def read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as fh:
        sr = fh.getframerate()
        channels = fh.getnchannels()
        raw = fh.readframes(fh.getnframes())
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, sr


def _db(value: float) -> float:
    return round(20.0 * float(np.log10(max(1e-9, value))), 2)


def validate(project_dir: str, plan: dict, *, min_rms_db: float = -40.0) -> dict:
    lines = plan.get("lines") or []
    problems: list[str] = []
    warnings: list[str] = []
    rows = []

    stem_rel = plan.get("stem") or "generation/voice/voice.wav"
    stem_path = os.path.join(project_dir, stem_rel)
    mix_path = os.path.join(project_dir, "generation", "audio", "mix.wav")
    voice, sr = read_wav(stem_path) if os.path.exists(stem_path) else (None, None)
    mixed, _ = read_wav(mix_path) if os.path.exists(mix_path) else (None, None)
    if voice is None:
        problems.append(f"missing narration stem: {stem_rel}")
    if mixed is None:
        problems.append("missing mix.wav: run `studio.py mixdown`")

    starts = [float(line.get("start") or 0) for line in lines]
    if starts != sorted(starts):
        problems.append("lines are not ordered by start time")
    texts = [str(line.get("text") or "").strip() for line in lines]
    if len(set(texts)) != len(texts):
        warnings.append("two lines share the same text (check for duplicated takes)")

    # Narration is one role, not a cast carousel. A character may speak only when
    # the shot explicitly declares dialogue; otherwise every line must use the
    # narrator voice, including shots that show a character.
    voices = {str(line.get("voice")) for line in lines if line.get("voice")}
    speakers = {str(line.get("speaker")) for line in lines if line.get("speaker")}
    if plan.get("narration"):
        if speakers - {"narrator"}:
            problems.append(
                "narration mode uses character speaker(s): " + ", ".join(sorted(speakers - {"narrator"}))
            )
        if len(voices) > 1:
            problems.append(
                "narration mode uses more than one voice: " + ", ".join(sorted(voices))
            )

    for index, line in enumerate(lines):
        start = float(line.get("start") or 0)
        duration = float(line.get("audio_duration") or 0)
        next_start = starts[index + 1] if index + 1 < len(starts) else start + duration
        audible_end = min(start + duration, next_start)
        take_rel = line.get("audio")
        take_path = os.path.join(project_dir, take_rel) if take_rel else None
        row = {
            "shot": line.get("shot"),
            "speaker": line.get("speaker"),
            "voice": line.get("voice"),
            "start": round(start, 3),
            "audio_seconds": round(duration, 3),
            "slot_seconds": round(float(line.get("end") or 0) - start, 3),
            "stem_seconds": round(max(0.0, audible_end - start), 3),
            "trimmed": bool(duration and audible_end < start + duration - 0.005),
        }
        if not take_path or not os.path.exists(take_path):
            problems.append(f"{row['shot']}: no narration WAV at {take_rel}")
        else:
            take, take_sr = read_wav(take_path)
            row["take_seconds"] = round(len(take) / take_sr, 3)
            row["take_rms_db"] = _db(np.sqrt(np.mean(take**2))) if len(take) else -120.0
            row["take_peak_db"] = _db(float(np.max(np.abs(take)))) if len(take) else -120.0
            if len(take) == 0 or row["take_seconds"] < 0.2:
                problems.append(f"{row['shot']}: take is empty or shorter than 0.2 s")
            if row["take_peak_db"] >= -0.1:
                problems.append(f"{row['shot']}: take peaks at {row['take_peak_db']} dB (clipping risk)")
        if duration <= 0.2:
            problems.append(f"{row['shot']}: no usable audio duration in the plan")
        if voice is not None and sr:
            segment = voice[int(start * sr) : int(audible_end * sr)]
            row["stem_rms_db"] = _db(np.sqrt(np.mean(segment**2))) if len(segment) else -120.0
            if len(segment) == 0 or row["stem_rms_db"] < min_rms_db:
                problems.append(f"{row['shot']}: stem is silent at {start:.2f}s ({row['stem_rms_db']} dB)")
        if mixed is not None:
            mix_sr = 48000
            segment = mixed[int(start * mix_sr) : int(audible_end * mix_sr)]
            row["mix_rms_db"] = _db(np.sqrt(np.mean(segment**2))) if len(segment) else -120.0
            row["mix_peak_db"] = _db(float(np.max(np.abs(segment)))) if len(segment) else -120.0
            if len(segment) == 0 or row["mix_rms_db"] < min_rms_db:
                problems.append(f"{row['shot']}: voice window is silent in the mix")
            if row["mix_peak_db"] >= -0.05:
                warnings.append(f"{row['shot']}: mix reaches {row['mix_peak_db']} dB in this window")
        if row["trimmed"]:
            warnings.append(f"{row['shot']}: take runs {duration - (audible_end - start):.2f}s past the next line; trimmed in the stem")
        rows.append(row)

    total = max(starts[-1] + float(lines[-1].get("audio_duration") or 0), 0.0) if lines else 0.0
    speech = sum(float(line.get("audio_duration") or 0) for line in lines)
    stem_seconds = round(len(voice) / sr, 3) if voice is not None and sr else None
    mix_seconds = round(len(mixed) / 48000.0, 3) if mixed is not None else None
    project_seconds = float(plan.get("project_seconds") or total)
    # A silent tail is legitimate; a stem that ends before the last spoken line
    # is not. This is the duration check that catches a short WAV paired with a
    # longer narrated film without penalising a deliberate wordless ending.
    narration_end = max(starts[index] + float(line.get("audio_duration") or 0) for index, line in enumerate(lines)) if lines else 0.0
    if stem_seconds is not None and stem_seconds + 0.05 < narration_end:
        problems.append(
            f"narration stem is {stem_seconds:.3f}s but the last line ends at {narration_end:.3f}s; "
            "the WAV cuts narration"
        )
    if mix_seconds is not None and mix_seconds + 0.05 < narration_end:
        problems.append(
            f"mix.wav is {mix_seconds:.3f}s but the last line ends at {narration_end:.3f}s; "
            "the soundtrack cuts narration"
        )
    return {
        "ok": not problems,
        "provider": plan.get("provider"),
        "model": plan.get("model"),
        "lines": len(lines),
        "words": sum(len(line.get("words") or []) for line in lines),
        "speech_seconds": round(speech, 2),
        "timeline_seconds": round(total, 2),
        "project_seconds": round(project_seconds, 3),
        "narration_end": round(narration_end, 3),
        "stem_seconds": stem_seconds,
        "mix_seconds": mix_seconds,
        "narration": bool(plan.get("narration")),
        "voices": sorted(voices),
        "rows": rows,
        "problems": problems,
        "warnings": warnings,
        "method": (
            "PCM RMS/peak per line on the take, the stem and mix.wav. Audible signal, not intelligibility; "
            "no ASR and no claim of word-level alignment."
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Narration validation",
        "",
        f"Result: **{'OK' if report['ok'] else 'FAIL'}** · {report['lines']} lines · "
        f"{report['words']} words · {report['speech_seconds']} s of speech · "
        f"stem {report.get('stem_seconds')}s / last line {report.get('narration_end')}s",
        "",
        "| shot | speaker | voice | start | take | stem | mix RMS | peak | trimmed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['shot']} | {row['speaker']} | {row.get('voice') or '—'} | {row['start']}s | "
            f"{row.get('take_seconds', '—')}s | {row.get('stem_rms_db', '—')} dB | "
            f"{row.get('mix_rms_db', '—')} dB | {row.get('mix_peak_db', '—')} dB | "
            f"{'yes' if row['trimmed'] else 'no'} |"
        )
    lines += ["", "## Problems", ""]
    lines += [f"- {p}" for p in report["problems"]] or ["- none"]
    lines += ["", "## Warnings", ""]
    lines += [f"- {w}" for w in report["warnings"]] or ["- none"]
    lines += ["", f"> {report['method']}"]
    return "\n".join(lines) + "\n"
