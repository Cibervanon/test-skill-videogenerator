"""The delivered audio must contain the narration, not just the score."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from acs import mixdown, narration, qa  # noqa: E402


def tone(freq: float, seconds: float, sr: int, amp: float = 0.3) -> np.ndarray:
    return amp * np.sin(2 * np.pi * freq * np.arange(int(seconds * sr)) / sr)


def write_wav(path: str, data: np.ndarray, sr: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())


def pcm(path: str, sr: int = 24000) -> np.ndarray:
    import subprocess

    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    )
    return np.frombuffer(proc.stdout, dtype="<f4").astype(np.float64)


class VoicePresenceTests(unittest.TestCase):
    def _signals(self, with_voice: bool):
        sr = 24000
        t = np.arange(sr * 2) / sr
        bed = 0.4 * np.sin(2 * np.pi * 220 * t)
        voice = 0.2 * np.sin(2 * np.pi * 660 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
        delivered = bed + (voice if with_voice else 0.0)
        return delivered, voice, bed

    def test_detects_a_voice_over_a_bed(self):
        delivered, voice, bed = self._signals(True)
        fit = qa.voice_fit(delivered, voice, bed)
        self.assertTrue(fit["ok"], fit)
        self.assertGreater(fit["correlation"], 0.9)
        self.assertGreater(fit["voice_gain"], 0.05)

    def test_rejects_a_score_only_delivery(self):
        delivered, voice, bed = self._signals(False)
        fit = qa.voice_fit(delivered, voice, bed)
        self.assertFalse(fit["ok"], fit)
        self.assertLess(abs(fit["correlation"]), 0.1)

    def test_voice_without_a_known_bed_still_measures_presence(self):
        delivered, voice, _ = self._signals(True)
        fit = qa.voice_fit(delivered, voice, None)
        self.assertTrue(fit["ok"], fit)


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for the mixdown graph")
class MixdownGraphTests(unittest.TestCase):
    def test_mix_contains_both_the_score_and_the_voice(self):
        from acs.ffmpeg import Tools

        sr = 48000
        with tempfile.TemporaryDirectory() as tmp:
            score = os.path.join(tmp, "score.wav")
            voice = os.path.join(tmp, "voice.wav")
            out = os.path.join(tmp, "mix.wav")
            write_wav(score, tone(440, 1.0, sr), sr)
            write_wav(voice, tone(880, 1.0, sr), sr)
            mixdown.duck(Tools.detect(), score=score, voice=voice, out=out, music_gain=0.45, voice_gain=1.0)

            mixed = pcm(out, sr)
            spectrum = np.abs(np.fft.rfft(mixed))
            freqs = np.fft.rfftfreq(len(mixed), 1 / sr)

            def energy(freq: float) -> float:
                index = int(freq / (sr / len(mixed)))
                return float(spectrum[max(0, index - 3) : index + 4].max())

            score_energy = energy(440)
            voice_energy = energy(880)
            self.assertGreater(score_energy, 100)
            # The old graph produced a voice/score ratio of 0.001.
            self.assertGreater(voice_energy / score_energy, 0.2)
            self.assertLessEqual(float(np.abs(mixed).max()), 0.95)


class NarrationMixVoiceTests(unittest.TestCase):
    def test_voicecheck_rejects_a_score_only_mix(self):
        sr = 24000
        with tempfile.TemporaryDirectory() as tmp:
            voice = tone(660, 0.4, sr)
            write_wav(os.path.join(tmp, "generation/voice/take.wav"), voice, sr)
            write_wav(os.path.join(tmp, "generation/voice/voice.wav"), np.concatenate([voice, np.zeros(sr // 2)]), sr)
            write_wav(os.path.join(tmp, "generation/audio/mix.wav"), tone(220, 1.0, 48000, amp=0.3), 48000)
            plan = {
                "narration": True,
                "stem": "generation/voice/voice.wav",
                "project_seconds": 1.0,
                "lines": [
                    {
                        "shot": "S01",
                        "speaker": "narrator",
                        "voice": "ef_dora",
                        "text": "una linea",
                        "start": 0.0,
                        "end": 1.0,
                        "audio": "generation/voice/take.wav",
                        "audio_duration": 0.4,
                        "words": [{"w": "una", "s": 0.0, "e": 0.2}],
                    }
                ],
            }
            report = narration.validate(tmp, plan)
            self.assertFalse(report["ok"])
            self.assertTrue(any("does not contain the narration stem" in p for p in report["problems"]))
            self.assertLess(abs(report["mix_voice_correlation"]), 0.1)


class SoundtrackSelectionTests(unittest.TestCase):
    def test_mix_is_preferred_over_the_score(self):
        import studio

        with tempfile.TemporaryDirectory() as tmp:
            score = os.path.join(tmp, "generation", "audio", "score.wav")
            mix = os.path.join(tmp, "generation", "audio", "mix.wav")
            os.makedirs(os.path.dirname(score), exist_ok=True)
            open(score, "wb").close()
            self.assertEqual(studio.default_soundtrack(tmp, score), score)
            open(mix, "wb").close()
            self.assertEqual(studio.default_soundtrack(tmp, score), mix)


class ManifestLockTests(unittest.TestCase):
    def test_a_second_render_fails_fast_instead_of_swapping_the_manifest(self):
        import studio

        with tempfile.TemporaryDirectory() as tmp:
            active = os.path.join(tmp, "project.json")
            requested = os.path.join(tmp, "requested.json")
            with open(active, "w", encoding="utf-8") as fh:
                json.dump({"id": "previous"}, fh)
            with open(requested, "w", encoding="utf-8") as fh:
                json.dump({"id": "requested"}, fh)

            original = studio.PROJECT_MANIFEST
            studio.PROJECT_MANIFEST = active
            try:
                with studio.manifest_lock(timeout=1.0):
                    with self.assertRaises(studio.ManifestBusy):
                        with studio.use_manifest(requested, lock_timeout=0.1):
                            pass
                with open(active, "r", encoding="utf-8") as fh:
                    self.assertEqual(json.load(fh)["id"], "previous")
            finally:
                studio.PROJECT_MANIFEST = original


if __name__ == "__main__":
    unittest.main()
