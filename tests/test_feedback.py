"""Feedback memory: scoping, recurrence and generated documents."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import feedback  # noqa: E402


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_category_from_spanish_note(self):
        self.assertEqual(feedback.classify("El movimiento de cámara es demasiado lento"), "camera")
        self.assertEqual(feedback.classify("Las etiquetas están demasiado grandes"), "typography")
        self.assertEqual(feedback.classify("Los gráficos parecen una presentación"), "motion_graphics")

    def test_single_scene_note_stays_local(self):
        record = feedback.add(self.root, problem="En esta escena la etiqueta tapa la cara", scene="S02")
        self.assertEqual(record["scope"], "local")
        self.assertEqual(record["category"], "typography")
        self.assertEqual(record["status"], "recorded")

    def test_global_wording_is_global_but_not_a_rule_until_validated(self):
        record = feedback.add(self.root, problem="En todos los planos el contraste es bajo", requested="subir contraste")
        self.assertEqual(record["scope"], "global")
        feedback.write_documents(self.root)
        rules = open(os.path.join(self.root, "STYLE_RULES.md"), encoding="utf-8").read()
        self.assertIn("No hay reglas promocionadas", rules)

    def test_recurring_is_evidence_not_automatic_rule(self):
        feedback.add(self.root, problem="La cámara va demasiado lenta", scene="S01")
        feedback.add(self.root, problem="Otra vez la cámara demasiado lenta", scene="S03")
        groups = feedback.recurring(self.root)
        self.assertEqual(groups[0]["category"], "camera")
        self.assertEqual(groups[0]["count"], 2)
        self.assertFalse(groups[0]["promotable"])

    def test_validated_non_local_record_becomes_a_rule(self):
        record = feedback.add(self.root, problem="En todos los planos el texto es ilegible")
        feedback.apply_fix(self.root, record["id"], solution="se añadió placa de contraste", component="motion-graphics/annotations.tsx")
        feedback.validate(self.root, record["id"], evidence="contraste medido 96 en la banda de subtítulos")
        feedback.write_documents(self.root)
        rules = open(os.path.join(self.root, "STYLE_RULES.md"), encoding="utf-8").read()
        self.assertIn(record["id"], rules)
        log = open(os.path.join(self.root, "IMPROVEMENT_LOG.md"), encoding="utf-8").read()
        self.assertIn("contraste medido 96", log)

    def test_validation_requires_evidence(self):
        record = feedback.add(self.root, problem="El fondo está vacío")
        with self.assertRaises(feedback.FeedbackError):
            feedback.validate(self.root, record["id"], evidence="  ")

    def test_records_survive_a_reload(self):
        record = feedback.add(self.root, problem="Los cortes son demasiados", scene="S04")
        again = feedback.get(self.root, record["id"])
        self.assertIsNotNone(again)
        self.assertEqual(again["problem"], "Los cortes son demasiados")
        with open(os.path.join(self.root, feedback.RECORDS), encoding="utf-8") as fh:
            self.assertTrue(fh.read().strip())

    def test_regression_case_is_unique(self):
        feedback.add_regression_case(self.root, case_id="R-001", description="demo passes qa", check="qa.ok", threshold="true")
        with self.assertRaises(feedback.FeedbackError):
            feedback.add_regression_case(self.root, case_id="R-001", description="dup", check="x", threshold="y")


if __name__ == "__main__":
    unittest.main()
