#!/usr/bin/env python3
"""AI CINEMATIC STUDIO — pipeline CLI.

Stages (each one is independently runnable and resumable):

    status        show mode, providers, budget and what is installed
    analysis      probe/scan reference video(s) into the project
    preproduction write script, storyboard, bibles, continuity report
    audio         synthesise the soundtrack (deterministic, local)
    render        render the Remotion composition to a silent MP4
    assemble      mux picture + soundtrack, normalise loudness
    qa            run the quality gates and write the report
    produce       analysis → preproduction → audio → render → assemble → qa

Examples:
    python scripts/studio.py status
    python scripts/studio.py produce --project projects/demo_001 --reference "Ejemplos/Video/x.mp4"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from acs import assemble as assemble_mod
from acs import generated as generated_mod
from acs import audio_gen, edit as edit_mod, library, mixcheck, project as project_mod, qa as qa_mod, storyboard as storyboard_mod
from acs import director as director_mod, evaluate as evaluate_mod, feedback as feedback_mod, inspect as inspect_mod
from acs import ui_director as ui_director_mod
from acs import av_director as av_director_mod, avqa as avqa_mod
from acs import voice as voice_mod
from acs import asset_forge
from acs import references as references_mod
from acs.ffmpeg import FFmpegError, Tools, summarize
from acs.providers import build_registry, load_config
from acs.providers.base import ProviderRequest
from acs.selector import plan_project

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "studio.config.json")
PROJECT_MANIFEST = os.path.join(ROOT, "studio", "src", "data", "project.json")
CAST_PATH = os.path.join(ROOT, "studio", "src", "data", "cast.json")


def load_project(path: str | None = None) -> dict:
    with open(path or PROJECT_MANIFEST, "r", encoding="utf-8") as fh:
        return json.load(fh)


class ManifestBusy(RuntimeError):
    """Another render owns the single active manifest."""


@contextmanager
def manifest_lock(timeout: float = 5.0):
    """Serialise activation of the one file Remotion imports at bundle time.

    Remotion reads ``studio/src/data/project.json``, so two concurrent renders
    would otherwise swap the film under each other. The lock is fail-fast: the
    second render gets a clear error instead of silently rendering the wrong
    project.
    """
    os.makedirs(os.path.dirname(os.path.abspath(PROJECT_MANIFEST)), exist_ok=True)
    lock_path = PROJECT_MANIFEST + ".lock"
    started = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            # A crashed process must not block every future render.
            try:
                if time.time() - os.path.getmtime(lock_path) > 3 * 3600:
                    os.remove(lock_path)
                    continue
            except OSError:
                pass
            if time.time() - started >= timeout:
                raise ManifestBusy(
                    f"another render owns {PROJECT_MANIFEST} (lock {lock_path}). "
                    "Wait for it to finish; the lock expires after 3 hours."
                )
            time.sleep(0.2)
    try:
        os.write(fd, f"{os.getpid()} {time.time():.3f}\n".encode("ascii"))
        os.close(fd)
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass


@contextmanager
def use_manifest(path: str | None, *, lock_timeout: float = 5.0):
    """Temporarily make a manifest active for the Remotion CLI.

    Remotion imports ``studio/src/data/project.json`` at bundle time. Commands
    that accept ``--manifest`` must therefore activate that file for the child
    renderer, then restore the previous bytes even if the render fails. Without
    this, a render could silently use the previous film while reporting success.
    """
    if not path:
        yield
        return
    with manifest_lock(timeout=lock_timeout):
        previous = None
        if os.path.exists(PROJECT_MANIFEST):
            with open(PROJECT_MANIFEST, "rb") as fh:
                previous = fh.read()
        project = load_project(path)
        os.makedirs(os.path.dirname(PROJECT_MANIFEST), exist_ok=True)
        with open(PROJECT_MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(project, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        try:
            yield project
        finally:
            if previous is None:
                if os.path.exists(PROJECT_MANIFEST):
                    os.remove(PROJECT_MANIFEST)
            else:
                with open(PROJECT_MANIFEST, "wb") as fh:
                    fh.write(previous)


def load_cast() -> dict:
    with open(CAST_PATH, "r", encoding="utf-8") as fh:
        base = json.load(fh)
    return generated_mod.merge_cast(ROOT, base)


def project_paths(root: str) -> dict:
    return {
        "root": root,
        "analysis": os.path.join(root, "analysis"),
        "preproduction": os.path.join(root, "preproduction"),
        "audio": os.path.join(root, "generation", "audio", "score.wav"),
        "silent": os.path.join(root, "output", "picture_silent.mp4"),
        "delivery": os.path.join(root, "output", "final_video.mp4"),
        "preview": os.path.join(root, "output", "final_video_preview.mp4"),
        "quality": os.path.join(root, "quality"),
        "logs": os.path.join(root, "logs"),
    }


def cmd_status(args) -> int:
    config = load_config(CONFIG_PATH)
    registry = build_registry(config, project_dir=args.project)
    status = registry.status()
    status["tools"] = {}
    try:
        tools = Tools.detect()
        status["tools"] = {"ffmpeg": tools.ffmpeg, "ffprobe": tools.ffprobe}
    except FFmpegError as exc:
        status["tools"] = {"error": str(exc)}
    print(json.dumps(status, indent=2))
    return 0


def cmd_analysis(args) -> int:
    from analyze_reference import analyze_one

    tools = Tools.detect()
    paths = project_paths(args.project)
    os.makedirs(paths["analysis"], exist_ok=True)
    results = []
    for ref in args.reference:
        stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in os.path.splitext(os.path.basename(ref))[0])[:60]
        out = os.path.join(paths["analysis"], stem)
        print(f"[analysis] {ref}")
        results.append(analyze_one(tools, ref, out, quick=args.quick))
    return 0


def cmd_preproduction(args) -> int:
    paths = project_paths(args.project)
    project_mod.init_project(os.path.dirname(paths["root"]), os.path.basename(paths["root"]), title=args.title)
    project = load_project(args.manifest)
    cast = load_cast()
    result = project_mod.write_preproduction(paths["root"], project, cast, source_project_path=args.manifest or PROJECT_MANIFEST)
    print(f"[preproduction] {result['storyboard']['total_shots']} shots, {result['storyboard']['total_seconds']}s")
    if not result["continuity"]["ok"]:
        print("[preproduction] continuity issues: " + "; ".join(result["continuity"]["issues"]))
    return 0 if result["continuity"]["ok"] else 1


def cmd_audio(args) -> int:
    config = load_config(CONFIG_PATH)
    registry = build_registry(config, project_dir=args.project)
    paths = project_paths(args.project)
    request = ProviderRequest(
        capability="audio.score",
        destination=paths["audio"],
        params={"project": args.manifest or PROJECT_MANIFEST, "seed": config.get("audio", {}).get("seed", 20261103)},
    )
    result = registry.execute("audio.score", request)
    print(f"[audio] {paths['audio']} ({result.meta.get('duration')}s, rms {result.meta.get('rms_db')} dBFS)")
    return 0


def cmd_render(args) -> int:
    config = load_config(CONFIG_PATH)
    registry = build_registry(config, project_dir=args.project)
    paths = project_paths(args.project)
    destination = os.path.abspath(args.out or paths["silent"])
    extra = [f"--concurrency={config.get('render', {}).get('concurrency', 4)}"]
    if args.frames:
        extra.append(f"--frames={args.frames}")
    request = ProviderRequest(
        capability="video.render",
        destination=destination,
        params={
            "entry": config.get("render", {}).get("entry", "src/index.ts"),
            "composition": config.get("render", {}).get("composition", "CinematicDemo"),
            "args": extra,
            "log": os.path.join(paths["logs"], "render.log"),
        },
    )
    with use_manifest(args.manifest):
        result = registry.execute("video.render", request)
    print(f"[render] {destination} in {result.meta.get('seconds')}s")
    return 0


def default_soundtrack(project: str, score: str) -> str:
    """Prefer the narrated mix when it exists.

    The score is the pre-voice bed. Defaulting to it produced a delivered MP4
    with music and effects but no narration, even though mix.wav existed.
    """
    mix = os.path.join(project, "generation", "audio", "mix.wav")
    return mix if os.path.exists(mix) else score


def cmd_assemble(args) -> int:
    config = load_config(CONFIG_PATH)
    tools = Tools.detect()
    paths = project_paths(args.project)
    audio = None if getattr(args, "silent", False) else (getattr(args, "audio", None) or default_soundtrack(args.project, paths["audio"]))
    if audio:
        print(f"[assemble] soundtrack: {audio}")
    report = assemble_mod.assemble(
        tools,
        video=paths["silent"],
        audio=audio,
        out=paths["delivery"],
        target_lufs=config.get("audio", {}).get("target_lufs", -16.0),
        true_peak_db=config.get("audio", {}).get("true_peak_db", -1.5),
        crf=config.get("render", {}).get("crf", 18),
        preset=config.get("render", {}).get("preset", "medium"),
        require_full_audio=not getattr(args, "allow_short_audio", False),
    )
    preview = assemble_mod.make_preview(tools, source=paths["delivery"], out=paths["preview"])
    print(f"[assemble] {report['output']} ({report['duration']}s, {report['size_bytes'] / 1e6:.1f} MB)")
    print(f"[assemble] preview {paths['preview']} ({preview['size_bytes'] / 1e6:.1f} MB)")
    project_mod.write_manifest(
        paths["root"],
        [paths["silent"], paths["audio"], paths["delivery"], paths["preview"]],
        extra={"delivery": report},
    )
    return 0


def cmd_qa(args) -> int:
    config = load_config(CONFIG_PATH)
    tools = Tools.detect()
    paths = project_paths(args.project)
    project = load_project(args.manifest)
    voice = os.path.join(args.project, "generation", "voice", "voice.wav")
    score = os.path.join(args.project, "generation", "audio", "score.wav")
    report = qa_mod.run_qa(
        tools,
        output=paths["delivery"],
        project=project,
        thresholds=config.get("qa"),
        out_dir=paths["quality"],
        voice_stem=voice if os.path.exists(voice) else None,
        score_stem=score if os.path.exists(score) else None,
    )
    for check in report["checks"]:
        mark = "PASS" if check["pass"] else "FAIL"
        print(f"[qa] {mark:4} {check['id']}: {check.get('value')} — {check.get('detail', '')}")
    print(f"[qa] overall: {'PASS' if report['ok'] else 'FAIL'}")
    return 0 if report["ok"] else 1


def cmd_produce(args) -> int:
    """Run the whole chain, stopping at the first hard failure."""
    paths = project_paths(args.project)
    project_mod.init_project(os.path.dirname(paths["root"]), os.path.basename(paths["root"]), title=args.title)

    if args.reference:
        project_mod.copy_reference(paths["root"], args.reference[0])
        if cmd_analysis(args) != 0:
            print("[produce] analysis failed", file=sys.stderr)
            return 1
    if cmd_preproduction(args) != 0:
        print("[produce] preproduction reported continuity issues", file=sys.stderr)
    if cmd_audio(args) != 0:
        return 1
    if cmd_render(args) != 0:
        return 1
    if cmd_assemble(args) != 0:
        return 1
    if cmd_qa(args) != 0:
        print("[produce] QA failed: delivery exists but is not accepted", file=sys.stderr)
        return 1
    print(f"[produce] done -> {paths['delivery']}")
    return 0


def cmd_assets(args) -> int:
    catalog = library.build(ROOT)
    action = args.action
    if action == "rebuild":
        print(f"[assets] {len(catalog['assets'])} assets -> assets/catalog.json {catalog['counts']}")
        return 0
    if action == "validate":
        result = library.validate(catalog, ROOT)
        for problem in result["problems"]:
            print(f"[assets] ! {problem}")
        print(f"[assets] {'OK' if result['ok'] else 'FAIL'} — {result['checked']} assets checked")
        return 0 if result["ok"] else 1
    if action == "show":
        asset = library.get(catalog, args.id or "", version=args.version)
        if not asset:
            print(f"[assets] no asset with id {args.id} (version {args.version})")
            return 1
        print(json.dumps(asset, indent=2, ensure_ascii=False))
        return 0
    if action == "reuse":
        project = load_project(args.manifest)
        report = library.reuse_report(project, catalog, ROOT)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report["missing"]:
            print("[assets] create or map the missing assets before rendering", file=sys.stderr)
        return 0 if report["ok"] else 1
    if action == "generate":
        if not args.prompt:
            print("[assets] --prompt is required for generate", file=sys.stderr)
            return 2
        result = asset_forge.create_bundle(
            args.prompt,
            ROOT,
            asset_id=args.id,
            style=args.style,
            resolution=args.resolution,
            aspect=args.aspect,
            license_=args.license,
            source=args.source,
            force=args.force,
            reference_ids=args.reference,
        )
        if not result.get("ok"):
            for problem in result.get("problems", []):
                print(f"[assets] ! {problem}", file=sys.stderr)
            return 1
        catalog = library.build(ROOT)
        created = [result["asset"]] + list(result.get("related") or [])
        for asset in created:
            print(f"[assets] created {asset['id']} v{asset['version']} — {asset['preview']}")
            asset = library.get(catalog, asset["id"]) or asset
            print(f"[assets]   {asset['type']} · {asset['style']} · {asset['license']} · {asset['status']}")
        validation = library.validate(catalog, ROOT)
        if not validation["ok"]:
            for problem in validation["problems"]:
                print(f"[assets] ! {problem}", file=sys.stderr)
            return 1
        print(f"[assets] library validated — {validation['checked']} assets")
        return 0
    if action == "versions":
        entry = generated_mod.load_registry(ROOT)
        entry = next((a for a in entry.get("assets", []) if a.get("id") == args.id), None)
        if not entry:
            print(f"[assets] no registry asset with id {args.id}")
            return 1
        for version in entry.get("versions", []):
            print(f"v{version.get('version')}  {version.get('created')}  {version.get('path')}")
        print(f"[assets] {len(entry.get('versions', []))} version(s); latest v{entry.get('version')}")
        return 0
    if action == "preview":
        asset = library.get(catalog, args.id or "", version=args.version)
        if not asset:
            print(f"[assets] no asset with id {args.id}")
            return 1
        print(asset.get("preview") or "(no explicit preview; derived asset renders from its source)")
        return 0
    if action == "similar":
        for asset in library.similar(catalog, args.id or "", limit=args.limit):
            print(f"{asset['similarity']:<6} {asset['id']:<30} {asset['type']:<14} {asset['name']}")
        return 0
    if action == "references":
        data = references_mod.load(ROOT)
        validation = references_mod.validate(data, ROOT)
        for ref in references_mod.search(data, query=args.query, purpose=args.purpose, tag=args.tag):
            print(f"{ref['id']:<32} {ref['purpose']:<12} {ref['name']}")
        print(f"[assets] {len(data.get('references', []))} reference(s), {'OK' if validation['ok'] else 'FAIL'}")
        return 0 if validation["ok"] else 1
    if action == "reference":
        try:
            record = references_mod.add(
                ROOT,
                name=args.name or "",
                purpose=args.purpose or "",
                source=args.path or "",
                license_=args.reference_license or "",
                origin=args.source or "user-provided",
                tags=(args.tags or "").split(","),
                applies_to=(args.applies_to or "").split(","),
                notes=args.notes or "",
                reference_id=args.id,
            )
        except ValueError as exc:
            print(f"[assets] ! {exc}", file=sys.stderr)
            return 1
        print(f"[assets] reference {record['id']} -> {record['source']}")
        return 0
    found = library.search(
        catalog,
        query=args.query,
        type_=args.type,
        tag=args.tag,
        style=args.style,
        scene=args.scene,
        character=args.character,
        usage=args.usage,
        compatible=args.compatible,
        limit=args.limit,
    )
    for asset in found:
        print(f"{asset['id']:<30} {asset['type']:<14} v{asset.get('version'):<4} {asset['name']}")
    print(f"[assets] {len(found)} match(es)")
    return 0


def cmd_compose(args) -> int:
    """Build a manifest through the catalogue: an unknown id fails, it never renders blank."""
    with open(args.spec, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    catalog = library.build(ROOT)
    result = library.compose(spec, catalog)
    if not result["ok"]:
        for problem in result["problems"]:
            print(f"[compose] ! {problem}", file=sys.stderr)
        return 1
    out = args.out or os.path.join(args.project, "manifest.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result["project"], fh, indent=2)
    print(f"[compose] {out} — {len(result['project']['shots'])} shots, every asset resolved")
    if args.write_active:
        with open(PROJECT_MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(result["project"], fh, indent=2)
        print(f"[compose] active manifest -> {PROJECT_MANIFEST}")
    return 0


def cmd_av(args) -> int:
    """Plan the audiovisual edit from a beat sheet, then audit it structurally."""
    with open(args.spec, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    planned = av_director_mod.plan(spec)
    if not planned["ok"]:
        for problem in planned["problems"]:
            print(f"[av] ! {problem}", file=sys.stderr)
        return 1
    catalog = library.build(ROOT)
    composed = library.compose(planned["manifest"], catalog)
    if not composed["ok"]:
        for problem in composed["problems"]:
            print(f"[av] ! {problem}", file=sys.stderr)
        return 1
    project_mod.init_project(os.path.dirname(os.path.abspath(args.project)), os.path.basename(args.project), title=spec.get("title"))
    manifest_path = os.path.join(args.project, "manifest.json")
    os.makedirs(args.project, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(composed["project"], fh, indent=2, ensure_ascii=False)
    paths = av_director_mod.write_plan(args.project, planned["record"])
    audit = avqa_mod.write(args.project, composed["project"])
    for shot in planned["record"]["shots"]:
        print(f"[av] {shot['id']} {shot['beat']:11s} {shot['scale']:6s} {shot['camera']:12s} {shot['seconds']:4.1f}s  {shot['cameraMotive']}")
    for warning in planned["warnings"]:
        print(f"[av] ! {warning}")
    print(f"[av] {planned['record']['edit']['shots']} planos · {planned['record']['edit']['seconds']}s · {planned['record']['edit']['sound_cues']} cue(s)")
    print(f"[av] creative QA: {audit['report']['summary']['headline']}")
    print(f"[av] manifest: {manifest_path}")
    print(f"[av] plan: {paths['markdown']}")
    if args.write_active:
        with open(PROJECT_MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(composed["project"], fh, indent=2, ensure_ascii=False)
        print(f"[av] active manifest -> {PROJECT_MANIFEST}")
    return 0


def cmd_avqa(args) -> int:
    project = load_project(args.manifest)
    result = avqa_mod.write(args.project, project)
    for check in result["report"]["checks"]:
        mark = "PASS" if check["pass"] else ("FAIL" if check["pass"] is False else "--  ")
        print(f"[avqa] {mark} {check['id']:22s} {check['status']:9s} {check['value']}")
    print(f"[avqa] {result['report']['summary']['headline']} · pendiente de revisión humana: {', '.join(result['report']['human_review'])}")
    if args.baseline:
        baseline = avqa_mod.audit(load_project(args.baseline))
        comparison = avqa_mod.compare(baseline, result["report"])
        path = avqa_mod.write_comparison(args.project, comparison)
        print(f"[avqa] before/after -> {path}")
    print(f"[avqa] {result['markdown']}")
    return 0 if result["report"]["summary"]["ok"] else 1


def cmd_edit(args) -> int:
    """Word-guided edit: nudge shot boundaries so captions open on spoken words."""
    project = load_project(args.manifest)
    words = voice_mod.read_json(os.path.join(args.project, "generation", "voice", "words.json"), []) or []
    if not words:
        print("[edit] no words.json: run `studio.py voice` first", file=sys.stderr)
        return 1
    result = edit_mod.align_manifest(project, words, tolerance=args.tolerance)
    out = os.path.join(args.project, "preproduction", "edit_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in result.items() if k != "project"}, fh, indent=2)
    for shift in result["shifts"]:
        mark = "ok " if shift.get("within_tolerance", True) else "!  "
        print(f"[edit] {mark}{shift['shot']}: drift {shift['drift']:+.2f}s (applied {shift['applied']:+.2f}s)")
    print(f"[edit] total shift {result['total_shift']:+.2f}s, tolerance ±{result['tolerance']}s -> {out}")
    return 0 if result["ok"] else 1


def cmd_voice(args) -> int:
    project = load_project(args.manifest)
    result = voice_mod.generate(
        args.project,
        project,
        root=ROOT,
        provider=args.provider,
        authorize=args.authorize_spend,
        allow_download=getattr(args, "allow_model_download", False),
    )
    print(
        f"[voice] provider={result['provider']} speech={result['speech']} "
        f"lines={result['total_lines']} words={result['total_words']}"
    )
    if result.get("credits"):
        print(f"[voice] ElevenLabs credits used: {result['credits']}")
    if result.get("model"):
        print(f"[voice] model {result['model']} · alignment {result.get('alignment')} · stem {result.get('stem')}")
    for line in result["lines"]:
        if line.get("audio_duration") is not None:
            mark = "!" if line.get("overflow", 0) > 0 else " "
            print(
                f"[voice] {mark} {line['shot']}: {line['audio_duration']:.2f}s audio in "
                f"{line['end'] - line['start']:.2f}s shot ({line['status']}, {line.get('voice')})"
            )
    if result.get("overflow"):
        print("[voice] lines longer than their shot: " + ", ".join(f"{o['shot']} +{o['seconds']:.2f}s" for o in result["overflow"]))
        if getattr(args, "fit_shots", False):
            from acs import kokoro_tts

            fitted, changes = kokoro_tts.fit_shots(project, result["lines"])
            out = os.path.join(args.project, "preproduction", "manifest_fitted.json")
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(fitted, fh, indent=2, ensure_ascii=False)
            for change in changes:
                print(f"[voice] shot {change['shot']}: {change['from']}s -> {change['to']}s ({change['reason']})")
            print(f"[voice] fitted manifest -> {out} (activate it deliberately; project.json is untouched)")
    if not result["speech"]:
        print(f"[voice] {result.get('note', '')}")
    return 0


def cmd_kokoro(args) -> int:
    from acs import kokoro_tts

    try:
        config = kokoro_tts.load_config(ROOT)
    except kokoro_tts.KokoroError as exc:
        print(f"[kokoro] {exc}", file=sys.stderr)
        return 1
    ok, detail = kokoro_tts.available(ROOT, config)
    print(f"[kokoro] runtime: {'ok' if ok else 'missing'} — {detail}")
    print(f"[kokoro] model: {config.get('model_id')} · lang {config.get('lang_code')} · device {config.get('device')}")
    for speaker, spec in (config.get("voices") or {}).items():
        cached = kokoro_tts.model_cached(ROOT, config, spec["kokoro"])
        print(f"[kokoro] {speaker:9s} -> {spec['kokoro']:9s} weights {'cached' if cached else 'not downloaded'}")
    return 0 if ok else 1


def cmd_subtitles(args) -> int:
    from acs import subtitles as subs

    project = load_project(args.manifest)
    del project
    out_dir = os.path.join(args.project, "generation", "voice")
    plan = json.load(open(os.path.join(out_dir, "voice_plan.json"), encoding="utf-8")) if os.path.exists(
        os.path.join(out_dir, "voice_plan.json")
    ) else None
    if not plan:
        print("[subtitles] no voice_plan.json: run `studio.py voice` first", file=sys.stderr)
        return 1
    cues = subs.from_plan(plan, max_words=args.max_words)
    path = os.path.join(args.project, "preproduction", "subtitles.srt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(subs.to_srt(cues))
    print(f"[subtitles] {len(cues)} cues -> {path}")
    return 0


def cmd_captions(args) -> int:
    """Carry the take's word timings into the manifest for the burned-in layer."""
    from acs import captions as captions_mod

    project = load_project(args.manifest)
    plan_path = os.path.join(args.project, "generation", "voice", "voice_plan.json")
    if not os.path.exists(plan_path):
        print("[captions] no voice_plan.json: run `studio.py voice --provider kokoro` first", file=sys.stderr)
        return 1
    with open(plan_path, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    result = captions_mod.attach(project, plan, max_words=args.max_words)
    for problem in result["problems"]:
        print(f"[captions] ! {problem}", file=sys.stderr)
    for warning in result["warnings"]:
        print(f"[captions]   {warning}")
    if not result["ok"]:
        return 1
    out = os.path.abspath(args.out or args.manifest)
    if args.dry_run:
        print(f"[captions] dry run: {result['shots']} shot(s), {result['cues']} cue(s); nothing written")
        return 0
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result["project"], fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    worst = captions_mod.max_reveal_error(result["project"], plan)
    print(
        f"[captions] {result['shots']} shot(s), {result['cues']} cue(s) -> {out}; "
        f"max reveal error {worst * 1000:.0f} ms (gate 120 ms)"
    )
    return 0


def cmd_storyboard(args) -> int:
    project = load_project(args.manifest)
    with use_manifest(args.manifest):
        result = storyboard_mod.build(args.project, project, studio=os.path.join(ROOT, "studio"), scale=args.scale)
    print(f"[storyboard] {result['shots']} stills -> {result['sheet']} {result['size']}")
    for frame in result["frames"]:
        print(f"[storyboard] {frame['id']} frame {frame['frame']} ({frame['scene']})")
    return 0


def cmd_cast(args) -> int:
    import subprocess

    studio = os.path.join(ROOT, "studio")
    out = os.path.abspath(os.path.join(args.project, "preproduction", "cast.png"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    npx = "npx.cmd" if os.name == "nt" else "npx"
    result = subprocess.run([npx, "remotion", "still", "src/index.ts", "CastSheet", out, "--scale", str(args.scale)], cwd=studio)
    if result.returncode != 0:
        return result.returncode
    print(f"[cast] {out}")
    return 0


def cmd_identity(args) -> int:
    from acs import identity as identity_mod
    from acs import overlays as overlays_mod

    project = load_project(args.manifest)
    report = identity_mod.audit(project, overlays_mod.load_cast(ROOT))
    out_dir = os.path.join(args.project, "quality")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "identity_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(out_dir, "identity_audit.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(identity_mod.render_markdown(report))
    print(f"[identity] {'OK' if report['ok'] else 'FAIL'} — {len(report['characters'])} canonical character(s)")
    for problem in report["problems"]:
        print(f"[identity] ! {problem}")
    for warning in report["warnings"]:
        print(f"[identity]   {warning}")
    print(f"[identity] {out_dir}/identity_audit.md")
    if not args.no_sheet:
        import subprocess

        studio = os.path.join(ROOT, "studio")
        out = os.path.abspath(os.path.join(args.project, "preproduction", "identity_sheet.png"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        npx = "npx.cmd" if os.name == "nt" else "npx"
        result = subprocess.run(
            [npx, "remotion", "still", "src/index.ts", "IdentitySheet", out, "--scale", str(args.scale)], cwd=studio
        )
        if result.returncode != 0:
            print("[identity] identity sheet failed", file=sys.stderr)
            return result.returncode
        print(f"[identity] sheet -> {out}")
        shots = identity_mod.shot_sheet(
            args.project, project, overlays_mod.load_cast(ROOT), os.path.join(out_dir, "identity_shots.png")
        )
        if shots:
            print(f"[identity] shot comparison -> {shots}")
    return 0 if report["ok"] else 1


def cmd_voicecheck(args) -> int:
    from acs import narration

    path = os.path.join(args.project, "generation", "voice", "voice_plan.json")
    if not os.path.exists(path):
        print("[voicecheck] no voice_plan.json: run `studio.py voice --provider kokoro` first", file=sys.stderr)
        return 1
    with open(path, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    report = narration.validate(args.project, plan)
    out_dir = os.path.join(args.project, "quality")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "narration_validation.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(out_dir, "narration_validation.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(narration.render_markdown(report))
    print(
        f"[voicecheck] {'OK' if report['ok'] else 'FAIL'} — {report['lines']} lines, "
        f"{report['words']} words, {report['speech_seconds']}s of speech"
    )
    for problem in report["problems"]:
        print(f"[voicecheck] ! {problem}")
    for warning in report["warnings"]:
        print(f"[voicecheck]   {warning}")
    print(f"[voicecheck] {out_dir}/narration_validation.md")
    return 0 if report["ok"] else 1


def cmd_mixdown(args) -> int:
    from acs import mixdown
    from acs.ffmpeg import Tools

    score = os.path.join(args.project, "generation", "audio", "score.wav")
    voice = os.path.join(args.project, "generation", "voice", "voice.wav")
    out = os.path.join(args.project, "generation", "audio", "mix.wav")
    info = mixdown.duck(Tools.detect(), score=score, voice=voice, out=out, music_gain=args.music_gain, voice_gain=args.voice_gain)
    print(f"[mixdown] {info['output']} ({info['duration']:.2f}s, {info['size_bytes'] / 1e6:.1f} MB)")
    print(f"[mixdown] {info['ducking']}")
    return 0


def cmd_mix(args) -> int:
    result = mixcheck.check(args.project, margin=args.margin)
    out = os.path.join(args.project, "preproduction", "mix_check.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(mixcheck.to_markdown(result))
    if not result["applicable"]:
        print(f"[mix] not applicable: {result['reason']}")
        return 0
    print(f"[mix] {len(result['flags'])} window(s) within {result['margin_db']:g} dB of the voice -> {out}")
    return 0


def cmd_plan(args) -> int:
    config = load_config(CONFIG_PATH)
    project = load_project(args.manifest)
    decisions, counts = plan_project(
        project,
        mode=config["mode"],
        assets_dir=os.path.join(args.project, "assets"),
        allow_external=bool(config.get("generation", {}).get("authorize_spend")),
    )
    out = os.path.join(args.project, "preproduction", "production_plan.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"mode": config["mode"], "counts": counts, "decisions": decisions}, fh, indent=2)
    print(f"[plan] {counts} -> {out}")
    return 0


def cmd_ui(args) -> int:
    """Decide which lines deserve UI, which mode, where and for how long."""
    project = load_project(args.manifest)
    cast = load_cast().get("characters", {})
    styles = json.load(open(os.path.join(ROOT, "studio", "src", "data", "styles.json"), encoding="utf-8"))
    result = ui_director_mod.plan_project(project, cast=cast, styles=styles)
    record = result["record"]
    paths = ui_director_mod.write_plan(args.project, record)
    for shot in record["shots"]:
        ui = ", ".join(f"{o['type']}@{o['anchor']}" for o in shot["overlays"]) or "sin UI"
        print(f"[ui] {shot['shot']}  modo {shot['mode']}  {shot['intent']:11s}  {ui}")
    for dropped in [d for s in record["shots"] for d in s["dropped"]]:
        print(f"[ui] descartado {dropped.get('id')}: {dropped.get('reason')}")
    for warning in record["warnings"]:
        print(f"[ui] ! {warning}")
    if args.apply:
        target = args.manifest or os.path.join(args.project, "manifest.json")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(result["project"], fh, indent=2, ensure_ascii=False)
        print(f"[ui] manifiesto planificado -> {target}")
        if args.write_active:
            with open(PROJECT_MANIFEST, "w", encoding="utf-8") as fh:
                json.dump(result["project"], fh, indent=2, ensure_ascii=False)
            print(f"[ui] active manifest -> {PROJECT_MANIFEST}")
    print(f"[ui] {record['totals']['overlays']} elemento(s), modos {record['modes']} -> {paths['markdown']}")
    return 0


def cmd_styles(args) -> int:
    styles = json.load(open(os.path.join(ROOT, "studio", "src", "data", "styles.json"), encoding="utf-8"))
    for key, style in styles["styles"].items():
        mark = " (default)" if key == styles["default"] else ""
        print(f"{key:12s}{mark:11s} {style['name']} — {style['use_when']}")
        print(f"{'':23s} density={style['ui']['density']} labels={style['ui']['labelStyle']} camera={style['camera']['energy']}")
    print(f"[styles] {len(styles['styles'])} styles, all rendering through the same engine")
    return 0


def cmd_direct(args) -> int:
    if not args.title:
        print("[direct] --title is required (a título, a guion or an idea)", file=sys.stderr)
        return 2
    cast = load_cast().get("characters", {})
    facts = []
    if args.facts:
        data = json.load(open(args.facts, encoding="utf-8"))
        facts = data.get("facts", data) if isinstance(data, dict) else data
    plan = director_mod.build_plan(
        title=args.title,
        idea=args.idea or "",
        script=args.script_text or "",
        seconds=args.seconds,
        style=args.style,
        audience=args.audience,
        language=args.language,
        facts=facts,
        cast=cast,
    )
    paths = director_mod.write_plan(args.project, plan)
    catalog = library.build(ROOT)
    composed = library.compose(plan["spec"], catalog)
    if not composed["ok"]:
        for problem in composed["problems"]:
            print(f"[direct] ! {problem}", file=sys.stderr)
        return 1
    manifest = os.path.join(args.project, "manifest.json")
    with open(manifest, "w", encoding="utf-8") as fh:
        json.dump(composed["project"], fh, indent=2, ensure_ascii=False)
    print(f"[direct] {len(plan['spec']['shots'])} shots · {plan['structure']['seconds']}s · style {plan['style']['id']} ({plan['style']['reason']})")
    print(f"[direct] narration={plan['narration']['source']} approval_required={plan['narration']['requires_author_approval']}")
    print(f"[direct] overlays={plan['overlays']['planned']} numeric={plan['overlays']['numeric']} sources={len(plan['overlays']['sources'])}")
    for warning in plan["warnings"]:
        print(f"[direct] ! {warning}")
    for key, path in paths.items():
        print(f"[direct] {key}: {path}")
    print(f"[direct] manifest: {manifest}")
    return 0


def cmd_inspect(args) -> int:
    project = load_project(args.manifest)
    delivery = os.path.join(args.project, "output", "final_video.mp4")
    report = inspect_mod.inspect_stills(args.project, project, root=ROOT, board_dir=args.board, video=args.video or delivery)
    paths = inspect_mod.write_report(args.project, report)
    flagged = [s for s in report["shots"] if s.get("flags")]
    for shot in report["shots"]:
        if shot.get("flags"):
            print(f"[inspect] ! {shot['shot']}: " + "; ".join(shot["flags"]))
    print(f"[inspect] {len(flagged)}/{len(report['shots'])} shot(s) flagged · overlays {'OK' if report['overlays']['ok'] else 'FAIL'}")
    ui = report.get("ui", {})
    print(f"[inspect] UI: {ui.get('modes')} · {ui.get('totals', {}).get('problems', 0)} problema(s) · {ui.get('totals', {}).get('warnings', 0)} aviso(s)")
    print(f"[inspect] aesthetics: {report['aesthetic_review']['status']} (no se puntúa sin revisión humana)")
    print(f"[inspect] {paths['markdown']}")
    return 0 if report["overlays"]["ok"] and ui.get("ok", False) and not report["problems"] else 1


def cmd_evaluate(args) -> int:
    project = load_project(args.manifest)
    quality = None
    if os.path.exists(os.path.join(args.project, "quality", "final_quality_report.json")):
        quality = json.load(open(os.path.join(args.project, "quality", "final_quality_report.json"), encoding="utf-8"))
    inspection = None
    if os.path.exists(os.path.join(args.project, "quality", "visual_inspection.json")):
        inspection = json.load(open(os.path.join(args.project, "quality", "visual_inspection.json"), encoding="utf-8"))
    review = None
    review_path = args.review or os.path.join(args.project, "preproduction", "visual_review.json")
    if os.path.exists(review_path):
        review = json.load(open(review_path, encoding="utf-8"))
    av = None
    av_path = os.path.join(args.project, "quality", "av_audit.json")
    if os.path.exists(av_path):
        av = json.load(open(av_path, encoding="utf-8"))
    card = evaluate_mod.scorecard(project_dir=args.project, project=project, quality=quality, inspection=inspection, review=review, av=av)
    paths = evaluate_mod.write_card(args.project, card)
    for dim, entry in card["dimensions"].items():
        mark = "PASS" if entry.get("pass") else ("FAIL" if entry.get("pass") is False else "--  ")
        print(f"[evaluate] {mark} {dim:15s} {entry['status']:9s} {entry['kind']}")
    print(f"[evaluate] {card['summary']['headline']} · {card['summary']['pending']} pendiente(s) sin puntuar")
    print(f"[evaluate] {paths['markdown']}")
    return 0 if not card["summary"]["failed"] else 1


def cmd_feedback(args) -> int:
    if args.action == "add":
        record = feedback_mod.add(
            ROOT,
            problem=args.problem,
            requested=args.requested or "",
            project=args.feedback_project or "",
            scene=args.scene or "",
            component=args.component or "",
            category=args.category,
            severity=args.severity,
            scope=args.scope,
            evidence=args.evidence or "",
        )
        print(f"[feedback] {record['id']} · {record['category']} · {record['severity']} · {record['scope']}")
        print(f"[feedback] {record['problem']}")
        return 0
    if args.action == "list":
        for record in feedback_mod.load(ROOT):
            if args.status and record["status"] != args.status:
                continue
            print(f"{record['id']}  {record['date']}  {record['category']:20s} {record['severity']:7s} {record['scope']:9s} {record['status']:10s} {record['problem'][:70]}")
        return 0
    if args.action == "apply":
        record = feedback_mod.apply_fix(ROOT, args.id, solution=args.solution, component=args.component or "")
        print(f"[feedback] {record['id']} applied: {record['solution']}")
        return 0
    if args.action == "validate":
        record = feedback_mod.validate(ROOT, args.id, evidence=args.evidence, passed=not args.failed)
        print(f"[feedback] {record['id']} -> {record['status']}: {record['validation']}")
        return 0
    if args.action == "case":
        case = feedback_mod.add_regression_case(
            ROOT, case_id=args.id, description=args.problem, check=args.check or "qa.ok", threshold=args.threshold or "true", evidence=args.evidence or ""
        )
        print(f"[feedback] regression case {case['id']}: {case['description']}")
        return 0
    paths = feedback_mod.write_documents(ROOT)
    for key, path in paths.items():
        print(f"[feedback] {key}: {path}")
    print(f"[feedback] {len(feedback_mod.load(ROOT))} record(s), {len(feedback_mod.recurring(ROOT))} recurring categor(y/ies)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Cinematic Studio pipeline")
    # Shared options are accepted both before and after the subcommand, because
    # `studio.py produce --project X` is the form people actually type.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=os.path.join(ROOT, "projects", "demo_001"))
    common.add_argument("--manifest", default=None, help="project.json to render (defaults to studio/src/data/project.json)")
    common.add_argument("--title", default=None)
    parser.add_argument("--project", default=os.path.join(ROOT, "projects", "demo_001"))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--title", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", parents=[common])
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("analysis", parents=[common])
    p.add_argument("--reference", nargs="+", required=True)
    p.add_argument("--quick", action="store_true")
    p.set_defaults(func=cmd_analysis)

    p = sub.add_parser("preproduction", parents=[common])
    p.set_defaults(func=cmd_preproduction)

    p = sub.add_parser("plan", parents=[common])
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("audio", parents=[common])
    p.set_defaults(func=cmd_audio)

    p = sub.add_parser("render", parents=[common])
    p.add_argument("--out", default=None, help="output path (defaults to output/picture_silent.mp4)")
    p.add_argument("--frames", default=None, help="Remotion frame range, e.g. 0-59 (short deterministic check)")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("assemble", parents=[common])
    p.add_argument("--silent", action="store_true", help="assemble without a soundtrack (debug only)")
    p.add_argument("--audio", default=None, help="track to mux (defaults to the procedural score; pass the voice mix)")
    p.add_argument("--allow-short-audio", action="store_true", help="deliberately allow a soundtrack shorter than the picture")
    p.set_defaults(func=cmd_assemble)

    p = sub.add_parser("qa", parents=[common])
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("assets", parents=[common])
    p.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "search", "validate", "rebuild", "show", "reuse", "generate", "versions", "preview", "similar", "references", "reference"],
    )
    p.add_argument("--query", default=None)
    p.add_argument("--type", default=None)
    p.add_argument("--tag", default=None)
    p.add_argument("--id", default=None)
    p.add_argument("--version", type=int, default=None)
    p.add_argument("--prompt", default=None, help="natural-language asset request (Spanish or English)")
    p.add_argument("--style", default=None)
    p.add_argument("--resolution", default=None, help="WIDTHxHEIGHT, default 1080x1920")
    p.add_argument("--aspect", default=None)
    p.add_argument("--license", default=None)
    p.add_argument("--source", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--purpose", default=None)
    p.add_argument("--path", default=None)
    p.add_argument("--tags", default=None, help="comma-separated reference tags")
    p.add_argument("--applies-to", dest="applies_to", default=None, help="comma-separated asset types")
    p.add_argument("--reference-license", dest="reference_license", default=None)
    p.add_argument("--notes", default=None)
    p.add_argument("--reference", action="append", default=None, help="reference id to attach to a generated asset")
    p.add_argument("--force", action="store_true", help="create a new version even when the spec is unchanged")
    p.add_argument("--scene", default=None)
    p.add_argument("--character", default=None)
    p.add_argument("--usage", default=None)
    p.add_argument("--compatible", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.set_defaults(func=cmd_assets)

    p = sub.add_parser("compose", parents=[common])
    p.add_argument("--spec", required=True, help="spec JSON naming scenes/cameras/characters by asset id")
    p.add_argument("--out", default=None)
    p.add_argument("--write-active", action="store_true", help="also write studio/src/data/project.json")
    p.set_defaults(func=cmd_compose)

    p = sub.add_parser("av", parents=[common])
    p.add_argument("--spec", required=True, help="beat sheet JSON (beats, scales, camera motives, sounds)")
    p.add_argument("--write-active", action="store_true", help="also write studio/src/data/project.json")
    p.set_defaults(func=cmd_av)

    p = sub.add_parser("avqa", parents=[common])
    p.add_argument("--baseline", default=None, help="previous manifest to compare against")
    p.set_defaults(func=cmd_avqa)

    p = sub.add_parser("edit", parents=[common])
    p.add_argument("--tolerance", type=float, default=0.45)
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("voice", parents=[common])
    p.add_argument("--provider", default="local", choices=["local", "kokoro", "elevenlabs"])
    p.add_argument("--authorize-spend", action="store_true", help="allow an ElevenLabs take (credits)")
    p.add_argument("--allow-model-download", action="store_true", help="allow Kokoro to download weights/voices")
    p.add_argument("--fit-shots", action="store_true", help="let an overflowing line stretch its shot (writes manifest_fitted.json)")
    p.set_defaults(func=cmd_voice)

    p = sub.add_parser("kokoro", parents=[common])
    p.set_defaults(func=cmd_kokoro)

    p = sub.add_parser("subtitles", parents=[common])
    p.add_argument("--max-words", type=int, default=3)
    p.set_defaults(func=cmd_subtitles)

    p = sub.add_parser("captions", parents=[common])
    p.add_argument("--out", default=None, help="manifest to write (defaults to --manifest)")
    p.add_argument("--max-words", type=int, default=3)
    p.add_argument("--dry-run", action="store_true", help="validate and report without writing")
    p.set_defaults(func=cmd_captions)

    p = sub.add_parser("storyboard", parents=[common])
    p.add_argument("--scale", type=float, default=0.45)
    p.set_defaults(func=cmd_storyboard)

    p = sub.add_parser("cast", parents=[common])
    p.add_argument("--scale", type=float, default=0.6)
    p.set_defaults(func=cmd_cast)

    p = sub.add_parser("identity", parents=[common])
    p.add_argument("--scale", type=float, default=0.6)
    p.add_argument("--no-sheet", action="store_true", help="audit only; skip the seven-pose contact sheet")
    p.set_defaults(func=cmd_identity)

    p = sub.add_parser("voicecheck", parents=[common])
    p.set_defaults(func=cmd_voicecheck)

    p = sub.add_parser("mixdown", parents=[common])
    p.add_argument("--music-gain", type=float, default=0.45)
    p.add_argument("--voice-gain", type=float, default=1.0)
    p.set_defaults(func=cmd_mixdown)

    p = sub.add_parser("mix", parents=[common])
    p.add_argument("--margin", type=float, default=3.0)
    p.set_defaults(func=cmd_mix)

    p = sub.add_parser("ui", parents=[common])
    p.add_argument("--apply", action="store_true", help="write the planned overlays into the manifest")
    p.add_argument("--write-active", action="store_true", help="also copy the planned manifest to studio/src/data/project.json")
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("styles", parents=[common])
    p.set_defaults(func=cmd_styles)

    p = sub.add_parser("direct", parents=[common])
    p.add_argument("--idea", default="")
    p.add_argument("--script", dest="script_text", default="")
    p.add_argument("--seconds", type=float, default=24.0)
    p.add_argument("--style", default=None, choices=["cinematic", "editorial", "infographic", "minimal", "cartoon"])
    p.add_argument("--audience", default="público general")
    p.add_argument("--language", default="es")
    p.add_argument("--facts", default=None, help="JSON with {facts:[{label,value,unit,source,numeric,series}]}")
    p.set_defaults(func=cmd_direct)

    p = sub.add_parser("inspect", parents=[common])
    p.add_argument("--board", default=None, help="stills directory (defaults to preproduction/board)")
    p.add_argument("--video", default=None, help="rendered file to sample (defaults to output/final_video.mp4)")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("evaluate", parents=[common])
    p.add_argument("--review", default=None)
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("feedback", parents=[common])
    p.add_argument("action", choices=["add", "list", "apply", "validate", "report", "case"])
    p.add_argument("--id", default="")
    p.add_argument("--problem", default="")
    p.add_argument("--requested", default="")
    p.add_argument("--feedback-project", dest="feedback_project", default="")
    p.add_argument("--scene", default="")
    p.add_argument("--component", default="")
    p.add_argument("--category", default=None, choices=sorted(feedback_mod.CATEGORIES))
    p.add_argument("--severity", default=None, choices=list(feedback_mod.SEVERITIES))
    p.add_argument("--scope", default=None, choices=list(feedback_mod.SCOPES))
    p.add_argument("--evidence", default="")
    p.add_argument("--solution", default="")
    p.add_argument("--status", default=None)
    p.add_argument("--check", default=None)
    p.add_argument("--threshold", default=None)
    p.add_argument("--failed", action="store_true")
    p.set_defaults(func=cmd_feedback)

    p = sub.add_parser("produce", parents=[common])
    p.add_argument("--reference", nargs="*", default=None)
    p.add_argument("--quick", action="store_true")
    p.set_defaults(func=cmd_produce)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FFmpegError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
