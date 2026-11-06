"""Pixel inspection: measured signals, with thresholds that must catch a defect."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import inspect as inspect_mod  # noqa: E402

STYLE = inspect_mod.load_style(ROOT, "cinematic")


def _big_font(size: int = 46):
    for candidate in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/DejaVuSans-Bold.ttf"):
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def flat(path: str, colour=(40, 40, 46)) -> str:
    Image.new("RGB", (540, 960), colour).save(path)
    return path


def detailed(path: str, *, caption=True) -> str:
    image = Image.new("RGB", (540, 960), (18, 14, 26))
    draw = ImageDraw.Draw(image)
    for y in range(0, 960, 24):
        draw.line([(0, y + (y % 7)), (540, y - (y % 5))], fill=(200, 170, 130), width=3)
        draw.ellipse([40 + (y % 300), y, 160 + (y % 300), y + 40], fill=(120, 60, 50))
    draw.rectangle([0, 820, 540, 905], fill=(0, 0, 0))
    if caption:
        # captions are large type; a default 11px font would occupy <3% of the band
        # and the percentile spread would read as zero for the wrong reason
        draw.text((40, 838), "TEXTO LEGIBLE", fill=(255, 250, 240), font=_big_font())
    image.save(path)
    return path


def low_contrast_caption(path: str) -> str:
    image = Image.new("RGB", (540, 960), (150, 150, 150))
    draw = ImageDraw.Draw(image)
    draw.text((40, 838), "TEXTO GRIS", fill=(160, 160, 160), font=_big_font())
    image.save(path)
    return path


class InspectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_flat_frame_is_flagged_as_empty(self):
        metrics = inspect_mod.frame_metrics(flat(os.path.join(self.dir, "flat.png")), STYLE)
        self.assertGreater(metrics["empty_ratio"], 0.9)
        flags = inspect_mod.flags_for(metrics)
        self.assertTrue(any("vacía" in f for f in flags))

    def test_detailed_frame_has_subject_and_depth(self):
        metrics = inspect_mod.frame_metrics(detailed(os.path.join(self.dir, "detail.png")), STYLE)
        self.assertLess(metrics["empty_ratio"], 0.55)
        self.assertGreater(metrics["subject_score"], 1.2)
        self.assertGreaterEqual(metrics["depth_bands"], 1)

    def test_caption_band_contrast_separates_readable_from_grey(self):
        readable = inspect_mod.frame_metrics(detailed(os.path.join(self.dir, "cap.png")), STYLE)
        grey = inspect_mod.frame_metrics(low_contrast_caption(os.path.join(self.dir, "grey.png")), STYLE)
        self.assertGreater(readable["caption_contrast"]["spread"], grey["caption_contrast"]["spread"])

    def test_flags_caption_risk_only_when_the_shot_has_words(self):
        metrics = inspect_mod.frame_metrics(low_contrast_caption(os.path.join(self.dir, "grey.png")), STYLE)
        metrics["has_captions"] = True
        self.assertTrue(any("texto" in f for f in inspect_mod.flags_for(metrics)))
        metrics["has_captions"] = False
        self.assertFalse(any("texto de riesgo" in f for f in inspect_mod.flags_for(metrics)))

    def test_stills_report_is_written_and_separates_evidence(self):
        board = os.path.join(self.dir, "board")
        os.makedirs(board)
        detailed(os.path.join(board, "S01.png"))
        project = {
            "style": "cinematic",
            "format": {"width": 1080, "height": 1920, "fps": 30},
            "shots": [{"id": "S01", "scene": "fieldDawn", "seconds": 4, "line": "una línea", "actors": [], "overlays": []}],
        }
        report = inspect_mod.inspect_stills(self.dir, project, root=ROOT, board_dir=board)
        self.assertEqual(report["aesthetic_review"]["status"], "pending")
        self.assertIn("geometry", report["method"])
        paths = inspect_mod.write_report(self.dir, report)
        self.assertIn("Visual inspection", open(paths["markdown"], encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
