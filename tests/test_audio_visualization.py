import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from audio_intelligence.visualization import (spectrogram_data, mel_spectrogram_data,
    power_to_db, save_plot, generate_audio_plots, generate_wav_plots)
from audio_intelligence.recorder import write_wav


class SpectralTests(unittest.TestCase):
    def test_tone_frequency_and_mel_shape(self):
        rate = 16000
        audio = np.sin(2 * np.pi * 1000 * np.arange(rate) / rate)
        times, frequencies, power = spectrogram_data(audio, rate)
        self.assertAlmostEqual(frequencies[np.argmax(power[:, 10])], 1000, delta=16)
        mtimes, centers, mel = mel_spectrogram_data(audio, rate)
        self.assertEqual(mel.shape, (64, len(times)))
        self.assertTrue(np.all(np.diff(centers) > 0))
        self.assertTrue(np.isfinite(power_to_db(mel)).all())

    def test_short_and_silent(self):
        for length in (1, 16000):
            _, _, power = spectrogram_data(np.zeros(length), 16000)
            np.testing.assert_array_equal(power_to_db(power), np.full(power.shape, -80))

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            spectrogram_data(np.array([]), 16000)
        with self.assertRaises(ValueError):
            spectrogram_data(np.zeros(10), 16000, hop_length=0)
        with self.assertRaises(ValueError):
            mel_spectrogram_data(np.zeros(10), 16000, fmax=9000)
        with self.assertRaises(ValueError):
            save_plot(MagicMock(), ".", name="../escape")

    def test_save_failure_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as folder:
            ax = MagicMock()
            ax.figure.savefig.side_effect = OSError("disk full")
            with self.assertRaises(OSError):
                save_plot(ax, folder)
            self.assertEqual(list(Path(folder).iterdir()), [])


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "optional plotting dependency")
class RenderTests(unittest.TestCase):
    def test_pngs_unique_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.wav"
            write_wav(path, np.sin(2 * np.pi * 500 * np.arange(8000) / 8000), 8000)
            original = path.read_bytes()
            first = generate_wav_plots(path, folder)
            second = generate_wav_plots(path, folder)
            self.assertTrue(set(first.values()).isdisjoint(second.values()))
            for image in list(first.values()) + list(second.values()):
                self.assertTrue(image.is_absolute())
                self.assertTrue(image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(path.read_bytes(), original)

    def test_batch_failure_rolls_back_only_new_files(self):
        with tempfile.TemporaryDirectory() as folder:
            existing = Path(folder) / "keep.txt"
            existing.write_text("keep")
            with patch("audio_intelligence.visualization.plot_mel_spectrogram", side_effect=ValueError("test")):
                with self.assertRaises(ValueError):
                    generate_audio_plots(np.ones(1600), 16000, folder)
            self.assertEqual(list(Path(folder).iterdir()), [existing])


if __name__ == "__main__":
    unittest.main()
