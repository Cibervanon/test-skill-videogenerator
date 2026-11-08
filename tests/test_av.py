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
DEMO_SPEC = os.path.join(ROOT, "projects", "av_direccion_demo", "spec.json")
NEW_STORY_SPEC = os.path.join(ROOT, "projects", "av_ultima_medida", "spec.json")
SECOND_STORY_SPEC = os.path.join(ROOT, "projects", "av_ultima_gota", "spec.json")
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

    def test_beat_order_is_audited(self):
        manifest = copy.deepcopy(av_director.plan(load(SPEC))["manifest"])
        manifest["shots"][0], manifest["shots"][1] = manifest["shots"][1], manifest["shots"][0]
        report = avqa.audit(manifest)
        self.assertIn("beat_order", report["summary"]["failed"])

    def test_axis_flip_between_the_same_two_actors_is_flagged(self):
        manifest = copy.deepcopy(av_director.plan(load(SPEC))["manifest"])
        first = next(s for s in manifest["shots"] if s["id"] == "S05")
        second = next(s for s in manifest["shots"] if s["id"] == "S07")
        for actor in second["actors"]:
            actor["x"] = 1080 - float(actor["x"])
        # Keep the scene and cast identical; only screen direction changed.
        report = avqa.audit({"format": {"fps": 30}, "shots": [first, second]})
        self.assertTrue(report["metrics"]["axis_violations"])

    def test_static_shot_without_a_motive_fails(self):
        manifest = copy.deepcopy(av_director.plan(load(SPEC))["manifest"])
        shot = next(s for s in manifest["shots"] if s["id"] == "S05")
        shot["camera"] = "static"
        shot["cameraIntensity"] = 0.0
        shot["cameraMotive"] = ""
        report = avqa.audit(manifest)
        self.assertIn("static_intent", report["summary"]["failed"])

    def test_director_records_camera_intensity(self):
        manifest = av_director.plan(load(SPEC))["manifest"]
        self.assertTrue(all("cameraIntensity" in shot for shot in manifest["shots"]))
        self.assertTrue(all(0.0 <= shot["cameraIntensity"] <= 1.35 for shot in manifest["shots"]))

    def test_compound_sequence_is_normalized_and_audited(self):
        planned = av_director.plan(load(DEMO_SPEC))
        self.assertTrue(planned["ok"], planned["problems"])
        manifest = planned["manifest"]
        young = next(
            a for s in manifest["shots"] if s["id"] == "S03" for a in s["actors"] if a["id"] == "young"
        )
        self.assertEqual([p["preset"] for p in young["sequence"]], ["turn", "reach"])
        self.assertEqual([(p["start"], p["end"]) for p in young["sequence"]], [(0.0, 0.34), (0.38, 1.0)])
        report = avqa.audit(manifest)
        self.assertGreaterEqual(report["metrics"]["phased_shots"], 2)
        self.assertGreaterEqual(report["metrics"]["action_phases"], 4)
        self.assertNotIn("action_completion", report["summary"]["failed"])

    def test_overlapping_compound_phases_are_rejected(self):
        spec = copy.deepcopy(load(DEMO_SPEC))
        young = next(
            a for b in spec["beats"] if b["id"] == "S03" for a in b["actors"] if a["id"] == "young"
        )
        young["sequence"][1]["start"] = 0.2
        planned = av_director.plan(spec)
        self.assertFalse(planned["ok"])
        self.assertTrue(any("overlaps the previous phase" in p for p in planned["problems"]))

    def test_sequence_ending_mid_walk_fails_creative_audit(self):
        manifest = copy.deepcopy(av_director.plan(load(DEMO_SPEC))["manifest"])
        young = next(
            a for s in manifest["shots"] if s["id"] == "S03" for a in s["actors"] if a["id"] == "young"
        )
        young["sequence"][-1]["preset"] = "walkIn"
        report = avqa.audit(manifest)
        self.assertIn("action_completion", report["summary"]["failed"])
        self.assertTrue(report["metrics"]["unfinished_sequences"])

    def test_carry_inherits_actor_state_without_resetting(self):
        planned = av_director.plan(load(NEW_STORY_SPEC))
        self.assertTrue(planned["ok"], planned["problems"])
        manifest = planned["manifest"]
        s02 = next(a for s in manifest["shots"] if s["id"] == "S02" for a in s["actors"] if a["id"] == "young")
        s03 = next(a for s in manifest["shots"] if s["id"] == "S03" for a in s["actors"] if a["id"] == "young")
        self.assertEqual(s03["x"], s02["continuity"]["exit"]["x"])
        self.assertTrue(s03["continuity"]["carried"])
        self.assertEqual(s03["continuity"]["shift"], 0.0)
        self.assertEqual(manifest["continuity"]["carried"], 5)
        report = avqa.audit(manifest)
        self.assertNotIn("character_continuity", report["summary"]["failed"])
        self.assertEqual(report["metrics"]["continuity_issues"], [])

    def test_carry_across_a_scene_change_is_rejected(self):
        spec = copy.deepcopy(load(NEW_STORY_SPEC))
        s04 = next(b for b in spec["beats"] if b["id"] == "S04")
        # Force a real location change; the story itself keeps every shot in the
        # workshop, so the old fixture no longer exercised this guard.
        s04["scene"] = "faceCloseup"
        s04["actors"].append({"id": "young", "preset": "idle", "carry": True, "y": 1900, "scale": 3.0})
        planned = av_director.plan(spec)
        self.assertFalse(planned["ok"])
        self.assertTrue(any("cannot carry across scene change" in p for p in planned["problems"]))

    def test_unmotivated_same_scene_teleport_is_rejected(self):
        spec = copy.deepcopy(load(NEW_STORY_SPEC))
        s03 = next(b for b in spec["beats"] if b["id"] == "S03")
        elder = next(a for a in s03["actors"] if a["id"] == "elder")
        elder.pop("carry")
        elder["x"] = 700
        planned = av_director.plan(spec)
        self.assertFalse(planned["ok"])
        self.assertTrue(any("same-scene shift without continuityMotive" in p for p in planned["problems"]))

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


