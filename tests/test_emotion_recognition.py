import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from assistant import runtime as main
from audio_intelligence.emotion_recognition import (
    PretrainedEmotionRecognizer, format_emotion_result, NOTICE,
)


class EmotionTests(unittest.TestCase):
    def configured(self):
        recognizer = PretrainedEmotionRecognizer()
        recognizer._model = MagicMock()
        recognizer._model.config.id2label = {0: "neu", 1: "hap", 2: "ang", 3: "sad"}
        recognizer._extractor = MagicMock(return_value={"input_values": "tensor"})
        recognizer._torch = MagicMock()
        recognizer._torch.softmax.return_value.__getitem__.return_value.cpu.return_value.tolist.return_value = [.15, .6, .2, .05]
        return recognizer

    def test_scores_labels_top_predictions_and_notice(self):
        recognizer = self.configured()
        result = recognizer.recognize(np.ones((8000, 2), dtype=np.float32) * .1, 8000)
        self.assertEqual(result["emotion"], "happy")
        self.assertEqual(result["confidence"], .6)
        self.assertEqual([p["emotion"] for p in result["top_predictions"]], ["happy", "angry", "neutral"])
        self.assertTrue(result["experimental"])
        self.assertIn(NOTICE, format_emotion_result(result))
        self.assertIn("60.0%", format_emotion_result(result))
        self.assertEqual(recognizer._extractor.call_args.args[0].shape, (16000,))
        self.assertEqual(recognizer._extractor.call_args.kwargs["sampling_rate"], 16000)

    def test_invalid_audio_does_not_load_model(self):
        recognizer = PretrainedEmotionRecognizer()
        with patch.object(recognizer, "load") as load:
            for audio in (np.zeros(16000), np.ones(100), np.ones(16000 * 31)):
                with self.assertRaises(ValueError):
                    recognizer.recognize(audio, 16000)
            load.assert_not_called()

    def test_missing_runtime_has_install_instruction(self):
        with patch.dict("sys.modules", {"torch": None}):
            with self.assertRaisesRegex(RuntimeError, "requirements-emotion.txt"):
                PretrainedEmotionRecognizer().load()

    def test_load_is_lazy_cached_and_disables_remote_code(self):
        torch, transformers = MagicMock(), MagicMock()
        with patch.dict("sys.modules", {"torch": torch, "transformers": transformers}):
            recognizer = PretrainedEmotionRecognizer(local_files_only=True)
            transformers.Wav2Vec2ForSequenceClassification.from_pretrained.assert_not_called()
            recognizer.load()
            recognizer.load()
        loader = transformers.Wav2Vec2ForSequenceClassification.from_pretrained
        loader.assert_called_once()
        self.assertFalse(loader.call_args.kwargs["trust_remote_code"])
        self.assertTrue(loader.call_args.kwargs["local_files_only"])
        loader.return_value.eval.assert_called_once()

    def test_model_load_failure_is_actionable(self):
        transformers = MagicMock()
        transformers.Wav2Vec2FeatureExtractor.from_pretrained.side_effect = OSError("offline")
        with patch.dict("sys.modules", {"torch": MagicMock(), "transformers": transformers}):
            with self.assertRaisesRegex(RuntimeError, "first download"):
                PretrainedEmotionRecognizer().load()

    def test_command_success_and_failure_preserve_loop(self):
        main.session.pending_action = None
        with patch.object(main, "safe_speak") as speak, patch.object(main, "analyze_voice_emotion", return_value="result") as analyze:
            self.assertTrue(main.process_command("analyze my voice emotion"))
            analyze.assert_called_once()
            self.assertIn("experimental", speak.call_args_list[0].args[0])
            analyze.side_effect = RuntimeError("microphone missing")
            self.assertTrue(main.process_command("analyze my voice emotion"))
            self.assertIn("continue typing", speak.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
