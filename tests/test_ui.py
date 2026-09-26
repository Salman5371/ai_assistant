import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import numpy as np
from ui.audio import decode_upload, pcm_for_stt


def wav_bytes():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(np.full(16000, 3000, dtype="<i2").tobytes())
    return stream.getvalue()


class UploadTests(unittest.TestCase):
    def test_valid_upload_and_conversion(self):
        samples, rate = decode_upload(wav_bytes())
        self.assertEqual(rate, 16000)
        self.assertEqual(pcm_for_stt(samples).shape, (16000, 1))
        self.assertEqual(pcm_for_stt(samples).dtype, np.int16)

    def test_invalid_or_empty_upload(self):
        for raw in (b"", b"not a WAV", b"x" * (20 * 1024 * 1024 + 1)):
            with self.subTest(size=len(raw)), self.assertRaises((ValueError, wave.Error, EOFError)):
                decode_upload(raw)


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "optional Streamlit dependency")
class StreamlitTests(unittest.TestCase):
    def test_chat_and_memory_without_microphone(self):
        from streamlit.testing.v1 import AppTest
        from ai import memory
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"ASSISTANT_MEMORY_DB": str(Path(folder) / "test.sqlite3")}), patch.object(memory, "MEMORY_FILE", Path(folder) / "missing.txt"):
            app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "streamlit_app.py"), default_timeout=20).run()
            self.assertEqual(len(app.exception), 0)
            app.chat_input[0].set_value("remember UI memory test").run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(memory.read_memory(), "UI memory test")
            app.chat_input[0].set_value("show memory").run()
            self.assertTrue(any("UI memory test" in str(item.value) for item in app.markdown))

    def test_audio_upload_transcription_and_plots(self):
        from streamlit.testing.v1 import AppTest
        from ai import memory
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"ASSISTANT_MEMORY_DB": str(Path(folder) / "test.sqlite3")}), patch.object(memory, "MEMORY_FILE", Path(folder) / "missing.txt"), patch("streamlit.audio_input", return_value=io.BytesIO(wav_bytes())), patch("voice.stt.transcribe", return_value="what is the time") as transcribe:
            app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "streamlit_app.py"), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            next(button for button in app.button if button.label == "Transcribe").click().run()
            self.assertEqual(len(app.exception), 0)
            transcribe.assert_called_once()
            next(button for button in app.button if button.label == "Generate plots").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.session_state["audio_results"]["plots"]), 3)

    def test_audio_model_results_and_failure_message(self):
        from streamlit.testing.v1 import AppTest
        from ai import memory
        emotion = {"emotion": "neutral", "confidence": .6, "top_predictions": [{"emotion": "neutral", "confidence": .6}], "notice": "Experimental test fixture, not diagnosis"}
        event = {"category": "Speech", "confidence": .7, "top_predictions": [{"category": "Speech", "confidence": .7}]}
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"ASSISTANT_MEMORY_DB": str(Path(folder) / "test.sqlite3")}), patch.object(memory, "MEMORY_FILE", Path(folder) / "missing.txt"), patch("streamlit.audio_input", return_value=io.BytesIO(wav_bytes())), patch("audio_intelligence.emotion_recognition.PretrainedEmotionRecognizer.recognize", return_value=emotion), patch("audio_intelligence.audio_event_classifier.PretrainedAudioEventClassifier.classify", return_value=event) as classifier:
            app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "streamlit_app.py"), default_timeout=30).run()
            next(button for button in app.button if button.label == "Analyze emotion").click().run()
            next(button for button in app.button if button.label == "Classify sounds").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.metric), 2)
            classifier.side_effect = RuntimeError("Model unavailable")
            next(button for button in app.button if button.label == "Classify sounds").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("Model unavailable" in error.value for error in app.error))
            self.assertNotIn("events", app.session_state["audio_results"])
