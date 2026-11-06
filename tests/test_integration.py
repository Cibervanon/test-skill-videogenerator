"""Tests for the pieces integrated from the external repository.

No test in this file may touch the network: the ElevenLabs path is exercised
only through its refusal gates, with urlopen patched to fail loudly.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import (  # noqa: E402
    edit,
    kokoro_tts,
    kokoro_worker,
    library,
    mixcheck,
    storyboard,
    subtitles,
    voice,
)

PROJECT_JSON = os.path.join(ROOT, "studio", "src", "data", "project.json")


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = library.collect(ROOT)

    def test_catalogue_is_derived_and_complete(self):
        types = {a["type"] for a in self.catalog["assets"]}
        for required in ("character", "set", "rig", "engine", "sfx", "voice", "camera", "transition"):
            self.assertIn(required, types)
        self.assertGreaterEqual(len(self.catalog["assets"]), 20)

    def test_ids_are_unique_and_files_exist(self):
        result = library.validate(self.catalog, ROOT)
        self.assertTrue(result["ok"], result["problems"])

    def test_search_by_query_and_type(self):
        found = library.search(self.catalog, query="keeper")
        self.assertIn("character:elder", [a["id"] for a in found])
        sets = library.search(self.catalog, type_="set")
        self.assertTrue(all(a["type"] == "set" for a in sets))
        self.assertTrue(any(a["id"] == "set:doorway" for a in sets))

    def test_every_asset_declares_a_licence(self):
        for asset in self.catalog["assets"]:
            self.assertTrue(asset["license"], asset["id"])

    def test_reuse_report_resolves_a_project(self):
        report = library.reuse_report(load(PROJECT_JSON), self.catalog, ROOT)
        self.assertTrue(report["ok"], report["missing"])
        self.assertIn("set:doorway", report["reused"])
        self.assertIn("character:elder", report["reused"])

    def test_catalogue_is_written_and_reloadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            # a minimal mirror of the paths the catalogue checks
            for rel in ("studio/src/data", "studio/src/scenes", "studio/src/engine", "config"):
                os.makedirs(os.path.join(tmp, rel), exist_ok=True)
            with open(os.path.join(tmp, "studio", "src", "data", "cast.json"), "w", encoding="utf-8") as fh:
                json.dump({"characters": {}}, fh)
            written = library.build(tmp)
            reloaded = library.load(tmp)
            self.assertEqual(len(written["assets"]), len(reloaded["assets"]))

    def test_fingerprint_changes_with_version(self):
        asset = library.get(self.catalog, "set:doorway")
        self.assertTrue(asset)
        first = library.fingerprint(self.catalog, "set:doorway")
        asset["version"] = (asset.get("version") or 1) + 1
        self.assertNotEqual(first, library.fingerprint(self.catalog, "set:doorway"))


class VoiceTests(unittest.TestCase):
    def test_local_plan_has_timings_and_no_speech(self):
        project = load(PROJECT_JSON)
        plan = voice.plan(project)
        self.assertGreater(plan["total_words"], 20)
        self.assertFalse(plan["speech"])
        for line in plan["lines"]:
            self.assertTrue(line["words"])
            for word in line["words"]:
                self.assertGreaterEqual(word["s"], line["start"] - 0.001)
                self.assertLessEqual(word["e"], line["end"] + 0.001)

    def test_narration_mode_uses_one_narrator_even_when_actors_are_visible(self):
        project = load(PROJECT_JSON)
        project["narration"] = True
        project["shots"] = [
            {**project["shots"][0], "speaker": "elder", "actors": [{"id": "elder"}]},
            {**project["shots"][1], "speaker": "young", "actors": [{"id": "young"}]},
        ]
        plan = voice.plan(project)
        self.assertTrue(plan["narration"])
        self.assertEqual({line["speaker"] for line in plan["lines"]}, {"narrator"})

    def test_dialogue_can_opt_out_of_narration_mode(self):
        project = load(PROJECT_JSON)
        project["narration"] = True
        project["shots"] = [
            {**project["shots"][0], "speaker": "elder", "dialogue": True, "actors": [{"id": "elder"}]},
        ]
        plan = voice.plan(project)
        self.assertEqual(plan["lines"][0]["speaker"], "elder")

    def test_local_generation_writes_only_files_and_never_calls_network(self):
        project = load(PROJECT_JSON)
        with tempfile.TemporaryDirectory() as tmp, mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            result = voice.generate(tmp, project, root=ROOT, provider="local")
            self.assertFalse(result["speech"])
            self.assertTrue(os.path.exists(os.path.join(tmp, "generation", "voice", "voice_plan.json")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "generation", "voice", "words.json")))

    def test_elevenlabs_refuses_without_authorisation(self):
        project = load(PROJECT_JSON)
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")) as net:
            with self.assertRaises(voice.VoiceError):
                voice.generate(tempfile.mkdtemp(), project, root=ROOT, provider="elevenlabs", authorize=False)
            net.assert_not_called()

    def test_elevenlabs_reports_missing_voice_id(self):
        config = {"authorize_spend": True, "voices": {"narrator": {"voice_id": None}}}
        ok, reason = voice.elevenlabs_available(config["voices"]["narrator"], config)
        self.assertFalse(ok)
        self.assertIn("voice_id", reason)

    def test_alignment_becomes_word_timings(self):
        alignment = {
            "characters": list("hi there"),
            "character_start_times_seconds": [i * 0.1 for i in range(8)],
            "character_end_times_seconds": [i * 0.1 + 0.08 for i in range(8)],
        }
        words = voice.alignment_to_words(alignment)
        self.assertEqual([w["w"] for w in words], ["hi", "there"])


class StoryboardTests(unittest.TestCase):
    def test_one_key_frame_inside_every_shot(self):
        project = load(PROJECT_JSON)
        frames = storyboard.key_frames(project)
        self.assertEqual(len(frames), len(project["shots"]))
        for frame, shot in zip(frames, project["shots"]):
            self.assertEqual(frame["id"], shot["id"])
            self.assertGreater(frame["frame"], frame["from"])
            self.assertLessEqual(frame["frame"], frame["from"] + frame["frames"] - 1)


class MixCheckTests(unittest.TestCase):
    def test_local_project_reports_not_applicable_instead_of_passing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mixcheck.check(tmp)
            self.assertFalse(result["applicable"])
            self.assertIn("no speech stem", result["reason"])
            self.assertIn("Not applicable", mixcheck.to_markdown(result))


class ComposeTests(unittest.TestCase):
    """The catalogue must build a project, not just list files."""

    def test_compose_resolves_assets_into_a_manifest(self):
        catalog = library.collect(ROOT)
        spec = load(os.path.join(ROOT, "projects", "demo_003", "spec.json"))
        result = library.compose(spec, catalog)
        self.assertTrue(result["ok"], result["problems"])
        project = result["project"]
        self.assertEqual(len(project["shots"]), len(spec["shots"]))
        self.assertEqual(project["format"]["fps"], 30)
        report = library.reuse_report(project, catalog, ROOT)
        self.assertTrue(report["ok"], report["missing"])
        self.assertIn("set:townnight", report["reused"])

    def test_compose_refuses_an_unknown_asset(self):
        catalog = library.collect(ROOT)
        bad = {"id": "x", "shots": [{"id": "S1", "scene": "atlantis", "camera": "static", "actors": []}]}
        result = library.compose(bad, catalog)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["project"])
        self.assertTrue(any("atlantis" in p for p in result["problems"]))

    def test_compose_refuses_an_unknown_character(self):
        catalog = library.collect(ROOT)
        bad = {
            "id": "x",
            "shots": [{"id": "S1", "scene": "townNight", "camera": "static", "actors": [{"id": "ghost"}]}],
        }
        result = library.compose(bad, catalog)
        self.assertFalse(result["ok"])
        self.assertTrue(any("ghost" in p for p in result["problems"]))

    def test_new_project_reuses_existing_assets_without_duplicating_them(self):
        """A brand new project must be buildable from the library alone."""
        catalog = library.collect(ROOT)
        shot = library.search(catalog, type_="set")[0]
        scene = shot["id"].split(":", 1)[1]
        character = library.search(catalog, type_="character")[0]["id"].split(":", 1)[1]
        spec = {
            "id": "reuse_probe",
            "title": "Reuse probe",
            "shots": [
                {
                    "id": "S1",
                    "scene": scene,
                    "camera": "drift",
                    "seconds": 3,
                    "line": "one line is enough",
                    "actors": [{"id": character, "preset": "idle", "x": 540, "y": 1700, "scale": 1.5}],
                }
            ],
        }
        result = library.compose(spec, catalog)
        self.assertTrue(result["ok"], result["problems"])
        report = library.reuse_report(result["project"], catalog, ROOT)
        self.assertTrue(report["ok"])
        self.assertEqual(report["new_assets_needed"], 0)


class WordEditTests(unittest.TestCase):
    """Word-guided editing, tested with synthetic timings (no provider)."""

    def _project(self):
        return {
            "format": {"fps": 30},
            "transitionFrames": 0,
            "shots": [
                {"id": "S1", "seconds": 3, "transitionIn": 0, "line": "one two three"},
                {"id": "S2", "seconds": 3, "transitionIn": 0, "line": "four five six"},
            ],
        }

    def _words(self, offset=0.0):
        return [
            {"w": "one", "s": 0.1 + offset, "e": 0.3},
            {"w": "two", "s": 0.4, "e": 0.6},
            {"w": "three", "s": 0.7, "e": 1.0},
            {"w": "four", "s": 3.25 + offset, "e": 3.5},
            {"w": "five", "s": 3.6, "e": 3.9},
            {"w": "six", "s": 4.0, "e": 4.2},
        ]

    def test_cues_expose_frames(self):
        cues = edit.cues(self._words(), fps=30)
        self.assertEqual(cues[0]["frame"], 3)
        self.assertEqual(cues[0]["w"], "one")

    def test_alignment_moves_the_cut_to_the_word(self):
        project = self._project()
        # "four" sits at 3.25 s in the fixture while S2 starts at 3.00 s: the
        # alignment must stretch S1 by that 0.25 s so the caption opens on the word.
        result = edit.align_manifest(project, self._words(offset=0.0))
        self.assertTrue(result["ok"], result["shifts"])
        # S2 must now start on "four" at 3.5 s, so S1 grew by 0.25 s
        self.assertAlmostEqual(result["project"]["shots"][0]["seconds"], 3.25, places=2)
        self.assertEqual(result["shifts"][0]["word"], "four")

    def test_alignment_reports_drift_beyond_tolerance_instead_of_hiding_it(self):
        project = self._project()
        result = edit.align_manifest(project, self._words(offset=1.4), tolerance=0.45)
        self.assertFalse(result["ok"])
        self.assertTrue(any(not s["within_tolerance"] for s in result["shifts"]))

    def test_total_duration_is_preserved(self):
        project = self._project()
        before = sum(s["seconds"] for s in project["shots"])
        result = edit.align_manifest(project, self._words(offset=0.3))
        after = sum(s["seconds"] for s in result["project"]["shots"])
        self.assertAlmostEqual(before, after, places=2)

    def test_caption_cues_cover_every_written_shot(self):
        cues = edit.caption_cues(self._project())
        self.assertEqual([c["shot"] for c in cues], ["S1", "S2"])
        self.assertTrue(all(c["end"] > c["start"] for c in cues))


class KokoroTests(unittest.TestCase):
    """Kokoro integration, tested without loading the model.

    These never synthesise: the real take is proven once, outside the suite, by
    `projects/kokoro_demo`. Here we check the contract, the cache and the maths.
    """

    def setUp(self):
        self.config = kokoro_tts.load_config(ROOT)

    def test_config_lists_spanish_voices(self):
        self.assertEqual(self.config["lang_code"], "e")
        for speaker in ("narrator", "elder", "young"):
            spec = kokoro_tts.voice_spec(self.config, speaker)
            self.assertTrue(spec["kokoro"].startswith("e"))

    def test_unknown_speaker_is_refused(self):
        with self.assertRaises(kokoro_tts.KokoroError):
            kokoro_tts.voice_spec(self.config, "nobody")

    def test_cache_key_is_stable_and_sensitive(self):
        base = kokoro_tts.cache_key("hola", "narrator", 1.0, self.config)
        self.assertEqual(base, kokoro_tts.cache_key("hola", "narrator", 1.0, self.config))
        self.assertNotEqual(base, kokoro_tts.cache_key("hola.", "narrator", 1.0, self.config))
        self.assertNotEqual(base, kokoro_tts.cache_key("hola", "elder", 1.0, self.config))
        self.assertNotEqual(base, kokoro_tts.cache_key("hola", "narrator", 1.1, self.config))
        other_model = dict(self.config, model_id="Kokoro-other")
        self.assertNotEqual(base, kokoro_tts.cache_key("hola", "narrator", 1.0, other_model))

    def test_missing_interpreter_reports_instead_of_crashing(self):
        broken = dict(self.config, python=".venv-does-not-exist/python.exe")
        ok, reason = kokoro_tts.available(ROOT, broken)
        self.assertFalse(ok)
        self.assertIn("not found", reason)
        with self.assertRaises(kokoro_tts.KokoroError):
            kokoro_tts.synthesize(
                ROOT, broken, text="hola", speaker="narrator", speed=1.0,
                out_wav=os.path.join(ROOT, ".tmp", "nope.wav"),
                meta_path=os.path.join(ROOT, ".tmp", "nope.json"), allow_download=True,
            )

    def test_weights_are_detected_without_downloading(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = dict(self.config, models_dir="models")
            self.assertFalse(kokoro_tts.model_cached(tmp, config, "ef_dora"))
            voice_dir = os.path.join(tmp, "models", "hub", "models--hexgrad--Kokoro-82M", "snapshots", "rev", "voices")
            os.makedirs(voice_dir)
            open(os.path.join(voice_dir, os.pardir, "config.json"), "w").close()
            open(os.path.join(voice_dir, "ef_dora.pt"), "w").close()
            self.assertTrue(kokoro_tts.model_cached(tmp, config, "ef_dora"))
            self.assertFalse(kokoro_tts.model_cached(tmp, config, "em_alex"))

    def test_pred_dur_is_grouped_into_words(self):
        ps = "nwˈeβe ðˈias"
        pred = [3.0] + [10.0] * len(ps) + [2.0]
        words = kokoro_worker.words_from_pred(ps, pred, "Nueve dias", 1.0, 0.5)
        self.assertEqual([w["w"] for w in words], ["Nueve", "dias"])
        self.assertEqual(words[0]["s"], 1.0)
        # 6 phones x 10 frames = 1.5 s predicted, normalised to the 0.5 s clip:
        # 1.5 * (0.5 / 3.0) = 0.25 s, so the first word ends at 1.25 s.
        self.assertAlmostEqual(words[0]["e"], 1.25, places=3)
        self.assertTrue(all(w["source"] == "pred_dur" for w in words))

    def test_mismatched_phones_fall_back_to_syllables_and_say_so(self):
        words = kokoro_worker.words_from_pred("a", None, "una frase", 0.0, 1.0)
        self.assertEqual(len(words), 2)
        self.assertTrue(all(w["source"] == "syllables" for w in words))

    def test_fit_shots_stretches_only_what_overflows(self):
        project = {
            "format": {"fps": 30},
            "shots": [
                {"id": "S1", "seconds": 4, "transitionIn": 0},
                {"id": "S2", "seconds": 4, "transitionIn": 0},
            ],
        }
        lines = [
            {"shot": "S1", "start": 0.0, "audio_duration": 2.0},
            {"shot": "S2", "start": 4.0, "audio_duration": 6.0},
        ]
        fitted, changes = kokoro_tts.fit_shots(project, lines)
        self.assertEqual([c["shot"] for c in changes], ["S2"])
        self.assertEqual(fitted["shots"][0]["seconds"], 4)
        self.assertAlmostEqual(fitted["shots"][1]["seconds"], 6.25, places=2)
        self.assertEqual(project["shots"][1]["seconds"], 4)  # input not mutated


class SubtitleTests(unittest.TestCase):

    def test_cues_group_by_word_count(self):
        words = [{"w": f"w{i}", "s": i * 0.4, "e": i * 0.4 + 0.35} for i in range(7)]
        cues = subtitles.group_words(words, max_words=3)
        self.assertEqual([len(c["text"].split()) for c in cues], [3, 3, 1])

    def test_srt_timestamps(self):
        text = subtitles.to_srt([{"start": 1.5, "end": 2.25, "text": "hola"}])
        self.assertIn("00:00:01,500 --> 00:00:02,250", text)
        self.assertIn("hola", text)

    def test_plan_cues_are_sorted_and_do_not_invent_time(self):
        plan = {
            "lines": [
                {"words": [{"w": "dos", "s": 3.0, "e": 3.3}]},
                {"words": [{"w": "uno", "s": 0.5, "e": 0.8}]},
            ]
        }
        cues = subtitles.from_plan(plan, max_words=1)
        self.assertEqual([c["text"] for c in cues], ["uno", "dos"])
        self.assertAlmostEqual(cues[0]["start"], 0.5, places=3)


if __name__ == "__main__":
    unittest.main()
