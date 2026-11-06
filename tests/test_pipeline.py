"""Tests for the deterministic parts of the pipeline.

Run: python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import audio_gen, project as project_mod, qa  # noqa: E402
from acs.providers.base import (  # noqa: E402
    CostGuard,
    CostModel,
    Provider,
    ProviderError,
    ProviderRequest,
    ProviderResult,
    SpendNotAuthorized,
)
from acs.providers.registry import MODE_RANK, Registry  # noqa: E402
from acs.providers.local import LocalRemotionRenderProvider  # noqa: E402
from acs.scenes import build_shots  # noqa: E402
from acs.selector import choose  # noqa: E402

PROJECT_JSON = os.path.join(ROOT, "studio", "src", "data", "project.json")
CAST_JSON = os.path.join(ROOT, "studio", "src", "data", "cast.json")


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class SceneTests(unittest.TestCase):
    def test_micro_shots_are_absorbed(self):
        # 1.0 is a legitimate 1s shot; 1.2 and 4.1 are flash frames after a cut
        shots = build_shots([1.0, 1.2, 4.0, 4.1], duration=10.0, min_shot=0.6)
        self.assertEqual([s.start for s in shots], [0.0, 1.0, 4.0])
        self.assertEqual(shots[-1].end, 10.0)
        for shot in shots:
            self.assertGreaterEqual(shot.duration, 0.6)

    def test_shots_are_contiguous(self):
        shots = build_shots([2.0, 5.5], duration=9.0, min_shot=0.6)
        for prev, nxt in zip(shots, shots[1:]):
            self.assertAlmostEqual(prev.end, nxt.start, places=3)

    def test_cut_outside_media_is_ignored(self):
        shots = build_shots([0.0, 12.0], duration=10.0)
        self.assertEqual(len(shots), 1)


class SelectorTests(unittest.TestCase):
    def test_local_mode_never_selects_external(self):
        d = choose(element="S01.face", kind="photoreal_face", mode="local", allow_external=True)
        self.assertEqual(d.strategy, "code")
        self.assertEqual(d.quality_risk, "high")  # limitation is surfaced, not hidden

    def test_hybrid_without_authorization_stays_local(self):
        d = choose(element="S01.face", kind="photoreal_face", mode="hybrid", allow_external=False)
        self.assertEqual(d.strategy, "code")
        self.assertIn("not authorised", d.reason)

    def test_hybrid_with_authorization_can_go_external(self):
        d = choose(
            element="S01.face",
            kind="photoreal_face",
            mode="hybrid",
            allow_external=True,
            provider="video.generic",
            provider_cost_usd=0.4,
        )
        self.assertEqual(d.strategy, "external")
        self.assertAlmostEqual(d.estimated_cost_usd, 0.4)

    def test_code_native_elements_never_escalate(self):
        for kind in ("character", "environment", "camera", "music", "caption"):
            d = choose(element="x", kind=kind, mode="premium", allow_external=True)
            self.assertEqual(d.strategy, "code", kind)

    def test_reuse_beats_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, "characters")
            os.makedirs(asset_dir)
            with open(os.path.join(asset_dir, "elder.json"), "w", encoding="utf-8") as fh:
                json.dump({"fingerprint": "elder-v1"}, fh)
            d = choose(element="S01.elder", kind="character", mode="local", spec={"fingerprint": "elder-v1"}, assets_dir=tmp)
            self.assertEqual(d.strategy, "reuse")


class _FakeProvider(Provider):
    name = "fake"
    capability = "video.clip"
    is_external = True
    min_mode = "hybrid"
    cost_model = CostModel("clip", 1.5)

    def __init__(self, available: bool = True):
        self._available = available

    def is_available(self):
        return self._available, "ok" if self._available else "not configured"

    def run(self, request, guard):
        guard.check(self.cost_model.usd_per_unit, is_external=True)
        return ProviderResult(provider=self.name, capability=self.capability, ok=True, cost_usd=self.cost_model.usd_per_unit)


class GuardTests(unittest.TestCase):
    def test_spend_blocked_without_authorization(self):
        guard = CostGuard(budget_usd=5.0, authorized=False)
        with self.assertRaises(SpendNotAuthorized):
            guard.check(0.5, is_external=True)

    def test_local_spend_is_always_allowed(self):
        guard = CostGuard(budget_usd=0.0, authorized=False)
        guard.check(0.0, is_external=False)  # must not raise

    def test_budget_ceiling(self):
        guard = CostGuard(budget_usd=1.0, authorized=True)
        guard.commit(0.9)
        with self.assertRaises(Exception):
            guard.check(0.5, is_external=True)


class RegistryTests(unittest.TestCase):
    def _registry(self, mode: str, authorized: bool = False, budget: float = 0.0):
        config = {"mode": mode, "generation": {"authorize_spend": authorized, "budget_usd": budget}}
        registry = Registry(config, project_dir=tempfile.mkdtemp())
        registry.add(_FakeProvider())
        return registry

    def test_local_mode_skips_external_provider(self):
        registry = self._registry("local")
        with self.assertRaises(Exception):
            registry.select("video.clip")

    def test_hybrid_requires_authorization(self):
        registry = self._registry("hybrid")
        with self.assertRaises(SpendNotAuthorized):
            registry.select("video.clip")

    def test_hybrid_with_authorization_selects(self):
        registry = self._registry("hybrid", authorized=True, budget=3.0)
        provider = registry.select("video.clip")
        self.assertEqual(provider.name, "fake")

    def test_mode_ranking_is_ordered(self):
        self.assertLess(MODE_RANK["local"], MODE_RANK["hybrid"])
        self.assertLess(MODE_RANK["hybrid"], MODE_RANK["premium"])


class AudioTests(unittest.TestCase):
    def test_spec_matches_project_timeline(self):
        project = load(PROJECT_JSON)
        spec = audio_gen.spec_from_project(project)
        # Each shot is overlapped by the NEXT shot's transitionIn, so the film is
        # sum(seconds) minus every transition except the first shot's (there is
        # nothing before it). The renderer, the score and QA share this rule.
        fps = project["format"]["fps"]
        default = project["transitionFrames"]
        shots = project["shots"]
        expected = 0.0
        for i, shot in enumerate(shots):
            overlap = shots[i + 1].get("transitionIn", default) / fps if i + 1 < len(shots) else 0.0
            expected += shot["seconds"] - overlap
        self.assertAlmostEqual(spec["duration"], expected, places=2)
        self.assertTrue(spec["events"], "sound design must contain at least one event")

    def test_synthesis_is_deterministic(self):
        spec = {"duration": 0.5, "events": [{"type": "footstep", "at": 0.1}], "music": False}
        a, _ = audio_gen.build(spec, seed=7)
        b, _ = audio_gen.build(spec, seed=7)
        self.assertEqual(a.left[:200], b.left[:200])
        self.assertNotEqual(a.left[:200], audio_gen.build(spec, seed=8)[0].left[:200])


class PreproductionTests(unittest.TestCase):
    def test_documents_are_written(self):
        project = load(PROJECT_JSON)
        cast = load(CAST_JSON)
        with tempfile.TemporaryDirectory() as tmp:
            root = project_mod.init_project(tmp, "demo_test")
            result = project_mod.write_preproduction(root, project, cast, source_project_path=PROJECT_JSON)
            for name in ("script.md", "storyboard.json", "shot_list.json", "character_bible.json", "environment_bible.json"):
                self.assertTrue(os.path.exists(os.path.join(root, "preproduction", name)), name)
            self.assertTrue(result["continuity"]["ok"], result["continuity"]["issues"])
            self.assertEqual(result["storyboard"]["total_shots"], len(project["shots"]))


class QATests(unittest.TestCase):
    def test_caption_coverage_is_high_for_a_written_script(self):
        project = load(PROJECT_JSON)
        cov = qa.caption_coverage(project, transition_frames=project["transitionFrames"], fps=project["format"]["fps"])
        self.assertGreaterEqual(cov["coverage"], 0.99)
        self.assertTrue(cov["method"].startswith("computed"))

    def test_missing_output_fails_loudly(self):
        project = load(PROJECT_JSON)
        report = qa.run_qa(None, output=os.path.join(ROOT, "does_not_exist.mp4"), project=project)  # type: ignore[arg-type]
        self.assertFalse(report["ok"])
        self.assertEqual(report["checks"][0]["id"], "exists")

    def test_delivery_passes_when_present(self):
        # Each delivery is checked against ITS OWN manifest: the live project.json
        # moves on with every film, and a stale pairing would either fail for the
        # wrong reason or pass by accident.
        delivery = os.path.join(ROOT, "projects", "demo_002", "output", "final_video.mp4")
        manifest = os.path.join(ROOT, "projects", "demo_002", "manifest.json")
        if not (os.path.exists(delivery) and os.path.exists(manifest)):
            self.skipTest("demo_002 delivery not rendered yet")
        from acs.ffmpeg import Tools

        report = qa.run_qa(Tools.detect(), output=delivery, project=load(manifest))
        self.assertTrue(report["ok"], [c for c in report["checks"] if not c["pass"]])


class ManifestActivationTests(unittest.TestCase):
    def test_use_manifest_restores_previous_bytes(self):
        import studio

        with tempfile.TemporaryDirectory() as tmp:
            active = os.path.join(tmp, "project.json")
            requested = os.path.join(tmp, "requested.json")
            previous = b'{"id": "previous"}\n'
            with open(active, "wb") as fh:
                fh.write(previous)
            with open(requested, "w", encoding="utf-8") as fh:
                json.dump({"id": "requested", "shots": []}, fh)

            original = studio.PROJECT_MANIFEST
            studio.PROJECT_MANIFEST = active
            try:
                with studio.use_manifest(requested) as project:
                    self.assertEqual(project["id"], "requested")
                    self.assertEqual(load(active)["id"], "requested")
                with open(active, "rb") as fh:
                    self.assertEqual(fh.read(), previous)
            finally:
                studio.PROJECT_MANIFEST = original

    def test_use_manifest_restores_after_an_exception(self):
        import studio

        with tempfile.TemporaryDirectory() as tmp:
            active = os.path.join(tmp, "project.json")
            requested = os.path.join(tmp, "requested.json")
            previous = b'{"id": "previous"}\n'
            with open(active, "wb") as fh:
                fh.write(previous)
            with open(requested, "w", encoding="utf-8") as fh:
                json.dump({"id": "requested", "shots": []}, fh)

            original = studio.PROJECT_MANIFEST
            studio.PROJECT_MANIFEST = active
            try:
                with self.assertRaises(RuntimeError):
                    with studio.use_manifest(requested):
                        raise RuntimeError("render failed")
                with open(active, "rb") as fh:
                    self.assertEqual(fh.read(), previous)
            finally:
                studio.PROJECT_MANIFEST = original


class RenderProviderTests(unittest.TestCase):
    def test_render_streams_progress_to_its_log_file(self):
        provider = LocalRemotionRenderProvider(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "logs", "render.log")
            seen = {}

            def fake_run(cmd, **kwargs):
                seen["cmd"] = cmd
                seen["stdout"] = kwargs.get("stdout")
                kwargs["stdout"].write("Rendered 1/10\nRendered 10/10\n")
                kwargs["stdout"].flush()
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            request = ProviderRequest(
                capability="video.render",
                destination=os.path.join(tmp, "out.mp4"),
                params={"composition": "CinematicDemo", "log": log},
            )
            with mock.patch("acs.providers.local.subprocess.run", side_effect=fake_run):
                result = provider.run(request, CostGuard(budget_usd=0.0, authorized=False))

            self.assertTrue(result.ok)
            self.assertEqual(result.meta["log"], log)
            self.assertIsNotNone(seen["stdout"])
            with open(log, "r", encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("$ npx remotion render", text)
            self.assertIn("Rendered 10/10", text)


if __name__ == "__main__":
    unittest.main()
