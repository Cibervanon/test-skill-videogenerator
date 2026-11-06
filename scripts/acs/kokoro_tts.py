"""Kokoro as a first-class local voice provider.

Split of responsibilities:

* this module (system Python 3.14) owns configuration, cache, the timeline stem
  and the contract with the rest of the pipeline;
* ``kokoro_worker.py`` (the `.venv-kokoro` interpreter, 3.12) owns torch and the
  model.

That split exists because torch has no 3.14 wheels. It also keeps the skill's
main environment free of a 1.2 GB dependency it would never import itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import wave

import numpy as np

CONFIG_VERSION = 2


class KokoroError(RuntimeError):
    """Raised before a partial write or an unauthorised download."""


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def load_config(root: str = ".") -> dict:
    config = read_json(os.path.join(root, "config", "kokoro.json"), None)
    if not config:
        raise KokoroError("config/kokoro.json is missing")
    if not config.get("voices"):
        raise KokoroError("config/kokoro.json declares no voices")
    return config


def interpreter(root: str, config: dict) -> str:
    override = os.environ.get("KOKORO_PYTHON")
    path = override or config.get("python", "")
    if not path:
        raise KokoroError("no Kokoro interpreter configured (config/kokoro.json: python)")
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    return path


def available(root: str, config: dict) -> tuple[bool, str]:
    path = interpreter(root, config)
    if not os.path.exists(path):
        return False, (
            f"Kokoro interpreter not found at {os.path.relpath(path, root)}: create it with "
            "`python -m venv .venv-kokoro` on Python 3.12 and `pip install kokoro soundfile espeakng-loader`"
        )
    worker = os.path.join(root, "scripts", "acs", "kokoro_worker.py")
    meta = os.path.join(root, ".tmp", "kokoro_probe.json")
    os.makedirs(os.path.dirname(meta), exist_ok=True)
    try:
        result = subprocess.run(
            # -P keeps scripts/acs off sys.path: its module names collide with
            # numpy's bootstrap ("no known parent package") when the worker runs
            # as a plain script.
            [path, "-P", worker, "--text-file", os.devnull, "--voice", "probe", "--out", os.devnull, "--meta", meta, "--probe"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=180,
            cwd=root,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"could not run the Kokoro worker: {exc}"
    probe = read_json(meta, {}) or {}
    if result.returncode != 0 or not probe.get("ok"):
        tail = (result.stderr or "").strip().splitlines()[-3:]
        return False, "Kokoro worker failed: " + (" / ".join(tail) or "no output")
    return True, (
        f"kokoro {probe.get('kokoro')} · torch {probe.get('torch')} · "
        f"{'cuda' if probe.get('cuda') else 'cpu'} on Python {probe.get('python')}"
    )


def model_cached(root: str, config: dict, voice: str) -> bool:
    """True when the weights and this voice are already on disk (no download)."""
    models = os.path.join(root, config.get("models_dir", ".models/kokoro"))
    snapshots = os.path.join(models, "hub", "models--hexgrad--Kokoro-82M", "snapshots")
    if not os.path.isdir(snapshots):
        return False
    for revision in os.listdir(snapshots):
        base = os.path.join(snapshots, revision)
        if os.path.exists(os.path.join(base, "config.json")) and os.path.exists(
            os.path.join(base, "voices", f"{voice}.pt")
        ):
            return True
    return False


def voice_spec(config: dict, speaker: str) -> dict:
    voices = config.get("voices") or {}
    spec = voices.get(speaker)
    if not spec:
        raise KokoroError(f"no Kokoro voice for '{speaker}': available are {', '.join(voices) or 'none'}")
    if not spec.get("kokoro"):
        raise KokoroError(f"voice entry for '{speaker}' has no kokoro id")
    return spec


def cache_key(text: str, speaker: str, speed: float, config: dict) -> str:
    raw = json.dumps(
        [
            "kokoro",
            config.get("model_id"),
            (config.get("voices", {}).get(speaker) or {}).get("kokoro"),
            config.get("lang_code"),
            round(float(speed), 3),
            CONFIG_VERSION,
            text,
        ],
        sort_keys=True,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _cache_paths(root: str, config: dict, key: str) -> tuple[str, str]:
    base = os.path.join(root, config.get("cache_dir", "assets/voice_cache/kokoro"))
    return os.path.join(base, f"{key}.wav"), os.path.join(base, f"{key}.json")


def synthesize(
    root: str,
    config: dict,
    *,
    text: str,
    speaker: str,
    speed: float,
    out_wav: str,
    meta_path: str,
    allow_download: bool = False,
    timeout: int = 600,
) -> dict:
    """One take, straight from the worker. Refuses an unauthorised download."""
    spec = voice_spec(config, speaker)
    has_runtime, reason = available(root, config)
    if not has_runtime:
        raise KokoroError(f"Kokoro is not usable: {reason}")
    if not allow_download and not model_cached(root, config, spec["kokoro"]):
        raise KokoroError(
            "Kokoro weights or this voice are not on disk yet: pass --allow-model-download "
            "(about 350 MB from huggingface.co/hexgrad/Kokoro-82M, Apache-2.0)"
        )
    text_path = out_wav + ".txt"
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    with open(text_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    cmd = [
        interpreter(root, config),
        # -P: keep the worker's own directory off sys.path. `scripts/acs` holds
        # modules whose names collide with numpy's bootstrap, which fails with
        # "attempted relative import with no known parent package".
        "-P",
        os.path.join(root, "scripts", "acs", "kokoro_worker.py"),
        "--text-file", text_path,
        "--voice", spec["kokoro"],
        "--lang", str(spec.get("lang_code") or config.get("lang_code", "e")),
        "--speed", str(speed),
        "--repo", str(config.get("repo_id", "hexgrad/Kokoro-82M")),
        "--device", str(config.get("device", "cpu")),
        "--models-dir", os.path.join(root, config.get("models_dir", ".models/kokoro")),
        "--out", out_wav,
        "--meta", meta_path,
    ]
    started = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=timeout, cwd=root)
    os.remove(text_path)
    meta = read_json(meta_path, {}) or {}
    if result.returncode != 0 or not meta.get("ok"):
        tail = (result.stderr or "").strip().splitlines()[-6:]
        raise KokoroError("Kokoro failed: " + (" / ".join(tail) or f"exit {result.returncode}"))
    meta["wall_seconds"] = round(time.time() - started, 2)
    meta["text"] = text
    meta["speaker"] = speaker
    return meta


def _wav_duration(path: str) -> float:
    with wave.open(path, "rb") as fh:
        return fh.getnframes() / float(fh.getframerate())


def build_stem(
    root: str, project_dir: str, lines: list[dict], sample_rate: int = 24000, total_seconds: float | None = None
) -> str:
    """Place every line on one silent timeline so the mixer has a real stem.

    Takes the lines from this run, never from the plan file: the plan is written
    after the stem, so reading it here would mix the previous take's paths.
    """
    lines = [l for l in lines if l.get("audio")]
    total = max([l["start"] + float(l.get("audio_duration") or 0) for l in lines] + [float(total_seconds or 0)])
    frames = int(np.ceil((total + 0.25) * sample_rate))
    buffer = np.zeros(frames, dtype=np.float32)
    ordered = sorted(lines, key=lambda l: float(l["start"]))
    for index, line in enumerate(ordered):
        path = os.path.join(project_dir, line["audio"])
        with wave.open(path, "rb") as fh:
            if fh.getframerate() != sample_rate or fh.getnchannels() != 1:
                raise KokoroError(
                    f"{path}: expected mono {sample_rate} Hz WAV from the worker, got "
                    f"{fh.getnchannels()}ch {fh.getframerate()}Hz"
                )
            data = np.frombuffer(fh.readframes(fh.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        at = int(round(line["start"] * sample_rate))
        # Shot windows overlap on dissolves, so two consecutive takes were summed
        # into each other (S01/S02 and S03/S04, 0.16 s each). A line ends where
        # the next one starts: a short fade stops the cut from clicking, and no
        # word is ever spoken twice.
        limit = frames
        if index + 1 < len(ordered):
            limit = min(frames, int(round(float(ordered[index + 1]["start"]) * sample_rate)))
        end = min(limit, at + len(data))
        if end <= at:
            continue
        chunk = data[: end - at].copy()
        if len(chunk) < len(data):
            fade = min(len(chunk), int(0.02 * sample_rate))
            if fade > 0:
                chunk[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
        buffer[at:end] += chunk
    # Kokoro is quiet by design (its takes peak around -6 dBFS). Normalise the
    # stem to -1.5 dBFS peak so the duck has something to sit under; no dynamics
    # processing touches the speech itself.
    peak = float(np.abs(buffer).max())
    if peak > 1e-6:
        buffer *= 0.84 / peak
    out = os.path.join(project_dir, "generation", "voice", "voice.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with wave.open(out, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(sample_rate)
        fh.writeframes((buffer * 32767).astype("<i2").tobytes())
    return out


def fit_shots(project: dict, lines: list[dict], *, margin: float = 0.25, min_seconds: float = 0.6) -> tuple[dict, list[dict]]:
    """Let the voice push the cut: a shot never ends before its line does."""
    shots = [dict(s) for s in project["shots"]]
    by_id = {s["id"]: s for s in shots}
    changes = []
    windows = {}
    cursor = 0.0
    fps = project["format"]["fps"]
    for i, shot in enumerate(shots):
        start = cursor / fps
        windows[shot["id"]] = start
        cursor += round(shot["seconds"] * fps) - (shots[i + 1].get("transitionIn", 0) if i + 1 < len(shots) else 0)
    for line in lines:
        shot = by_id.get(line["shot"])
        if not shot:
            continue
        need = float(line.get("audio_duration") or 0) + margin
        offset = line["start"] - windows[line["shot"]]
        if need + offset <= float(shot["seconds"]) + 1e-6:
            continue
        new = max(min_seconds, round(need + offset, 3))
        changes.append({"shot": shot["id"], "from": shot["seconds"], "to": new, "reason": "voice overflow"})
        shot["seconds"] = new
    return {**project, "shots": shots}, changes
