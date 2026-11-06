"""Narration validation: a real signal in the take, the stem and the mix."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import narration  # noqa: E402


def write(path, data, sr):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())


def plan(duration=0.8):
    return {
        "provider": "kokoro",
        "model": "test",
        "narration": False,
        "project_seconds": 1.0,
        "stem": "generation/voice/voice.wav",
        "lines": [
            {
                "shot": "S01",
                "speaker": "narrator",
                "voice": "ef_dora",
                "text": "una línea",
                "start": 0.0,
                "end": 1.0,
                "audio": "generation/voice/take.wav",
                "audio_duration": duration,
                "words": [{"w": "una", "s": 0.0, "e": 0.3}, {"w": "línea", "s": 0.3, "e": 0.7}],
            }
        ],
    }


class NarrationTests(unittest.TestCase):
    def test_audible_take_stem_and_mix_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = np.linspace(0, 0.4, int(0.4 * 24000), endpoint=False)
            tone = 0.4 * np.sin(2 * np.pi * 220 * t)
            write(os.path.join(tmp, "generation/voice/take.wav"), tone, 24000)
            write(os.path.join(tmp, "generation/voice/voice.wav"), np.concatenate([tone, np.zeros(1200)]), 24000)
            t2 = np.linspace(0, 1.0, 48000, endpoint=False)
            write(os.path.join(tmp, "generation/audio/mix.wav"), 0.3 * np.sin(2 * np.pi * 220 * t2), 48000)
            report = narration.validate(tmp, plan(duration=0.4))
            self.assertTrue(report["ok"], report["problems"])
            self.assertEqual(report["lines"], 1)
            self.assertGreater(report["rows"][0]["stem_rms_db"], -40)

    def test_silent_stem_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "generation/voice/take.wav"), np.zeros(9600), 24000)
            write(os.path.join(tmp, "generation/voice/voice.wav"), np.zeros(24000), 24000)
            write(os.path.join(tmp, "generation/audio/mix.wav"), np.zeros(48000), 48000)
            report = narration.validate(tmp, plan())
            self.assertFalse(report["ok"])
            self.assertTrue(any("silent" in p for p in report["problems"]))

    def test_narration_mode_rejects_a_second_voice_and_character_speaker(self):
        with tempfile.TemporaryDirectory() as tmp:
            tone = 0.4 * np.sin(2 * np.pi * 220 * np.linspace(0, 1.0, 24000, endpoint=False))
            write(os.path.join(tmp, "generation/voice/take.wav"), tone, 24000)
            write(os.path.join(tmp, "generation/voice/voice.wav"), tone, 24000)
            write(os.path.join(tmp, "generation/audio/mix.wav"), tone, 48000)
            data = plan(duration=1.0)
            data["narration"] = True
            data["lines"][0]["speaker"] = "elder"
            data["lines"][0]["voice"] = "em_alex"
            report = narration.validate(tmp, data)
            self.assertFalse(report["ok"])
            self.assertTrue(any("character speaker" in p for p in report["problems"]))

    def test_short_stem_is_rejected_even_when_the_mp4_is_long(self):
        with tempfile.TemporaryDirectory() as tmp:
            short = 0.4 * np.sin(2 * np.pi * 220 * np.linspace(0, 0.3, 7200, endpoint=False))
            mix = 0.4 * np.sin(2 * np.pi * 220 * np.linspace(0, 1.0, 48000, endpoint=False))
            write(os.path.join(tmp, "generation/voice/take.wav"), short, 24000)
            write(os.path.join(tmp, "generation/voice/voice.wav"), short, 24000)
            write(os.path.join(tmp, "generation/audio/mix.wav"), mix, 48000)
            data = plan(duration=1.0)
            data["lines"][0]["audio_duration"] = 1.0
            data["project_seconds"] = 1.0
            report = narration.validate(tmp, data)
            self.assertFalse(report["ok"])
            self.assertTrue(any("cuts narration" in p for p in report["problems"]))

    def test_missing_take_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "generation/voice/voice.wav"), np.zeros(24000), 24000)
            write(os.path.join(tmp, "generation/audio/mix.wav"), np.zeros(48000), 48000)
            report = narration.validate(tmp, plan())
            self.assertFalse(report["ok"])
            self.assertTrue(any("no narration WAV" in p for p in report["problems"]))


if __name__ == "__main__":
    unittest.main()
