"""Kokoro synthesis worker — executed by the isolated interpreter.

torch ships no wheels for Python 3.14, the interpreter this skill runs on, so
Kokoro lives in `.venv-kokoro` (3.12). The pipeline never imports torch: it
calls this worker as a subprocess and reads the JSON it writes.

Word timings come from Kokoro's own predicted phoneme durations (`pred_dur`).
That is the model's duration predictor, not an ASR forced alignment: it is
accurate enough to place captions and to decide whether a line overflows its
shot, and it is labelled `pred_dur` in every record so nobody mistakes it for a
measured alignment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

SAMPLE_RATE = 24000
CHUNK_PAUSE = 0.08
# Kokoro's duration predictor counts 600-sample frames: 24000 / 600 = 40 frames a second.
FRAMES_PER_SECOND = 40.0


def _syllables(word: str) -> int:
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", word.lower())))


def _proportional(text: str, start: float, span: float) -> list[dict]:
    """Fallback when phoneme/word counts disagree: distribute by syllables."""
    words = text.split()
    if not words or span <= 0:
        return []
    total = sum(_syllables(w) for w in words)
    out, t = [], start
    for word in words:
        dur = span * _syllables(word) / total
        out.append({"w": word, "s": round(t, 3), "e": round(t + dur, 3), "p": "", "source": "syllables"})
        t += dur
    return out


def words_from_pred(ps: str, pred, text: str, start: float, span: float) -> list[dict]:
    """Group per-phoneme durations into words, in order, starting at `start`."""
    ps_words = ps.split()
    text_words = text.split()
    frames = [float(x) for x in pred[1 : 1 + len(ps)]] if pred is not None else []
    if not ps_words or len(ps_words) != len(text_words) or len(frames) != len(ps):
        return _proportional(text, start, span)
    # The predictor can be a few frames off the vocoder's real length, so the
    # word times are normalised to the audio the model actually produced.
    predicted = sum(frames) / FRAMES_PER_SECOND
    scale = (span / predicted) if predicted > 0 and span > 0 else 1.0
    out, idx, t = [], 0, start
    for i, pw in enumerate(ps_words):
        while idx < len(ps) and ps[idx] == " ":
            idx += 1
        dur = sum(frames[idx : idx + len(pw)]) / FRAMES_PER_SECOND * scale
        idx += len(pw)
        out.append({"w": text_words[i], "s": round(t, 3), "e": round(t + max(dur, 0.02), 3), "p": "", "source": "pred_dur"})
        t += dur
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--lang", default="e")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--repo", default="hexgrad/Kokoro-82M")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--models-dir", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()

    if args.models_dir:
        os.makedirs(args.models_dir, exist_ok=True)
        os.environ.setdefault("HF_HOME", os.path.abspath(args.models_dir))

    started = time.time()
    import numpy as np
    import soundfile as sf
    import torch
    from kokoro import KPipeline

    version = getattr(__import__("kokoro"), "__version__", "unknown")
    if args.probe:
        with open(args.meta, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "ok": True,
                    "kokoro": version,
                    "torch": torch.__version__,
                    "cuda": bool(torch.cuda.is_available()),
                    "device": args.device,
                    "python": sys.version.split()[0],
                },
                fh,
            )
        return 0

    with open(args.text_file, "r", encoding="utf-8") as fh:
        text = fh.read().strip()
    if not text:
        print("[kokoro] empty text", file=sys.stderr)
        return 2

    pipeline = KPipeline(lang_code=args.lang, repo_id=args.repo, device=args.device)
    loaded = time.time()

    audio_parts: list = []
    words: list[dict] = []
    cursor = 0.0
    chunks = 0
    for result in pipeline(text, voice=args.voice, speed=args.speed):
        audio = result.audio
        if audio is None:
            continue
        samples = audio.detach().cpu().numpy().astype("float32").reshape(-1)
        dur = len(samples) / SAMPLE_RATE
        words.extend(words_from_pred(result.phonemes, result.pred_dur, result.graphemes, cursor, dur))
        audio_parts.append(samples)
        cursor += dur + CHUNK_PAUSE
        chunks += 1

    if not audio_parts:
        print("[kokoro] the model produced no audio", file=sys.stderr)
        return 3

    audio = np.concatenate([np.concatenate(audio_parts), np.zeros(int(CHUNK_PAUSE * SAMPLE_RATE), dtype="float32")])
    # 6 ms de-click on both ends; nothing else is processed, so the take stays raw
    edge = int(0.006 * SAMPLE_RATE)
    if len(audio) > 2 * edge:
        audio[:edge] *= np.linspace(0, 1, edge, dtype="float32")
        audio[-edge:] *= np.linspace(1, 0, edge, dtype="float32")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    sf.write(args.out, audio, SAMPLE_RATE, subtype="PCM_16")

    synth_seconds = time.time() - loaded
    with open(args.meta, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "ok": True,
                "provider": "kokoro",
                "model": f"Kokoro-82M ({args.repo})",
                "kokoro_version": version,
                "torch": torch.__version__,
                "device": args.device,
                "cuda": bool(torch.cuda.is_available()),
                "voice": args.voice,
                "lang_code": args.lang,
                "speed": args.speed,
                "sample_rate": SAMPLE_RATE,
                "duration": round(len(audio) / SAMPLE_RATE, 3),
                "chunks": chunks,
                "words": words,
                "alignment": "pred_dur" if all(w.get("source") == "pred_dur" for w in words) else "mixed",
                "timing": {
                    "load_seconds": round(loaded - started, 2),
                    "synth_seconds": round(synth_seconds, 2),
                    "realtime_factor": round(synth_seconds / max(len(audio) / SAMPLE_RATE, 1e-6), 2),
                },
            },
            fh,
            ensure_ascii=False,
        )
    print(
        f"[kokoro] {len(audio) / SAMPLE_RATE:.2f}s in {synth_seconds:.1f}s "
        f"({chunks} chunk(s), {len(words)} words, device={args.device})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
