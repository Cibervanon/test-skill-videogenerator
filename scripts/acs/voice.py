"""Voice and narration, provider-agnostic.

Two providers, one contract:

* ``local``      — never touches the network and never spends. It writes the
                   *timing plan*: which words are spoken in which shot, with
                   word-level start/end times at a measured reading pace. There
                   is no speech audio, and the module says so instead of
                   pretending.
* ``elevenlabs`` — the real take, with character-level alignment converted to
                   word timings. It is only reachable when a Voice ID and a key
                   are configured *and* the caller passes ``authorize=True``;
                   otherwise it raises before any request is built.

Calls are cached by a hash of (text, voice id, settings), so retuning pauses
never pays twice. Costs are appended to the project's ``costs.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass

ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
DEFAULT_OUTPUT = "mp3_44100_128"
# Measured against the reference corpus: 2.3-2.6 words a second of narration.
WORDS_PER_SECOND = 2.45
WORD_SECONDS = 0.3
WORD_GAP = 0.07


class VoiceError(RuntimeError):
    """Raised before any spend or partial write."""


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def load_voices(root: str) -> dict:
    return read_json(os.path.join(root, "config", "voices.json"), {}) or {}


def shot_windows(project: dict) -> list[dict]:
    """Shot start/end in seconds, using the same overlap arithmetic as the renderer."""
    fps = project["format"]["fps"]
    default = project.get("transitionFrames", 0)
    shots = project["shots"]
    cursor = 0
    out = []
    for i, shot in enumerate(shots):
        frames = round(shot["seconds"] * fps)
        nxt = shots[i + 1].get("transitionIn", default) if i + 1 < len(shots) else 0
        out.append({"id": shot["id"], "from": cursor, "frames": frames, "start": cursor / fps,
                    "end": (cursor + frames) / fps})
        cursor += frames - nxt
    return out


def speaker_of(shot: dict, project: dict | None = None) -> str:
    """Resolve the voice for a line.

    A project in ``narration`` mode uses one narrator for every line unless the
    shot explicitly marks itself as character dialogue. This is deliberately
    stronger than looking at the visible actor: narration describes what the
    audience sees, so the actor on screen must not become the speaker.
    """
    if project and project.get("narration") and not shot.get("dialogue"):
        return "narrator"
    # A shot may name its narrator explicitly; otherwise the first actor speaks.
    if shot.get("speaker"):
        return shot["speaker"]
    actors = shot.get("actors") or []
    for actor in actors:
        if actor.get("speaks") or actor.get("line"):
            return actor["id"]
    return actors[0]["id"] if actors else "narrator"


def words_for(text: str, start: float, end: float) -> list[dict]:
    """Word timings for a line, compressed to fit inside its shot (estimated)."""
    tokens = [t for t in re.split(r"\s+", text.strip()) if t]
    if not tokens:
        return []
    need = len(tokens) * (WORD_SECONDS + WORD_GAP)
    span = max(0.4, end - start - 0.12)
    scale = min(1.0, span / need)
    out, t = [], start + 0.06
    for token in tokens:
        dur = WORD_SECONDS * scale
        out.append({"w": token, "s": round(t, 3), "e": round(t + dur, 3), "p": ""})
        t += dur + WORD_GAP * scale
    return out


def plan(project: dict) -> dict:
    shots = {s["id"]: s for s in project["shots"]}
    windows = shot_windows(project)
    lines = []
    for window in windows:
        shot = shots[window["id"]]
        text = (shot.get("line") or "").strip()
        if not text:
            continue
        lines.append(
            {
                "shot": window["id"],
                "scene": shot.get("scene", ""),
                "speaker": speaker_of(shot, project),
                "text": text,
                "start": round(window["start"], 3),
                "end": round(window["end"], 3),
                "words": words_for(text, window["start"], window["end"]),
                "audio": None,
                "status": "planned",
                "estimated": True,
            }
        )
    project_end = windows[-1]["end"] if windows else 0.0
    return {
        "provider": "local",
        "speech": False,
        "narration": bool(project.get("narration")),
        "project_seconds": round(project_end, 3),
        "total_lines": len(lines),
        "total_words": sum(len(l["words"]) for l in lines),
        "lines": lines,
    }


def _cache_paths(root: str, key: str) -> tuple[str, str]:
    base = os.path.join(root, "assets", "voice_cache")
    return os.path.join(base, f"{key}.mp3"), os.path.join(base, f"{key}.json")


def _hash(text: str, voice_id: str, settings: dict) -> str:
    raw = json.dumps([text, voice_id, settings], sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def elevenlabs_available(voice: dict, voices_config: dict) -> tuple[bool, str]:
    voice_id = (voice or {}).get("voice_id")
    if not voice_id:
        return False, "no voice_id configured for this character (choose one in your account)"
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return False, "ELEVENLABS_API_KEY is not set in the environment"
    if not voices_config.get("authorize_spend", False):
        return False, "config/voices.json has authorize_spend=false (explicit approval required)"
    return True, "ok"


def synthesize_elevenlabs(text: str, voice: dict, voices_config: dict, *, authorize: bool) -> dict:
    """One ElevenLabs take. Never called unless the caller authorised the spend."""
    ok, reason = elevenlabs_available(voice, voices_config)
    if not ok:
        raise VoiceError(f"ElevenLabs is not usable: {reason}")
    if not authorize:
        raise VoiceError(
            "refusing to spend ElevenLabs credits: pass --authorize-spend after the user approves "
            f"(the take is {len(text)} characters, about {len(text)} credits)"
        )

    import urllib.request

    defaults = voices_config.get("defaults", {})
    settings = {**defaults.get("settings", {}), **(voice.get("settings") or {})}
    payload = {
        "text": text,
        "model_id": voice.get("model") or defaults.get("model", "eleven_multilingual_v2"),
        "voice_settings": settings,
    }
    url = ENDPOINT.format(voice_id=voice["voice_id"]) + f"?output_format={voice.get('output_format', DEFAULT_OUTPUT)}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 (documented endpoint)
        body = json.loads(response.read())
    return {"body": body, "seconds": time.time() - started, "settings": settings, "payload": payload}


def alignment_to_words(alignment: dict) -> list[dict]:
    words: list[dict] = []
    current = None
    for char, start, end in zip(
        alignment.get("characters", []),
        alignment.get("character_start_times_seconds", []),
        alignment.get("character_end_times_seconds", []),
    ):
        if re.match(r"[\w'’]", char):
            if current is None:
                current = {"w": "", "s": float(start), "e": float(end), "p": ""}
            current["w"] += char
            current["e"] = float(end)
        else:
            if current is not None:
                words.append(current)
                current = None
            if words and char.strip():
                words[-1]["p"] += char
    if current is not None:
        words.append(current)
    for word in words:
        word["s"], word["e"] = round(word["s"], 3), round(word["e"], 3)
    return words


def generate(
    project_dir: str,
    project: dict,
    *,
    root: str = ".",
    provider: str = "local",
    authorize: bool = False,
    allow_download: bool = False,
) -> dict:
    """Write the voice plan (and, when authorised, the takes) for a project."""
    voices_config = load_voices(root)
    result = plan(project)

    if provider == "local":
        result["note"] = (
            "LOCAL: timings only, no speech audio and no network. The score keeps carrying the film; "
            "run the elevenlabs provider with --authorize-spend to hear the lines."
        )
    elif provider == "kokoro":
        # Local take: torch lives in .venv-kokoro, this process never imports it.
        from . import kokoro_tts

        config = kokoro_tts.load_config(root)
        voices_available = set((config.get("voices") or {}).keys())
        for line in result["lines"]:
            speaker = line["speaker"] if line["speaker"] in voices_available else "narrator"
            speed = float((config.get("speed") or {}).get(speaker, 1.0))
            key = kokoro_tts.cache_key(line["text"], speaker, speed, config)
            wav_path, meta_path = kokoro_tts._cache_paths(root, config, key)
            if os.path.exists(wav_path) and os.path.exists(meta_path):
                meta = read_json(meta_path, {}) or {}
                line["status"] = "cached"
            else:
                meta = kokoro_tts.synthesize(
                    root,
                    config,
                    text=line["text"],
                    speaker=speaker,
                    speed=speed,
                    out_wav=wav_path,
                    meta_path=meta_path,
                    allow_download=allow_download,
                )
                write_json(meta_path, meta)
                line["status"] = "generated"
            line["audio"] = os.path.relpath(wav_path, project_dir).replace(os.sep, "/")
            line["audio_duration"] = meta.get("duration")
            # The worker times words from zero inside its own take; the film clock
            # starts at the line's slot, and words.json feeds the cut.
            shift = float(line["start"])
            line["words"] = [
                {**w, "s": round(float(w["s"]) + shift, 3), "e": round(float(w["e"]) + shift, 3)}
                for w in (meta.get("words") or line["words"])
            ]
            line["estimated"] = meta.get("alignment") != "pred_dur"
            line["alignment"] = meta.get("alignment")
            line["model"] = meta.get("model")
            line["voice"] = meta.get("voice")
            line["speaker"] = speaker
            line["device"] = meta.get("device")
            line["cost_usd"] = 0.0
            line["overflow"] = round(max(0.0, line["start"] + float(meta.get("duration") or 0) - line["end"]), 3)
        result["provider"] = "kokoro"
        result["speech"] = True
        result["narration"] = bool(project.get("narration"))
        result["costs"] = [{"shot": l["shot"], "usd": 0.0, "cached": l["status"] == "cached"} for l in result["lines"]]
        result["credits"] = 0
        result["model"] = config.get("model_id", "Kokoro-82M")
        result["alignment"] = config.get("alignment", "pred_dur")
        project_end = shot_windows(project)[-1]["end"]
        result["stem"] = os.path.relpath(
            kokoro_tts.build_stem(root, project_dir, result["lines"], total_seconds=project_end), project_dir
        ).replace(os.sep, "/")
        result["note"] = "LOCAL Kokoro: audio, timings and stem generated on this machine. No network at synthesis time, no credits."
        overflows = [l for l in result["lines"] if l.get("overflow", 0) > 0]
        if overflows:
            result["overflow"] = [{"shot": l["shot"], "seconds": l["overflow"]} for l in overflows]
    elif provider == "elevenlabs":
        taken = []
        for line in result["lines"]:
            voice = (voices_config.get("voices") or {}).get(line["speaker"]) or {}
            key = _hash(line["text"], voice.get("voice_id", ""), voice.get("settings") or {})
            audio_path, meta_path = _cache_paths(root, key)
            if os.path.exists(audio_path) and os.path.exists(meta_path):
                cached = read_json(meta_path, {})
                line["words"] = cached.get("words", line["words"])
                line["audio"] = os.path.relpath(audio_path, project_dir).replace(os.sep, "/")
                line["status"] = "cached"
                line["estimated"] = False
                taken.append({"shot": line["shot"], "credits": 0, "cached": True})
                continue
            import base64

            response = synthesize_elevenlabs(line["text"], voice, voices_config, authorize=authorize)
            body = response["body"]
            audio = base64.b64decode(body["audio_base64"])
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            with open(audio_path, "wb") as fh:
                fh.write(audio)
            words = alignment_to_words(body.get("alignment", {}))
            write_json(meta_path, {"words": words, "text": line["text"], "voice_id": voice.get("voice_id")})
            line["words"] = words
            line["audio"] = os.path.relpath(audio_path, project_dir).replace(os.sep, "/")
            line["status"] = "generated"
            line["estimated"] = False
            line["model"] = response["payload"]["model_id"]
            taken.append({"shot": line["shot"], "credits": len(line["text"]), "cached": False})
        result["provider"] = "elevenlabs"
        result["speech"] = True
        result["costs"] = taken
        result["credits"] = sum(t["credits"] for t in taken)
        _log_costs(project_dir, taken)
    else:
        raise VoiceError(f"unknown voice provider: {provider}")

    out_dir = os.path.join(project_dir, "generation", "voice")
    write_json(os.path.join(out_dir, "voice_plan.json"), result)
    write_json(os.path.join(out_dir, "words.json"), [w for line in result["lines"] for w in line["words"]])
    return result


def _log_costs(project_dir: str, taken: list[dict]) -> None:
    path = os.path.join(project_dir, "generation", "voice", "costs.json")
    rows = read_json(path, []) or []
    rows.extend({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **t} for t in taken)
    write_json(path, rows)