class SecondStoryTests(unittest.TestCase):
    """The second authored story must be different, stateful and renderable."""

    def test_second_story_is_structurally_valid_and_distinct(self):
        planned = av_director.plan(load(SECOND_STORY_SPEC))
        self.assertTrue(planned["ok"], planned["problems"])
        manifest = planned["manifest"]
        self.assertEqual(len(manifest["shots"]), 7)
        self.assertTrue(all(s["scene"] == "greenhouse" for s in manifest["shots"]))
        self.assertNotIn("workshop", {s["scene"] for s in manifest["shots"]})
        self.assertEqual(
            [s["state"] for s in manifest["shots"]],
            ["table", "table", "held", "held", "held", "pour", "bloom"],
        )
        self.assertEqual(manifest["continuity"]["carried"], 1)
        report = avqa.audit(manifest)
        self.assertTrue(report["summary"]["ok"], report["summary"])
        self.assertEqual(report["metrics"]["continuity_issues"], [])

    def test_second_story_keeps_the_water_can_across_the_action(self):
        manifest = av_director.plan(load(SECOND_STORY_SPEC))["manifest"]
        young = [
            (s["id"], a)
            for s in manifest["shots"]
            for a in s["actors"]
            if a["id"] == "young"
        ]
        self.assertEqual([shot_id for shot_id, _ in young], ["S03", "S04", "S05"])
        self.assertTrue(all(a["hold"] == "can" for _, a in young))
        self.assertTrue(young[1][1]["continuity"]["carried"])

    def test_second_story_opens_and_closes_on_the_changed_object(self):
        manifest = av_director.plan(load(SECOND_STORY_SPEC))["manifest"]
        opening = manifest["shots"][0]
        closing = manifest["shots"][-1]
        self.assertEqual(opening["actors"], [])
        self.assertGreater(opening["zoom"], 1.0)
        self.assertLess(opening["offsetX"], 0.0)
        self.assertEqual(closing["state"], "bloom")
        self.assertGreater(closing["zoom"], 1.0)
        self.assertNotEqual(opening["line"], closing["line"])


if __name__ == "__main__":
    unittest.main()
