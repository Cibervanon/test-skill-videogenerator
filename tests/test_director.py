"""Creative direction: deterministic planning, honest numbers, style choice."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import director, overlays  # noqa: E402

CAST = overlays.load_cast(ROOT)
FACTS = [
    {"label": "campanas fundidas", "value": 3, "unit": "unidades", "source": "inventario municipal", "numeric": True},
]


class DirectorTests(unittest.TestCase):
    def test_plan_from_a_title_only_is_flagged_as_template(self):
        plan = director.build_plan(title="El pan que no se vendió", cast=CAST, seconds=24)
        self.assertEqual(plan["narration"]["source"], "template")
        self.assertTrue(plan["narration"]["requires_author_approval"])
        self.assertEqual(plan["overlays"]["numeric"], 0)
        self.assertGreaterEqual(len(plan["spec"]["shots"]), 3)

    def test_no_facts_means_no_numeric_graphic(self):
        plan = director.build_plan(title="Una idea", idea="algo cotidiano", cast=CAST)
        numeric = [o for s in plan["spec"]["shots"] for o in s["overlays"] if o["type"] in overlays.NUMERIC_TYPES]
        self.assertEqual(numeric, [])

    def test_facts_produce_numeric_overlays_with_a_source(self):
        plan = director.build_plan(title="Tres campanas", idea="un inventario", cast=CAST, facts=FACTS)
        numeric = [o for s in plan["spec"]["shots"] for o in s["overlays"] if o["type"] in overlays.NUMERIC_TYPES]
        self.assertTrue(numeric)
        for item in numeric:
            self.assertTrue(item["source"])

    def test_user_style_is_respected(self):
        plan = director.build_plan(title="Prueba", script="Una línea. Otra línea.", style="minimal", cast=CAST)
        self.assertEqual(plan["style"]["id"], "minimal")
        self.assertIn("usuario", plan["style"]["reason"])

    def test_style_is_explained_when_not_specified(self):
        plan = director.build_plan(title="Datos del pueblo", idea="cifras", cast={}, facts=FACTS, seconds=30)
        self.assertEqual(plan["style"]["id"], "infographic")
        self.assertTrue(plan["style"]["reason"])

    def test_plan_overlays_pass_the_validator(self):
        plan = director.build_plan(title="La campana", script="El viejo no la toca. El aprendiz insiste. Nadie duerme.", cast=CAST)
        project = {**plan["spec"], "style": plan["style"]["id"], "format": {"width": 1080, "height": 1920, "fps": 30}}
        result = overlays.validate_project(project, cast=CAST, styles=overlays.load_styles(ROOT))
        self.assertTrue(result["ok"], result["problems"])

    def test_plan_writes_files(self):
        plan = director.build_plan(title="Un título", cast=CAST)
        with tempfile.TemporaryDirectory() as tmp:
            paths = director.write_plan(tmp, plan)
            for path in paths.values():
                self.assertTrue(os.path.exists(path), path)
            self.assertIn("plan de dirección", open(paths["board_plan"], encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
