import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import numpy as np
from voice import stt


class STTTests(unittest.TestCase):
    def setUp(self):
        self.audio = np.full((16000, 1), 3000, dtype=np.int16)
        self.env = patch.dict("os.environ", {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        stt._whisper_model.cache_clear()
        self.addCleanup(stt._whisper_model.cache_clear)

    def test_google_default_does_not_load_whisper(self):
        with patch.object(stt, "_transcribe_google", return_value="help") as google, patch.object(stt, "_transcribe_whisper") as whisper:
            self.assertEqual(stt.transcribe(self.audio), "help")
            google.assert_called_once()
            whisper.assert_not_called()

    def test_local_success_never_calls_google(self):
        with patch.object(stt, "_transcribe_google") as google, patch.object(stt, "_transcribe_whisper", return_value="open google"):
            self.assertEqual(stt.transcribe(self.audio, backend="whisper"), "open google")
            google.assert_not_called()

    def test_missing_whisper_falls_back_using_same_audio(self):
        with patch.dict("sys.modules", {"faster_whisper": None}), patch.object(stt, "_transcribe_google", return_value="help") as google:
            self.assertEqual(stt.transcribe(self.audio, backend="auto"), "help")
            self.assertIs(google.call_args.args[0], self.audio)

    def test_empty_whisper_falls_back(self):
        with patch.object(stt, "_transcribe_whisper", return_value=""), patch.object(stt, "_transcribe_google", return_value="help"):
            self.assertEqual(stt.transcribe(self.audio, backend="whisper"), "help")

    def test_local_only_failure_does_not_upload(self):
        with patch.object(stt, "_transcribe_whisper", side_effect=RuntimeError), patch.object(stt, "_transcribe_google") as google:
            self.assertEqual(stt.transcribe(self.audio, backend="whisper", google_fallback=False), "")
            google.assert_not_called()

    def test_generator_failure_falls_back(self):
        def broken():
            yield SimpleNamespace(text="partial")
            raise RuntimeError("inference failed")
        model = MagicMock()
        model.transcribe.return_value = (broken(), None)
        with patch.object(stt, "_whisper_model", return_value=model), patch.object(stt, "_transcribe_google", return_value="help"):
            self.assertEqual(stt.transcribe(self.audio, backend="whisper"), "help")

    def test_whisper_is_cached_and_uses_lightweight_cpu(self):
        module = MagicMock()
        module.WhisperModel.return_value.transcribe.side_effect = lambda *args, **kwargs: (iter([SimpleNamespace(text=" help ")]), None)
        with patch.dict("sys.modules", {"faster_whisper": module}):
            for _ in range(2):
                self.assertEqual(stt.transcribe(self.audio, backend="whisper"), "help")
        module.WhisperModel.assert_called_once()
        options = module.WhisperModel.call_args.kwargs
        self.assertEqual(options["device"], "cpu")
        self.assertEqual(options["compute_type"], "int8")
        self.assertEqual(module.WhisperModel.call_args.args[0], "tiny.en")

    def test_invalid_config_and_silence_never_upload(self):
        with patch.object(stt, "_transcribe_google") as google:
            self.assertEqual(stt.transcribe(self.audio, backend="unknown"), "")
            self.assertEqual(stt.transcribe(np.zeros_like(self.audio)), "")
            google.assert_not_called()

    def test_environment_and_explicit_override(self):
        with patch.dict("os.environ", {"ASSISTANT_STT_BACKEND": "whisper", "ASSISTANT_STT_GOOGLE_FALLBACK": "false"}), patch.object(stt, "_transcribe_whisper", side_effect=RuntimeError), patch.object(stt, "_transcribe_google", return_value="help") as google:
            self.assertEqual(stt.transcribe(self.audio), "")
            google.assert_not_called()
            self.assertEqual(stt.transcribe(self.audio, backend="google"), "help")

    def test_interrupt_propagates(self):
        with patch.object(stt, "_transcribe_whisper", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            stt.transcribe(self.audio, backend="whisper")


if __name__ == "__main__":
    unittest.main()
