"""Tests for the shared asset forge and its integration with the renderer."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import asset_forge, generated, library, references  # noqa: E402


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class ForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = library.collect(ROOT)

    def test_generated_assets_are_schema2_and_validated(self):
        ids = {"set:laboratorio", "character:cientifico", "expression:surprise_cientifico",
               "prop:lampara_laboratorio", "graphic:comparacion"}
        found = {a["id"] for a in self.catalog["assets"] if a.get("schema") == 2}
        self.assertTrue(ids <= found, ids - found)
        for asset in self.catalog["assets"]:
            if asset.get("schema") == 2:
                self.assertTrue(asset["preview"], asset["id"])
                self.assertTrue(asset["provenance"]["origin"], asset["id"])
                self.assertEqual(asset["status"], "validated", asset["id"])

    def test_versions_are_append_only_and_current_pointer_is_latest(self):
        entry = library.get(self.catalog, "set:laboratorio")
        self.assertGreaterEqual(len(entry["versions"]), 2)
        self.assertEqual(entry["version"], max(v["version"] for v in entry["versions"]))
        first, second = entry["versions"][0], entry["versions"][1]
        self.assertNotEqual(first["path"], second["path"])
        self.assertTrue(os.path.exists(os.path.join(ROOT, first["path"])))
        self.assertTrue(os.path.exists(os.path.join(ROOT, second["path"])))
        self.assertEqual(library.get(self.catalog, "set:laboratorio", version=1)["version"], 1)

    def test_previews_exist_and_open(self):
        for asset in self.catalog["assets"]:
            if asset.get("schema") != 2:
                continue
            path = os.path.join(ROOT, asset["preview"])
            self.assertTrue(os.path.exists(path), path)
            self.assertTrue(path.endswith(".svg"), path)
            with open(path, "rb") as fh:
                self.assertIn(b"<svg", fh.read(200))

    def test_search_can_find_by_style_scene_usage_and_compatibility(self):
        by_scene = library.search(self.catalog, scene="laboratorio")
        self.assertIn("set:laboratorio", [a["id"] for a in by_scene])
        by_usage = library.search(self.catalog, usage="prop")
        self.assertIn("prop:lampara_laboratorio", [a["id"] for a in by_usage])
        by_style = library.search(self.catalog, style="cinematic", type_="set")
        self.assertIn("set:laboratorio", [a["id"] for a in by_style])
        by_compat = library.search(self.catalog, compatible="remotion")
        self.assertIn("set:laboratorio", [a["id"] for a in compatible_ids(by_compat)])

    def test_similarity_helps_reuse_instead_of_duplicating(self):
        similar = library.similar(self.catalog, "set:laboratorio", limit=4)
        self.assertTrue(similar)
        self.assertTrue(all("similarity" in a for a in similar))
        self.assertTrue(any(a["type"] == "set" for a in similar))

    def test_compose_resolves_generated_props_expressions_and_graphics(self):
        spec = load(os.path.join(ROOT, "projects", "asset_forge", "spec.json"))
        result = library.compose(spec, self.catalog)
        self.assertTrue(result["ok"], result["problems"])
        shot = result["project"]["shots"][0]
        self.assertEqual(shot["props"][0]["id"], "prop:lampara_laboratorio")
        self.assertEqual(shot["actors"][0]["expression"], "surprise_cientifico")
        self.assertEqual(shot["overlays"][0]["type"], "bar")
        report = library.reuse_report(result["project"], self.catalog, ROOT)
        self.assertTrue(report["ok"], report["missing"])
        self.assertEqual(report["new_assets_needed"], 0)

    def test_compose_preserves_narration_mode(self):
        spec = load(os.path.join(ROOT, "projects", "asset_forge", "spec.json"))
        spec["narration"] = True
        result = library.compose(spec, self.catalog)
        self.assertTrue(result["ok"], result["problems"])
        self.assertTrue(result["project"]["narration"])

    def test_compose_refuses_unknown_prop_expression_and_graphic(self):
        base = load(os.path.join(ROOT, "projects", "asset_forge", "spec.json"))
        for field, value in (("props", [{"id": "prop:missing"}]), ("graphics", ["graphic:missing"])):
            spec = json.loads(json.dumps(base))
            spec["shots"][0][field] = value
            result = library.compose(spec, self.catalog)
            self.assertFalse(result["ok"], field)
        spec = json.loads(json.dumps(base))
        spec["shots"][0]["actors"][0]["expression"] = "missing"
        self.assertFalse(library.compose(spec, self.catalog)["ok"])

    def test_invalid_generated_specs_are_rejected_before_registration(self):
        problems = asset_forge._validate_spec("set", {"renderer": "generated-set-v1", "layers": [], "viewBox": [0, 0, 10, 10]}, preview=None)
        self.assertTrue(problems)
        bad = asset_forge._validate_spec("character", {"id": "x", "headRadius": 5, "height": 3}, preview=None)
        self.assertTrue(bad)

    def test_duplicate_is_noop_and_changed_request_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = asset_forge.create_bundle("Genera un fondo de laboratorio", tmp, asset_id="probe")
            self.assertTrue(first["ok"], first.get("problems"))
            duplicate = asset_forge.create_bundle("Genera un fondo de laboratorio", tmp, asset_id="probe")
            self.assertTrue(duplicate["duplicate"])
            changed = asset_forge.create_bundle("Genera un fondo nocturno de laboratorio", tmp, asset_id="probe")
            self.assertTrue(changed["ok"], changed.get("problems"))
            self.assertFalse(changed["duplicate"])
            self.assertEqual(changed["asset"]["version"], 2)
            registry = generated.load_registry(tmp)
            entry = next(a for a in registry["assets"] if a["id"] == "set:probe")
            self.assertEqual(len(entry["versions"]), 2)
            self.assertTrue(all(os.path.exists(os.path.join(tmp, v["path"])) for v in entry["versions"]))

    def test_generated_character_merges_without_overwriting_canonical_cast(self):
        merged = generated.merge_cast(ROOT, load(os.path.join(ROOT, "studio", "src", "data", "cast.json")))
        self.assertIn("cientifico", merged["characters"])
        self.assertIn("elder", merged["characters"])
        self.assertEqual(merged["characters"]["elder"]["name"], "The Bell-Keeper")

    def test_reference_library_is_metadata_only_and_licence_checked(self):
        data = references.load(ROOT)
        report = references.validate(data, ROOT)
        self.assertTrue(report["ok"], report["problems"])
        selected = references.select(data, purposes=("lighting",), tags=("night",))
        self.assertTrue(selected)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                references.add(tmp, name="x", purpose="lighting", source="missing.jpg", license_="CC0")
            with self.assertRaises(ValueError):
                references.add(tmp, name="x", purpose="not-a-purpose", source="scripts/studio.py", license_="CC0")

    def test_real_proof_stills_exist_and_are_not_blank(self):
        for name in ("A01_generated.png", "A02_existing.png"):
            path = os.path.join(ROOT, "projects", "asset_forge", "preview", name)
            self.assertTrue(os.path.exists(path), path)
            with Image.open(path) as image:
                self.assertGreater(image.width, 100)
                self.assertGreater(os.path.getsize(path), 10_000)
                self.assertIsNotNone(image.convert("RGB").getbbox())


def compatible_ids(assets: list[dict]) -> list[dict]:
    return assets


if __name__ == "__main__":
    unittest.main()
