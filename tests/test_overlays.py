"""Overlay validation, layout and anti-drift against the TypeScript engine."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import overlays  # noqa: E402

CAST = overlays.load_cast(ROOT)
STYLES = overlays.load_styles(ROOT)
STYLE = STYLES["styles"]["cinematic"]
ACTORS = [
    {"id": "elder", "preset": "closeup", "x": 540, "y": 1150, "scale": 2.2, "facing": 1},
]


def spec(**overrides):
    base = {
        "id": "T1",
        "type": "callout",
        "placement": {"kind": "screen", "box": {"x": 0.5, "y": 0.6, "w": 0.38, "h": 0.12}},
        "data": {"title": "la idea", "caption": "algo importante"},
    }
    base.update(overrides)
    return base


class AntiDriftTests(unittest.TestCase):
    def test_constants_match_the_renderer(self):
        ts = overlays.ts_constants(
            os.path.join(ROOT, "studio", "src", "motion-graphics", "layout.ts"),
            os.path.join(ROOT, "studio", "src", "characters", "geometry.ts"),
        )
        self.assertAlmostEqual(ts["SAFE"], overlays.SAFE, places=6)
        for key, value in overlays.RIG.items():
            self.assertAlmostEqual(ts["RIG"][key], value, places=6, msg=f"RIG.{key} drifted")

    def test_every_renderer_type_is_validatable(self):
        registry = open(os.path.join(ROOT, "studio", "src", "motion-graphics", "OverlayLayer.tsx"), encoding="utf-8").read()
        for kind in overlays.TYPES:
            self.assertIn(f'{kind}:', registry, f"{kind} is validated but not rendered")


class OverlayValidationTests(unittest.TestCase):
    def test_valid_callout_passes(self):
        result = overlays.validate_overlay(spec(), actors=ACTORS, cast=CAST, style=STYLE)
        self.assertTrue(result["ok"], result["problems"])

    def test_numeric_without_source_fails(self):
        bad = spec(id="N1", type="counter", placement={"kind": "screen", "box": {"x": 0.1, "y": 0.6, "w": 0.5, "h": 0.15}}, data={"value": 42, "title": "x"})
        result = overlays.validate_overlay(bad, actors=ACTORS, cast=CAST, style=STYLE)
        self.assertFalse(result["ok"])
        self.assertTrue(any("source" in p for p in result["problems"]))

    def test_numeric_with_source_passes(self):
        good = spec(
            id="N2",
            type="bar",
            placement={"kind": "screen", "box": {"x": 0.08, "y": 0.58, "w": 0.84, "h": 0.24}},
            data={"series": [{"label": "a", "value": 1}]},
            source="informe interno, 2026",
        )
        result = overlays.validate_overlay(good, actors=ACTORS, cast=CAST, style=STYLE)
        self.assertTrue(result["ok"], result["problems"])

    def test_illustrative_marks_schematic_values(self):
        schematic = spec(id="N3", type="bar", placement={"kind": "screen", "box": {"x": 0.08, "y": 0.58, "w": 0.84, "h": 0.24}}, data={"series": [{"label": "a", "value": 1}]}, illustrative=True)
        result = overlays.validate_overlay(schematic, actors=ACTORS, cast=CAST, style=STYLE)
        self.assertTrue(result["ok"], result["problems"])

    def test_missing_payload_fails(self):
        result = overlays.validate_overlay(spec(type="bar", data={}), actors=ACTORS, cast=CAST, style=STYLE)
        self.assertFalse(result["ok"])

    def test_caption_band_is_never_covered(self):
        result = overlays.validate_overlay(spec(box={"x": 0.1, "y": 0.9, "w": 0.6, "h": 0.08}, placement={"kind": "screen", "box": {"x": 0.1, "y": 0.9, "w": 0.6, "h": 0.08}}), actors=ACTORS, cast=CAST, style=STYLE)
        self.assertFalse(result["ok"])
        self.assertTrue(any("caption" in p for p in result["problems"]))

    def test_label_never_covers_the_face(self):
        label = spec(
            id="L1",
            type="label",
            placement={"kind": "actor", "actor": "elder", "at": "head"},
            data={"name": "The Bell-Keeper"},
        )
        result = overlays.validate_overlay(label, actors=ACTORS, cast=CAST, style=STYLE)
        self.assertTrue(result["ok"], result["problems"])
        head = overlays.face_circle(ACTORS[0], CAST)
        self.assertFalse(overlays.circle_hits_box(*head, result["box"]))

    def test_unknown_actor_in_placement_fails(self):
        label = spec(id="L2", type="label", placement={"kind": "actor", "actor": "ghost"}, data={"name": "x"})
        result = overlays.validate_overlay(label, actors=ACTORS, cast=CAST, style=STYLE)
        self.assertFalse(result["ok"])

    def test_actor_labels_sit_above_the_head_with_a_small_face(self):
        small = [{"id": "widow", "preset": "idle", "x": 540, "y": 1500, "scale": 1.1, "facing": -1}]
        label = spec(id="L3", type="label", placement={"kind": "actor", "actor": "widow"}, data={"name": "The Widow"})
        box = overlays.resolve_box(label, small, CAST)
        anchor = overlays.actor_anchor(small[0], CAST["widow"]["headRadius"])
        self.assertLess(box[1] + box[3], anchor["top"] / 1920 + 0.001)

    def test_project_validation_reports_counts(self):
        project = {
            "style": "cinematic",
            "format": {"width": 1080, "height": 1920, "fps": 30},
            "shots": [{"id": "S01", "actors": ACTORS, "overlays": [spec()]}],
        }
        result = overlays.validate_project(project, cast=CAST, styles=STYLES)
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["counts"]["callout"], 1)


if __name__ == "__main__":
    unittest.main()
