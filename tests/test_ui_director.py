"""Tests for the contextual UI director and its QA.

These assert the *decision rules*, not taste: a mode is chosen from the shot's
intent and payload, a box never covers a face/body/caption in B or C, and an
element without room is escalated instead of squeezed.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import overlays, ui_director, uiqa  # noqa: E402

CAST = overlays.load_cast(ROOT) or {"elder": {"headRadius": 46}, "young": {"headRadius": 46}}
STYLE = {"ui": {"maxPanels": 2, "density": "low"}}
STYLES = {"default": "cinematic", "styles": {"cinematic": STYLE}}


def shot(**kwargs):
    base = {
        "id": "S01",
        "scene": "townNight",
        "camera": "drift",
        "seconds": 4.0,
        "line": "",
        "actors": [],
        "overlays": [],
    }
    base.update(kwargs)
    return base


def counter(**extra):
    return {
        "id": "U1",
        "type": "counter",
        "placement": {"kind": "screen"},
        "anchor": "top-left",
        "from": 0.18,
        "to": 0.80,
        "illustrative": True,
        "data": {"title": "sin campana", "value": 3, "unit": "inviernos"},
        **extra,
    }


class ClassifyTest(unittest.TestCase):
    def test_intents(self):
        cases = {
            "El aprendiz señaló la cuerda.": "accion",
            "Comparó lo que el pueblo creía con lo que vio.": "comparacion",
            "El mecanismo tenía tres pasos.": "proceso",
            "El pueblo llevaba tres inviernos sin oírla.": "dato",
            "En realidad, no era una campana normal.": "aclaracion",
            "Desde entonces, el silencio tuvo fecha.": "cierre",
            "El guardián recordó lo que había sucedido.": "emocion",
            "Nadie supo cuándo dejó de sonar.": "narracion",
        }
        for text, expected in cases.items():
            self.assertEqual(ui_director.classify(text), expected, text)


class ModeTest(unittest.TestCase):
    def test_no_ui_is_scene_only(self):
        mode, _ = ui_director.choose_mode(intent="narracion", overlays=[], actors=[])
        self.assertEqual(mode, "A")

    def test_counter_over_scene_is_b(self):
        mode, _ = ui_director.choose_mode(intent="dato", overlays=[counter()], actors=[{"id": "elder"}])
        self.assertEqual(mode, "B")

    def test_label_is_c(self):
        label = {"type": "label", "data": {"name": "el aprendiz"}}
        mode, _ = ui_director.choose_mode(intent="accion", overlays=[label], actors=[{"id": "young"}])
        self.assertEqual(mode, "C")

    def test_comparison_is_d(self):
        chart = {"type": "bar", "data": {"series": []}}
        mode, _ = ui_director.choose_mode(intent="comparacion", overlays=[chart], actors=[{"id": "elder"}])
        self.assertEqual(mode, "D")

    def test_process_is_e(self):
        mode, _ = ui_director.choose_mode(intent="proceso", overlays=[{"type": "process", "data": {"steps": []}}], actors=[])
        self.assertEqual(mode, "E")

    def test_bridge_is_f(self):
        bridge = counter(ui_role="bridge")
        mode, _ = ui_director.choose_mode(intent="cierre", overlays=[bridge], actors=[])
        self.assertEqual(mode, "F")


class ReadingTest(unittest.TestCase):
    def test_more_text_needs_more_time(self):
        short = ui_director.reading_seconds({"type": "callout", "data": {"title": "hola"}})
        long = ui_director.reading_seconds(
            {"type": "callout", "data": {"title": "hola", "caption": "una explicación bastante más larga que la anterior"}}
        )
        self.assertGreater(long, short)

    def test_chart_gets_a_scan_beat(self):
        one = ui_director.reading_seconds({"type": "bar", "data": {"series": [{"label": "a", "value": 1}]}})
        two = ui_director.reading_seconds({"type": "bar", "data": {"series": [{"label": "a", "value": 1}, {"label": "b", "value": 2}]}})
        self.assertGreater(two, one)


class FaceTest(unittest.TestCase):
    def test_face_below_the_top_third_is_detected(self):
        # Regression: the old clamp mixed normalised and pixel units, so a face
        # at y=0.63 read as "not covered" by a chart ending at 0.61.
        self.assertTrue(overlays.circle_hits_box(380, 1203, 78, (0.07, 0.31, 0.86, 0.30)))
        self.assertFalse(overlays.circle_hits_box(380, 1203, 78, (0.07, 0.06, 0.86, 0.30)))


class PlacementTest(unittest.TestCase):
    actor = {"id": "elder", "x": 540, "y": 1600, "scale": 1.65, "facing": 1}

    def test_compact_box_never_covers_the_body(self):
        result = overlays.resolve_ui_box((0.34, 0.12), [self.actor], CAST, mode="B")
        self.assertIsNotNone(result["box"])
        box = result["box"]
        self.assertLessEqual(overlays.overlap_area(box, overlays.body_box(self.actor, CAST)), overlays.BODY_TOLERANCE)
        self.assertFalse(
            overlays.intersects(box, (0, overlays.CAPTION_BAND[0], 1, overlays.CAPTION_BAND[1] - overlays.CAPTION_BAND[0]))
        )

    def test_no_room_escalates_instead_of_squeezing(self):
        # A full-width plate with a huge central body has nowhere to go.
        big_actor = {"id": "elder", "x": 540, "y": 1900, "scale": 4.2, "facing": 1}
        result = overlays.resolve_ui_box((0.9, 0.42), [big_actor], CAST, mode="B", shrink=0)
        self.assertIsNone(result["box"])
        self.assertEqual(result["mode_shift"], "D")

    def test_escalation_opens_room(self):
        big_actor = {"id": "elder", "x": 540, "y": 1900, "scale": 4.2, "facing": 1}
        result = overlays.resolve_ui_box((0.86, 0.30), [big_actor], CAST, mode="D")
        self.assertIsNotNone(result["box"])

    def test_anchor_preference_wins_when_free(self):
        side = {"id": "elder", "x": 250, "y": 1600, "scale": 1.6, "facing": 1}
        result = overlays.resolve_ui_box((0.34, 0.12), [side], CAST, mode="B", anchor="top-right")
        self.assertEqual(result["anchor"], "top-right")


class PlanTest(unittest.TestCase):
    def test_action_drops_a_heavy_chart(self):
        plan = ui_director.plan_shot(
            shot(line="El aprendiz subió al campanario.", overlays=[counter(type="bar", data={"series": [{"label": "a", "value": 1}]})]),
            cast=CAST,
            style=STYLE,
        )
        self.assertEqual(plan["mode"], "A")
        self.assertTrue(plan["dropped"])
        self.assertEqual(plan["overlays"], [])

    def test_counter_goes_to_b_and_leaves_before_the_end(self):
        plan = ui_director.plan_shot(
            shot(line="El pueblo llevaba tres inviernos.", actors=[{"id": "elder", "x": 700, "y": 1900, "scale": 3.4, "facing": 1}], overlays=[counter()]),
            cast=CAST,
            style=STYLE,
        )
        self.assertEqual(plan["mode"], "B")
        overlay = plan["overlays"][0]
        self.assertLessEqual(overlay["to"], 0.90)
        self.assertGreater(overlay["from"], 0)
        self.assertEqual(overlay["placement"]["kind"], "screen")
        self.assertTrue(overlay["ui"]["reason"])

    def test_process_owns_the_frame(self):
        process = {
            "id": "U5",
            "type": "process",
            "placement": {"kind": "screen"},
            "anchor": "center",
            "data": {"title": "cómo suena", "steps": [{"label": "tensar"}, {"label": "soltar"}, {"label": "esperar"}]},
        }
        plan = ui_director.plan_shot(shot(line="El mecanismo tenía tres pasos.", overlays=[process]), cast=CAST, style=STYLE)
        self.assertEqual(plan["mode"], "E")
        self.assertTrue(plan["presentation"]["independent"])
        self.assertGreaterEqual(plan["overlays"][0]["placement"]["box"]["w"], 0.7)

    def test_bridge_fills_the_frame_and_reaches_the_cut(self):
        bridge = counter(ui_role="bridge")
        plan = ui_director.plan_shot(shot(line="Desde entonces, el silencio tuvo fecha.", ui_role="bridge", overlays=[bridge]), cast=CAST, style=STYLE)
        self.assertEqual(plan["mode"], "F")
        self.assertTrue(plan["presentation"]["bridge"])
        box = plan["overlays"][0]["placement"]["box"]
        self.assertEqual((box["x"], box["y"], box["w"], box["h"]), (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(plan["overlays"][0]["to"], 1.0)

    def test_project_plan_records_modes(self):
        project = {
            "id": "t",
            "style": "cinematic",
            "format": {"width": 1080, "height": 1920, "fps": 30},
            "shots": [
                shot(id="S01", line="Nadie supo cuándo dejó de sonar."),
                shot(id="S02", line="El pueblo llevaba tres inviernos.", actors=[{"id": "elder", "x": 700, "y": 1900, "scale": 3.4, "facing": 1}], overlays=[counter()]),
            ],
        }
        result = ui_director.plan_project(project, cast=CAST, styles=STYLES)
        self.assertEqual(result["record"]["modes"], {"A": 1, "B": 1})
        self.assertEqual(result["project"]["shots"][1]["presentation"]["mode"], "B")


class UiQaTest(unittest.TestCase):
    def _project(self, **shot_updates):
        base = shot(
            id="S01",
            seconds=4.0,
            line="El pueblo llevaba tres inviernos.",
            actors=[{"id": "elder", "x": 700, "y": 1900, "scale": 3.4, "facing": 1}],
            intent="dato",
            presentation={"mode": "B", "reason": "aclaración breve"},
            overlays=[
                counter(
                    placement={"kind": "screen", "box": {"x": 0.06, "y": 0.10, "w": 0.34, "h": 0.12}},
                    **{"from": 0.2, "to": 0.7},
                )
            ],
        )
        base.update(shot_updates)
        return {"id": "t", "style": "cinematic", "format": {"width": 1080, "height": 1920, "fps": 30}, "shots": [base]}

    def test_clean_b_is_ok(self):
        report = uiqa.inspect_ui(self._project(), cast=CAST, styles=STYLES)
        self.assertTrue(report["ok"], report["problems"])

    def test_mode_a_with_ui_fails(self):
        report = uiqa.inspect_ui(self._project(presentation={"mode": "A"}), cast=CAST, styles=STYLES)
        self.assertFalse(report["ok"])

    def test_ui_that_stays_to_the_end_fails(self):
        report = uiqa.inspect_ui(self._project(overlays=[counter(**{"from": 0.2, "to": 0.99})]), cast=CAST, styles=STYLES)
        self.assertFalse(report["ok"])
        self.assertTrue(any("retirarse" in p for p in report["problems"]))

    def test_short_window_fails(self):
        report = uiqa.inspect_ui(self._project(overlays=[counter(**{"from": 0.2, "to": 0.35})]), cast=CAST, styles=STYLES)
        self.assertFalse(report["ok"])
        self.assertTrue(any("lectura" in p for p in report["problems"]))

    def test_body_overlap_fails(self):
        over_body = counter(placement={"kind": "screen", "box": {"x": 0.55, "y": 0.55, "w": 0.4, "h": 0.2}})
        report = uiqa.inspect_ui(self._project(overlays=[over_body]), cast=CAST, styles=STYLES)
        self.assertFalse(report["ok"])
        self.assertTrue(any("cuerpo" in p for p in report["problems"]))

    def test_mode_d_needs_a_scrim(self):
        report = uiqa.inspect_ui(
            self._project(presentation={"mode": "D", "reason": "comparación"}, overlays=[counter(**{"from": 0.2, "to": 0.7})]),
            cast=CAST,
            styles=STYLES,
        )
        self.assertFalse(report["ok"])
        self.assertTrue(any("atenuación" in p for p in report["problems"]))


if __name__ == "__main__":
    unittest.main()
