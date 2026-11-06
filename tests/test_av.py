"""AV direction: beat planning, structural creative QA and explicit sound cues."""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import audio_gen, av_director, avqa, evaluate  # noqa: E402

SPEC = os.path.join(ROOT, "projects", "av_direccion", "spec.json")
BASELINE = os.path.join(ROOT, "projects", "ui_direccion", "manifest.json")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class DirectorTests(unittest.TestCase):
    def test_beat_sheet_becomes_a_manifest_with_motives(self):
        planned = av_director.plan(load(SPEC))
        self.assertTrue(planned["ok"], planned["problems"])
        manifest = planned["manifest"]
        self.assertEqual(len(manifest["shots"]), 10)
        self.assertTrue(all(s["cameraMotive"] for s in manifest["shots"]))
        self.assertTrue(all(s["beat"] for s in manifest["shots"]))
        self.assertEqual({s["scale"] for s in manifest["shots"]}, {"wide", "medium", "close", "detail"})
        self.assertEqual(manifest["shots"][-1]["beat"], "close")

    def test_narration_mode_overrides_character_speakers(self):
        spec = copy.deepcopy(load(SPEC))
        spec["narration"] = True
        planned = av_director.plan(spec)
        self.assertTrue(planned["ok"], planned["problems"])
        self.assertTrue(planned["manifest"]["narration"])
        spoken = [s for s in planned["manifest"]["shots"] if s["line"]]
        self.assertTrue(spoken)
        self.assertEqual({s["speaker"] for s in spoken}, {"narrator"})

    def test_dialogue_flag_keeps_a_character_voice_in_narration_mode(self):
        spec = copy.deepcopy(load(SPEC))
        spec["narration"] = True
        spec["beats"][0]["dialogue"] = True
        planned = av_director.plan(spec)
        self.assertTrue(planned["ok"], planned["problems"])
        self.assertEqual(planned["manifest"]["shots"][0]["speaker"], "elder")

    def test_unmotivated_dissolve_is_rejected(self):
        spec = copy.deepcopy(load(SPEC))
        spec["beats"][1]["transition"] = {"type": "dissolve", "motive": ""}
        planned = av_director.plan(spec)
        self.assertFalse(planned["ok"])
        self.assertTrue(any("dissolve without a motive" in p for p in planned["problems"]))

    def test_explicit_sound_replaces_scene_defaults(self):
        project = {
            "format": {"fps": 30},
            "transitionFrames": 10,
            "shots": [
                {"id": "S01", "scene": "bellInsert", "seconds": 2.0, "sound": [], "transitionIn": 0},
                {"id": "S02", "scene": "townNight", "seconds": 2.0, "sound": [{"type": "footstep", "at": 0.5}], "transitionIn": 0},
            ],
        }
        spec = audio_gen.spec_from_project(project)
        self.assertEqual(len(spec["events"]), 1)
        self.assertEqual(spec["events"][0]["type"], "footstep")
        self.assertAlmostEqual(spec["events"][0]["at"], 2.5, places=3)


class CreativeQATests(unittest.TestCase):
    def test_demo_has_no_structural_failures(self):
        planned = av_director.plan(load(SPEC))
        report = avqa.audit(planned["manifest"])
        self.assertTrue(report["summary"]["ok"], report["summary"])
        metrics = report["metrics"]
        self.assertGreaterEqual(metrics["scale_counts"].get("close", 0), 1)
        self.assertLessEqual(metrics["longest_scale_run"], 2)
        self.assertGreaterEqual(metrics["action_shots"], 3)
        self.assertEqual(metrics["reaction_shots"], 1)
        self.assertGreaterEqual(metrics["sound_shots"], 5)
        self.assertEqual(metrics["camera_motives"].split("/")[0], metrics["camera_motives"].split("/")[1])

    def test_legacy_manifest_is_audited_without_faking_beats(self):
        report = avqa.audit(load(BASELINE))
        self.assertIn("structure", report["summary"]["pending"])
        self.assertEqual(report["metrics"]["beat_counts"], {})
        self.assertIn("derived from actor scale", report["metrics"]["scale_source"])

    def test_before_after_reports_structural_deltas(self):
        before = avqa.audit(load(BASELINE))
        after = avqa.audit(av_director.plan(load(SPEC))["manifest"])
        comparison = avqa.compare(before, after)
        rows = {r["metric"]: r for r in comparison["rows"]}
        self.assertEqual(rows["planos"]["before"], 8)
        self.assertEqual(rows["planos"]["after"], 10)
        self.assertGreater(rows["planos con acción"]["after"], rows["planos con acción"]["before"])
        self.assertLess(rows["racha máxima de escala"]["after"], rows["racha máxima de escala"]["before"])
        self.assertIn("human review", comparison["note"])

    def test_montage_enters_evaluation_only_when_audited(self):
        quality = {"checks": []}
        project = {"id": "x", "shots": []}
        plain = evaluate.scorecard(project_dir=".", project=project, quality=quality, inspection={"shots": []})
        audited = evaluate.scorecard(
            project_dir=".",
            project=project,
            quality=quality,
            inspection={"shots": []},
            av={"summary": {"ok": True}, "metrics": {"shots": 10}},
        )
        self.assertEqual(plain["dimensions"]["montage"]["status"], "pending")
        self.assertEqual(audited["dimensions"]["montage"]["status"], "measured")
        self.assertEqual(audited["summary"]["measured"], plain["summary"]["measured"] + 1)


if __name__ == "__main__":
    unittest.main()
