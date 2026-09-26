import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
from assistant import runtime as main
from audio_intelligence.audio_event_classifier import PretrainedAudioEventClassifier, format_event_result
from audio_intelligence.recorder import write_wav


class EventTests(unittest.TestCase):
    def configured(self):
        classifier = PretrainedAudioEventClassifier()
        classifier._model = MagicMock()
        classifier._model.config.id2label = dict(enumerate(["Speech", "Dog", "Music", "Knock", "Rain"]))
        classifier._extractor = MagicMock(return_value={"input_values": "tensor"})
        classifier._torch = MagicMock()
        classifier._torch.sigmoid.return_value.__getitem__.return_value.cpu.return_value.tolist.return_value = [.2, .8, .1, .3, .05]
        return classifier

    def test_ranked_output(self):
        classifier = self.configured()
        result = classifier.classify(np.ones((8000, 2)) * .1, 8000, top_k=3)
        self.assertEqual(result["category"], "Dog")
        self.assertEqual(result["confidence"], .8)
        self.assertEqual(len(result["top_predictions"]), 3)
        self.assertIn("80.0%", format_event_result(result))
        self.assertEqual(classifier._extractor.call_args.args[0].shape, (16000,))

    def test_later_windows_are_included(self):
        classifier = self.configured()
        classifier._torch.sigmoid.return_value.__getitem__.return_value.cpu.return_value.tolist.side_effect = [[.2, .8, .1, .3, .05], [.9, .1, .1, .2, .05]]
        result = classifier.classify(np.ones(16000 * 11) * .1, 16000)
        self.assertEqual(result["category"], "Speech")
        self.assertEqual(result["windows"], 2)
        self.assertEqual(result["top_predictions"][1]["confidence"], .8)

    def test_wav_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Test Audio.wav"
            write_wav(path, np.ones(8000) * .1, 8000)
            self.assertEqual(self.configured().classify_wav(path)["category"], "Dog")

    def test_invalid_audio_and_k_do_not_load(self):
        classifier = PretrainedAudioEventClassifier()
        with patch.object(classifier, "load") as load:
            for samples in (np.zeros(16000), np.ones(10), np.ones(16000 * 61)):
                with self.assertRaises(ValueError):
                    classifier.classify(samples, 16000)
            with self.assertRaises(ValueError):
                classifier.classify(np.ones(16000), 16000, top_k=2)
            load.assert_not_called()

    def test_microphone_uses_event_capture(self):
        classifier = self.configured()
        with patch("audio_intelligence.recorder.check_microphone") as check, patch("audio_intelligence.recorder.record_audio", return_value=np.ones((16000, 1)) * .1) as record:
            classifier.classify_microphone(duration=8, device=2)
            check.assert_called_once_with(16000, device=2)
            record.assert_called_once_with(8, 16000, channels=1, device=2)

    def test_loading_is_optional_safe_and_cached(self):
        torch, transformers = MagicMock(), MagicMock()
        with patch.dict("sys.modules", {"torch": torch, "transformers": transformers}):
            classifier = PretrainedAudioEventClassifier(local_files_only=True)
            classifier.load()
            classifier.load()
        loader = transformers.ASTForAudioClassification.from_pretrained
        loader.assert_called_once()
        self.assertTrue(loader.call_args.kwargs["use_safetensors"])
        self.assertFalse(loader.call_args.kwargs["trust_remote_code"])
        self.assertTrue(loader.call_args.kwargs["local_files_only"])

    def test_missing_dependencies(self):
        with patch.dict("sys.modules", {"torch": None}), self.assertRaisesRegex(RuntimeError, "requirements-audio-events"):
            PretrainedAudioEventClassifier().load()

    def test_commands_preserve_path_and_recover(self):
        main.session.pending_action = None
        with patch.object(main, "safe_speak") as speak, patch.object(main, "analyze_audio_events", return_value="result") as analyze:
            self.assertTrue(main.process_command('classify wav "C:/Audio Samples/Test-01.wav"'))
            analyze.assert_called_once_with("C:/Audio Samples/Test-01.wav")
            analyze.reset_mock()
            main.process_command("classify audio")
            analyze.assert_called_once_with(None)
            analyze.side_effect = OSError("missing file")
            self.assertTrue(main.process_command("classify wav missing.wav"))
            self.assertIn("continue typing", speak.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
