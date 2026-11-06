"""Identity audit: canonical cast, no shot-level variants."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import identity  # noqa: E402


def character(cid="char_a", **extra):
    base = {
        "id": cid,
        "name": "A",
        "coat": "#b8423f",
        "coatDark": "#7d2b2b",
        "hat": "#e9d7b4",
        "hatBand": "#b8423f",
        "height": 1.0,
        "headRadius": 46,
        "hatStyle": "beanie",
        "hairStyle": "none",
        "facialHair": "moustache",
        "silhouette": "tall coat",
        "wardrobe_states": {"default": "red coat"},
    }
    base.update(extra)
    return base


def project(actors=None):
    return {
        "shots": [
            {
                "id": "S01",
                "presentation": {"mode": "A"},
                "actors": actors if actors is not None else [{"id": "elder", "scale": 1.8, "preset": "idle"}],
            }
        ]
    }


class IdentityTests(unittest.TestCase):
    def test_canonical_cast_passes(self):
        report = identity.audit(project(), {"elder": character()})
        self.assertTrue(report["ok"])
        self.assertEqual(report["coverage"]["elder"]["shots"], ["S01"])

    def test_unknown_actor_fails(self):
        report = identity.audit(project([{"id": "ghost"}]), {"elder": character()})
        self.assertFalse(report["ok"])
        self.assertTrue(any("no canonical identity" in p for p in report["problems"]))

    def test_shot_cannot_override_identity(self):
        report = identity.audit(project([{"id": "elder", "coat": "#00ff00"}]), {"elder": character()})
        self.assertFalse(report["ok"])
        self.assertTrue(any("overrides canonical coat" in p for p in report["problems"]))

    def test_duplicate_canonical_ids_fail(self):
        report = identity.audit(project(), {"elder": character(), "twin": character()})
        self.assertFalse(report["ok"])
        self.assertTrue(any("duplicate canonical id" in p for p in report["problems"]))

    def test_unused_character_is_a_warning_not_a_failure(self):
        report = identity.audit(project(), {"elder": character(), "widow": character("char_w")})
        self.assertTrue(report["ok"])
        self.assertTrue(any("never appears" in w for w in report["warnings"]))

    def test_reports_head_to_body_proportion(self):
        report = identity.audit(project(), {"elder": character()})
        elder = report["characters"][0]
        self.assertAlmostEqual(elder["head_to_body"], 92 / 170, places=3)
        self.assertTrue(identity.PROPORTION_BAND[0] <= elder["head_to_body"] <= identity.PROPORTION_BAND[1])

    def test_unregistered_wardrobe_fails(self):
        report = identity.audit(project([{"id": "elder", "wardrobe": "snow"}]), {"elder": character()})
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
