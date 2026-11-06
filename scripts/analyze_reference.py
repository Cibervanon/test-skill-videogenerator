#!/usr/bin/env python3
"""Analyse one or more reference videos and emit structured production data.

Usage:
    python scripts/analyze_reference.py --input Ejemplos/Video/foo.mp4 --out projects/demo/analysis
    python scripts/analyze_reference.py --input a.mp4 b.mp4 --summary references/measurements.json

Outputs (per input, under --out/<stem>/):
    video_metadata.json   probe + shots + palette + motion + audio
    scene_breakdown.json  shot list with timestamps
    reference_style.md    human-readable report
    frames/               representative frames (3 per shot)
    contact_sheet.jpg     tiled review sheet
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acs import audio as audio_mod
from acs import frames as frames_mod
from acs import motion as motion_mod
from acs import palette as palette_mod
from acs import scenes as scenes_mod
from acs.ffmpeg import FFmpegError, Tools, summarize
from acs.report import build_markdown


def analyze_one(tools: Tools, path: str, out_dir: str, *, quick: bool = False) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    meta = summarize(tools, path)
    duration = meta["duration"]

    scenes = scenes_mod.analyze(tools, path, duration)
    frames_dir = os.path.join(out_dir, "frames")
    extracted = frames_mod.shot_frames(tools, path, scenes["shots"], frames_dir, per_shot=2 if quick else 3)
    sheet = os.path.join(out_dir, "contact_sheet.jpg")
    has_sheet = frames_mod.contact_sheet(tools, frames_dir, sheet) if extracted else False

    result = {
        **meta,
        "scenes": scenes,
        "palette": palette_mod.extract(tools, path, fps=0.5 if quick else 1.0),
        "motion": motion_mod.analyze(tools, path, fps=2.0 if quick else 3.0),
        "audio_analysis": audio_mod.analyze(tools, path) if meta.get("audio") else {},
        "frames": extracted,
        "contact_sheet": "contact_sheet.jpg" if has_sheet else None,
        "generated_by": "ai-cinematic-studio/scripts/analyze_reference.py",
        "limits": [
            "scene score is frame-difference, not semantic shot understanding",
            "motion model is translation-only (no zoom/rotation/parallax)",
            "no OCR, no object detection, no speaker diarisation without external models",
        ],
    }

    with open(os.path.join(out_dir, "video_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    with open(os.path.join(out_dir, "scene_breakdown.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "duration": duration,
                "shots": scenes["shots"],
                "hard_cuts": scenes["hard_cuts"],
                "shot_duration_stats": scenes["shot_duration_stats"],
            },
            fh,
            indent=2,
        )
    with open(os.path.join(out_dir, "reference_style.md"), "w", encoding="utf-8") as fh:
        fh.write(build_markdown(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse reference videos deterministically.")
    parser.add_argument("--input", nargs="+", required=True, help="video file(s)")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--summary", help="write a compact cross-video summary JSON here")
    parser.add_argument("--quick", action="store_true", help="lower sampling rates (faster, less precise)")
    args = parser.parse_args(argv)

    try:
        tools = Tools.detect()
    except FFmpegError as exc:
        print(f"[analysis] {exc}", file=sys.stderr)
        return 2

    summary = []
    failures = 0
    for path in args.input:
        if not os.path.exists(path):
            print(f"[analysis] missing input: {path}", file=sys.stderr)
            failures += 1
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)[:60]
        out_dir = os.path.join(args.out, safe)
        print(f"[analysis] {path} -> {out_dir}", flush=True)
        try:
            result = analyze_one(tools, path, out_dir, quick=args.quick)
        except FFmpegError as exc:
            print(f"[analysis] FAILED {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        summary.append(
            {
                "file": result["file"],
                "duration": result["duration"],
                "resolution": (
                    f"{result['video']['width']}x{result['video']['height']}" if result["video"] else None
                ),
                "fps": result["video"]["fps"] if result["video"] else None,
                "shots": result["scenes"]["shot_count"],
                "soft_cuts": result["scenes"]["cut_count_soft"],
                "cuts_per_min_soft": result["scenes"]["cuts_per_minute_soft"],
                "shot_mean": result["scenes"]["shot_duration_stats"]["mean"],
                "shot_max": result["scenes"]["shot_duration_stats"]["max"],
                "palette": [p["hex"] for p in result["palette"]["palette"][:6]],
                "mean_motion_energy": result["motion"]["mean_motion_energy"],
                "pan_ratio": result["motion"]["pan_ratio"],
                "mean_volume_db": result["audio_analysis"].get("loudness", {}).get("mean_volume_db"),
                "active_ratio": result["audio_analysis"].get("activity", {}).get("active_ratio"),
                "analysis_dir": os.path.relpath(out_dir),
            }
        )

    if args.summary:
        os.makedirs(os.path.dirname(os.path.abspath(args.summary)), exist_ok=True)
        with open(args.summary, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "generated_by": "scripts/analyze_reference.py",
                    "videos": summary,
                    "method": {
                        "cuts": "ffmpeg select 'gt(scene,T)' + metadata=print",
                        "palette": "k-means k=6 on 1fps 48px decode",
                        "motion": "SAD translation search ±6px",
                        "audio": "volumedetect + 8kHz RMS envelope",
                    },
                },
                fh,
                indent=2,
            )
        print(f"[analysis] summary -> {args.summary}", flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
