import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import MagicMock, patch
from assistant.models import CommandUnavailableError
from assistant.pipeline import AssistantPipeline
from audio_intelligence.recorder import read_wav
from evaluation.latency import main


class AuditRegressionTests(unittest.TestCase):
    def test_invalid_evaluation_arguments_do_not_decode_or_load(self):
        with patch("sys.argv", ["latency", "events", "missing.wav", "--runs", "0"]), patch("audio_intelligence.recorder.read_wav") as read, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            read.assert_not_called()

    def test_expected_ui_restriction_is_visible(self):
        def resolve(name):
            raise CommandUnavailableError("Enable desktop automation in the sidebar first")
        response = AssistantPipeline(resolve=resolve).handle("open google")
        self.assertIn("Enable desktop automation", response.text)
        self.assertTrue(response.continue_running)

    def test_oversized_wav_header_is_rejected_before_read(self):
        wav = MagicMock()
        wav.getnchannels.return_value = 1
        wav.getsampwidth.return_value = 2
        wav.getframerate.return_value = 16000
        wav.getnframes.return_value = 100_000_000
        wav.getcomptype.return_value = "NONE"
        with patch("audio_intelligence.recorder.wave.open") as open_wave:
            open_wave.return_value.__enter__.return_value = wav
            with self.assertRaisesRegex(ValueError, "128 MiB"):
                read_wav("malformed.wav")
        wav.readframes.assert_not_called()
