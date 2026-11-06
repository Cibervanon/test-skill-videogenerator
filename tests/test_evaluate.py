"""Evaluation: measured vs pending, and regression against a reference."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import evaluate  # noqa: E402

QA_OK = {
    "ok": True,
    "checks": [
        {"id": "motion", "pass": True, "value": 3.2, "detail": "min 1.0"},
        {"id": "format", "pass": True, "value": "1080x1920", "detail": "to spec"},
        {"id": "loudness", "pass": True, "value": -15.0, "detail": "band"},
        {"id": "caption_plan", "pass": True, "value": 0.72, "detail": "plan"},
    ],
}


def inspection(empty=0.1, spread=120.0, shift=0.1, ok=True):
    return {
        "style": "cinematic",
        "shots": [
            {
                "shot": "S01",
                "status": "clean (pixels)",
                "empty_ratio": empty,
                "subject_score": 2.4,
                "caption_contrast": {"spread": spread, "edges": 9.0},
                "palette_shift": shift,
                "depth_bands": 3,
                "has_captions": True,
                "flags": [],
            }
        ],
        "overlays": {"ok": ok, "problems": [] if ok else ["S01: overlaps the caption band"], "warnings": [], "counts": {"label": 1}},
    }


class EvaluateTests(unittest.TestCase):
    def test_unmeasured_dimensions_are_pending_not_zero(self):
        card = evaluate.scorecard(project_dir=".", project={"id": "x", "style": "cinematic"}, quality=QA_OK, inspection=inspection())
        self.assertEqual(card["dimensions"]["narrative"]["status"], "pending")
        self.assertIsNone(card["dimensions"]["narrative"]["value"])
        self.assertEqual(card["summary"]["measured"], 8)
        self.assertFalse(card["summary"]["failed"])

    def test_defective_render_fails_measured_dimensions(self):
        card = evaluate.scorecard(project_dir=".", project={"id": "x"}, quality=QA_OK, inspection=inspection(empty=0.8, spread=40.0, shift=0.6, ok=False))
        self.assertIn("composition", card["summary"]["failed"])
        self.assertIn("legibility", card["summary"]["failed"])
        self.assertIn("consistency", card["summary"]["failed"])
        self.assertIn("overlays", card["summary"]["failed"])

    def test_graphic_plates_are_not_judged_as_empty_scenes(self):
        insp = inspection(empty=0.9)
        insp["shots"][0]["shot"] = "S02"
        project = {
            "id": "x",
            "style": "cinematic",
            "shots": [
                {"id": "S01", "presentation": {"mode": "A"}},
                {"id": "S02", "presentation": {"mode": "E"}},
            ],
        }
        card = evaluate.scorecard(project_dir=".", project=project, quality=QA_OK, inspection=insp)
        self.assertTrue(card["dimensions"]["composition"]["pass"])

        insp["shots"][0]["shot"] = "S01"
        card = evaluate.scorecard(project_dir=".", project=project, quality=QA_OK, inspection=insp)
        self.assertFalse(card["dimensions"]["composition"]["pass"])

    def test_declared_detail_insert_is_not_an_empty_scene(self):
        insp = inspection(empty=0.8)
        insp["shots"][0]["shot"] = "S01"
        project = {
            "id": "x",
            "style": "cinematic",
            "shots": [{"id": "S01", "beat": "insert", "scale": "detail", "presentation": {"mode": "A"}}],
        }
        card = evaluate.scorecard(project_dir=".", project=project, quality=QA_OK, inspection=insp)
        self.assertTrue(card["dimensions"]["composition"]["pass"])
        self.assertEqual(card["dimensions"]["composition"]["value"]["declared_insert_max"], 0.8)

    def test_human_review_fills_a_subjective_dimension(self):
        card = evaluate.scorecard(
            project_dir=".",
            project={"id": "x"},
            quality=QA_OK,
            inspection=inspection(),
            review={"narrative": {"score": 4, "note": "cierre claro", "reviewer": "autor"}},
        )
        self.assertEqual(card["dimensions"]["narrative"]["status"], "reviewed")

    def test_markdown_has_no_global_score(self):
        card = evaluate.scorecard(project_dir=".", project={"id": "x"}, quality=QA_OK, inspection=inspection())
        text = evaluate.render_markdown(card)
        self.assertIn("pending", text)
        self.assertIn("No hay una nota global", text)

    def test_regression_compare_flags_a_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = os.path.join(tmp, "v.mp4")
            with open(video, "wb") as fh:
                fh.write(b"fake-video")
            evaluate.snapshot(tmp, render_id="ref1", video=video, metrics={"empty_ratio": 0.1, "palette_shift": 0.12})
            result = evaluate.compare(tmp, render_id="ref1", current={"empty_ratio": 0.5, "palette_shift": 0.12})
            self.assertFalse(result["ok"])
            self.assertEqual([d["metric"] for d in result["deltas"] if not d["ok"]], ["empty_ratio"])

    def test_missing_reference_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate.compare(tmp, render_id="nope", current={"empty_ratio": 0.1})
            self.assertFalse(result["ok"])
            self.assertIn("no reference", result["reason"])


if __name__ == "__main__":
    unittest.main()
