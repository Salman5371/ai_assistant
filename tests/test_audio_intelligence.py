import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
from audio_intelligence.preprocessing import to_mono, resample, normalize, trim_silence, preprocess
from audio_intelligence.recorder import read_wav, write_wav, temporary_wav, record_audio
from audio_intelligence.emotion_recognition import EmotionRecognizer
from audio_intelligence.audio_event_classifier import AudioEventClassifier


class AudioTests(unittest.TestCase):
    def test_mono_pcm_scaling_and_no_mutation(self):
        data = np.array([[32767, -32768], [16384, 16384]], dtype=np.int16)
        original = data.copy()
        np.testing.assert_allclose(to_mono(data), [-1 / 65536, .5])
        np.testing.assert_array_equal(data, original)

    def test_normalize_and_silence(self):
        np.testing.assert_allclose(normalize(np.array([-.2, .1])), [-.95, .475])
        np.testing.assert_array_equal(normalize(np.zeros(10)), np.zeros(10))
        self.assertEqual(len(trim_silence(np.zeros(10))), 0)
        np.testing.assert_allclose(trim_silence(np.array([0., .5, 0, -.5, 0])), [.5, 0, -.5])

    def test_resample_duration_and_alias_rejection(self):
        time = np.arange(4800) / 48000
        low = resample(np.sin(2 * np.pi * 1000 * time), 48000, 16000)
        high = resample(np.sin(2 * np.pi * 12000 * time), 48000, 16000)
        self.assertEqual(len(low), 1600)
        self.assertGreater(np.std(low[100:-100]), .65)
        self.assertLess(np.std(high[100:-100]), .02)
        self.assertEqual(resample(np.zeros((10, 2)), 8000, 16000).shape, (20, 2))

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(resample(np.array([], dtype=float), 8000, 16000).shape, (0,))
        for value in (np.array([np.nan]), np.zeros((2, 0)), np.zeros((2, 2, 2))):
            with self.assertRaises(ValueError):
                to_mono(value)
        with self.assertRaises(ValueError):
            resample(np.zeros(2), 0, 16000)

    def test_wav_roundtrip_and_refuse_overwrite(self):
        audio = np.array([[-1., .5], [0, .999]], dtype=np.float32)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.wav"
            write_wav(path, audio, 16000)
            actual, rate = read_wav(path)
            self.assertEqual(rate, 16000)
            np.testing.assert_allclose(actual, audio, atol=1 / 32768)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_wav(path, np.zeros(5), 8000)
            self.assertEqual(path.read_bytes(), before)

    def test_temporary_cleanup_after_exception(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                with temporary_wav(np.zeros(5), 16000, directory=folder) as path:
                    self.assertTrue(path.exists())
                    read_wav(path)
                    raise RuntimeError("test failure")
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_recording_stops_after_failure(self):
        sd = MagicMock()
        sd.wait.side_effect = RuntimeError("device failed")
        with patch.dict("sys.modules", {"sounddevice": sd}):
            with self.assertRaises(RuntimeError):
                record_audio()
        sd.stop.assert_called_once()

    def test_recording_parameters(self):
        sd = MagicMock()
        sd.rec.return_value = np.zeros((800, 1), dtype=np.int16)
        with patch.dict("sys.modules", {"sounddevice": sd}):
            self.assertEqual(record_audio(.1, 8000).shape, (800, 1))
        sd.rec.assert_called_once_with(800, samplerate=8000, channels=1, dtype="int16", device=None)
        sd.stop.assert_called_once()

    def test_model_adapters(self):
        for instance, method in ((EmotionRecognizer(), "recognize"), (AudioEventClassifier(), "classify")):
            with self.assertRaisesRegex(RuntimeError, "No .* model configured"):
                getattr(instance, method)(np.ones(10), 16000)
            instance.backend = MagicMock(return_value={"label": "test"})
            self.assertEqual(getattr(instance, method)(np.ones((10, 2)), 16000), {"label": "test"})
            samples, rate = instance.backend.call_args.args
            self.assertEqual(samples.shape, (10,))
            self.assertEqual(rate, 16000)
            with self.assertRaisesRegex(ValueError, "non-silent"):
                getattr(instance, method)(np.zeros(10), 16000)

    def test_waveform_on_provided_axes(self):
        from audio_intelligence.visualization import plot_waveform
        ax = MagicMock()
        self.assertIs(plot_waveform(np.zeros(10), 10, ax=ax), ax)
        np.testing.assert_allclose(ax.plot.call_args.args[0], np.arange(10) / 10)


if __name__ == "__main__":
    unittest.main()
