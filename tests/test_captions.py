"""Word-timed captions, mix sample-rate handling and QA robustness."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import captions, narration, qa  # noqa: E402


def project() -> dict:
    return {
        "format": {"fps": 30},
        "transitionFrames": 0,
        "shots": [
            {"id": "S1", "seconds": 3, "transitionIn": 0, "line": "uno dos tres cuatro"},
            {"id": "S2", "seconds": 3, "transitionIn": 0, "line": "cinco seis"},
        ],
    }


def plan() -> dict:
    return {
        "provider": "fixture",
        "narration": True,
        "project_seconds": 6.0,
        "stem": "generation/voice/voice.wav",
        "lines": [
            {
                "shot": "S1",
                "speaker": "narrator",
                "text": "uno dos tres cuatro",
                "start": 0.0,
                "end": 3.0,
                "audio": "generation/voice/take.wav",
                "audio_duration": 1.0,
                "words": [
                    {"w": "uno", "s": 0.1, "e": 0.3},
                    {"w": "dos", "s": 0.35, "e": 0.55},
                    {"w": "tres", "s": 0.7, "e": 0.95},
                    {"w": "cuatro", "s": 1.0, "e": 1.4},
                ],
            },
            {
                "shot": "S2",
                "speaker": "narrator",
                "text": "cinco seis",
                "start": 3.0,
                "end": 6.0,
                "audio": "generation/voice/take2.wav",
                "audio_duration": 0.8,
                "words": [
                    {"w": "cinco", "s": 3.2, "e": 3.5},
                    {"w": "seis", "s": 3.6, "e": 3.9},
                ],
            },
        ],
    }


def write_wav(path: str, data: np.ndarray, sr: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())


class CaptionTimingTests(unittest.TestCase):
    def test_cues_are_placed_on_the_real_word_clock(self):
        result = captions.attach(project(), plan(), max_words=2)
        self.assertTrue(result["ok"], result["problems"])
        cues = result["project"]["shots"][0]["captions"]
        self.assertEqual([cue["text"] for cue in cues], ["uno dos", "tres cuatro"])
        self.assertAlmostEqual(cues[0]["start"], 0.1, places=3)
        self.assertAlmostEqual(cues[1]["start"], 0.7, places=3)
        self.assertEqual(result["project"]["shots"][1]["captions"][0]["start"], 0.2)

    def test_reveal_error_is_zero_milliseconds(self):
        result = captions.attach(project(), plan())
        # The gate is 120 ms; the data path introduces no error at all because
        # the cue start IS the word start, not a re-estimate of it.
        self.assertEqual(captions.max_reveal_error(result["project"], plan()), 0.0)

    def test_no_word_is_lost_or_duplicated(self):
        result = captions.attach(project(), plan())
        rendered = " ".join(
            cue["text"] for shot in result["project"]["shots"] for cue in shot.get("captions", [])
        ).split()
        spoken = [word["w"] for line in plan()["lines"] for word in line["words"]]
        self.assertEqual(rendered, spoken)

    def test_stale_voice_plan_is_rejected_instead_of_attaching_wrong_words(self):
        data = project()
        data["shots"][0]["line"] = "una línea distinta"
        result = captions.attach(data, plan())
        self.assertFalse(result["ok"])
        self.assertTrue(any("does not match" in problem for problem in result["problems"]))
        self.assertNotIn("captions", result["project"]["shots"][0])

    def test_plan_for_an_unknown_shot_is_rejected(self):
        data = plan()
        data["lines"][0]["shot"] = "S99"
        result = captions.attach(project(), data)
        self.assertFalse(result["ok"])
        self.assertTrue(any("not in the manifest" in problem for problem in result["problems"]))

    def test_wordless_shot_gets_no_cues(self):
        data = project()
        empty = plan()
        empty["lines"] = []
        result = captions.attach(data, empty)
        self.assertTrue(result["ok"])
        self.assertTrue(all("captions" not in shot for shot in result["project"]["shots"]))


class NarrationSampleRateTests(unittest.TestCase):
    def test_mix_is_read_at_its_own_sample_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 24 kHz takes/stem, 8 kHz mix: indexing the mix as 48 kHz would read
            # past the end and report the line as silent.
            tone = 0.4 * np.sin(2 * np.pi * 220 * np.linspace(0, 0.4, 9600, endpoint=False))
            write_wav(os.path.join(tmp, "generation/voice/take.wav"), tone, 24000)
            write_wav(os.path.join(tmp, "generation/voice/take2.wav"), tone, 24000)
            stem = np.zeros(24000, dtype=np.float32)
            stem[12000:21600] = tone[:9600]
            write_wav(os.path.join(tmp, "generation/voice/voice.wav"), stem, 24000)
            mix = np.zeros(8000, dtype=np.float32)
            mix[4000:7200] = 0.3 * np.sin(2 * np.pi * 220 * np.linspace(0, 0.4, 3200, endpoint=False))
            write_wav(os.path.join(tmp, "generation/audio/mix.wav"), mix, 8000)

            data = plan()
            data["lines"] = [
                {
                    "shot": "S1",
                    "speaker": "narrator",
                    "text": "uno dos tres cuatro",
                    "start": 0.5,
                    "end": 1.0,
                    "audio": "generation/voice/take.wav",
                    "audio_duration": 0.4,
                    "words": [{"w": "uno", "s": 0.5, "e": 0.9}],
                }
            ]
            report = narration.validate(tmp, data)
            self.assertTrue(report["ok"], report["problems"])
            self.assertGreater(report["rows"][0]["mix_rms_db"], -40)
            self.assertEqual(report["mix_seconds"], 1.0)


class CaptionCoverageTests(unittest.TestCase):
    def test_shot_without_a_line_key_does_not_crash_qa(self):
        data = {
            "format": {"fps": 30},
            "transitionFrames": 0,
            "shots": [
                {"id": "S1", "seconds": 2, "line": "hola"},
                {"id": "S2", "seconds": 2},
            ],
        }
        coverage = qa.caption_coverage(data, transition_frames=0, fps=30)
        self.assertAlmostEqual(coverage["coverage"], 0.5, places=3)
        self.assertEqual(coverage["uncovered"][0]["shot"], "S2")


if __name__ == "__main__":
    unittest.main()
