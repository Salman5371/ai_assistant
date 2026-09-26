import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from assistant import runtime as main
from audio_intelligence.recorder import (
    check_microphone, record_until_silence, NoSpeechError,
    AudioQualityError, MicrophoneUnavailableError,
)


class RecordingTests(unittest.TestCase):
    def device(self, levels):
        sd = MagicMock()
        sd.PortAudioError = type("PortAudioError", (Exception,), {})
        sd.query_devices.return_value = {"max_input_channels": 1}
        stream = sd.InputStream.return_value.__enter__.return_value
        stream.read.side_effect = [(np.full((800, 1), level, dtype=np.int16), False) for level in levels]
        return sd, stream

    def test_microphone_absent(self):
        sd, _ = self.device([])
        sd.query_devices.return_value = {"max_input_channels": 0}
        with patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaises(MicrophoneUnavailableError):
            check_microphone()
        sd.InputStream.assert_not_called()

    def test_stops_on_silence_preserves_onset(self):
        sd, stream = self.device([0] * 6 + [0] * 2 + [3000] * 6 + [0] * 16)
        with patch.dict("sys.modules", {"sounddevice": sd}):
            samples = record_until_silence()
        self.assertLess(len(samples), 16000 * 5)
        self.assertEqual(np.count_nonzero(samples), 800 * 6)
        sd.InputStream.return_value.__exit__.assert_called_once()

    def test_silence_times_out(self):
        sd, _ = self.device([0] * 10)
        with patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaises(NoSpeechError):
            record_until_silence(start_timeout=.2)
        sd.InputStream.return_value.__exit__.assert_called_once()

    def test_noise_and_clipping(self):
        for level in (4000, 32767):
            sd, _ = self.device([level] * 6)
            with self.subTest(level=level), patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaises(AudioQualityError):
                record_until_silence()

    def test_continuous_signal_rejected_at_limit(self):
        sd, _ = self.device([0] * 6 + [3000] * 20)
        with patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaisesRegex(AudioQualityError, "limit"):
            record_until_silence(max_duration=1, silence_duration=.2)

    def test_overflow_and_empty_frames(self):
        for response in ((np.zeros((800, 1), dtype=np.int16), True), (np.empty((0, 1), dtype=np.int16), False)):
            sd, stream = self.device([])
            stream.read.side_effect = None
            stream.read.return_value = response
            with patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaises(AudioQualityError):
                record_until_silence()

    def test_interruption_closes_stream(self):
        sd, stream = self.device([])
        stream.read.side_effect = KeyboardInterrupt
        with patch.dict("sys.modules", {"sounddevice": sd}), self.assertRaises(KeyboardInterrupt):
            record_until_silence()
        sd.InputStream.return_value.__exit__.assert_called_once()


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.sr = MagicMock()
        self.sr.UnknownValueError = type("UnknownValueError", (Exception,), {})
        self.sr.RequestError = type("RequestError", (Exception,), {})
        spec = importlib.util.spec_from_file_location("voice_under_test", Path(__file__).resolve().parent.parent / "voice/listen.py")
        self.module = importlib.util.module_from_spec(spec)
        patcher = patch.dict("sys.modules", {"speech_recognition": self.sr})
        patcher.start()
        self.addCleanup(patcher.stop)
        environment = patch.dict("os.environ", {"ASSISTANT_STT_BACKEND": "google"})
        environment.start()
        self.addCleanup(environment.stop)
        spec.loader.exec_module(self.module)

    def test_empty_or_silent_audio_never_uploaded(self):
        for samples in (np.empty((0, 1), dtype=np.int16), np.zeros((800, 1), dtype=np.int16)):
            with patch.object(self.module, "record_until_silence", return_value=samples):
                self.assertEqual(self.module.listen(), "")
        self.sr.Recognizer.return_value.recognize_google.assert_not_called()

    def test_recognition_failures_and_success(self):
        recognizer = self.sr.Recognizer.return_value
        with patch.object(self.module, "record_until_silence", return_value=np.full((800, 1), 3000, dtype=np.int16)):
            for error in (self.sr.UnknownValueError(), self.sr.RequestError(), TimeoutError()):
                recognizer.recognize_google.side_effect = error
                self.assertEqual(self.module.listen(), "")
            recognizer.recognize_google.side_effect = None
            recognizer.recognize_google.return_value = "  open google  "
            self.assertEqual(self.module.listen(), "open google")
            self.assertEqual(recognizer.operation_timeout, 10)

    def test_text_mode_does_not_touch_microphone(self):
        with patch("builtins.input", return_value="help"), patch.object(main, "listen") as listen:
            self.assertEqual(main.get_user_command(), "help")
            listen.assert_not_called()

    def test_failed_voice_prompts_for_text(self):
        with patch("builtins.input", side_effect=["", "help"]), patch.object(main, "listen", return_value=""):
            self.assertEqual(main.get_user_command(), "help")


if __name__ == "__main__":
    unittest.main()
