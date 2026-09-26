import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from voice.speak import SpeechSettings, clean_text, split_text, speak, list_voices
from assistant import responses


class TTSTests(unittest.TestCase):
    def setUp(self):
        self.module = MagicMock()
        self.engine = self.module.init.return_value
        self.engine.getProperty.return_value = [SimpleNamespace(id="voice-1", name="Alice", languages=["en"])]
        patcher = patch.dict("sys.modules", {"pyttsx3": self.module})
        patcher.start()
        self.addCleanup(patcher.stop)
        env = patch.dict("os.environ", {}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def test_settings_and_voice_selection(self):
        self.assertTrue(speak("Hello", settings=SpeechSettings(rate=190, volume=.5, voice="alice")))
        self.engine.setProperty.assert_any_call("rate", 190)
        self.engine.setProperty.assert_any_call("volume", .5)
        self.engine.setProperty.assert_any_call("voice", "voice-1")
        self.engine.stop.assert_called_once()
        self.assertEqual(self.engine.disconnect.call_count, 2)

    def test_environment_configuration(self):
        with patch.dict("os.environ", {"ASSISTANT_TTS_RATE": "180", "ASSISTANT_TTS_VOLUME": "0.2"}):
            self.assertTrue(speak("Hello"))
        self.engine.setProperty.assert_any_call("rate", 180)
        self.engine.setProperty.assert_any_call("volume", .2)

    def test_long_chunks_preserve_content(self):
        text = "First sentence. " + "word " * 200 + "X" * 500
        chunks = split_text(text, 180)
        self.assertTrue(all(0 < len(chunk) <= 180 for chunk in chunks))
        self.assertEqual("".join(chunks).replace(" ", ""), clean_text(text).replace(" ", ""))
        self.assertTrue(speak(text))
        self.assertEqual(self.engine.say.call_count, len(chunks))
        self.assertEqual(self.engine.runAndWait.call_count, len(chunks))

    def test_missing_dependency_prints_once(self):
        output = io.StringIO()
        with patch.dict("sys.modules", {"pyttsx3": None}), redirect_stdout(output):
            self.assertFalse(speak("Readable response"))
        self.assertEqual(output.getvalue().count("Assistant: Readable response"), 1)

    def test_disabled_and_bad_settings_do_not_initialize(self):
        for config in ({"ASSISTANT_TTS_ENABLED": "false"}, {"ASSISTANT_TTS_RATE": "bad"}, {"ASSISTANT_TTS_VOLUME": "nan"}):
            with patch.dict("os.environ", config):
                self.assertFalse(speak("Hello"))
        self.module.init.assert_not_called()

    def test_playback_failure_cleans_up_and_does_not_replay(self):
        self.engine.runAndWait.side_effect = RuntimeError("driver failed")
        self.assertFalse(speak("word " * 100))
        self.engine.say.assert_called_once()
        self.engine.stop.assert_called_once()

    def test_callback_error_is_detected(self):
        callbacks = {}
        self.engine.connect.side_effect = lambda topic, callback: callbacks.setdefault(topic, callback)
        self.engine.runAndWait.side_effect = lambda: callbacks["error"]("response-0", RuntimeError("driver callback"))
        self.assertFalse(speak("Hello"))
        self.engine.stop.assert_called_once()

    def test_interrupt_propagates_after_cleanup(self):
        self.engine.runAndWait.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            speak("Hello")
        self.engine.stop.assert_called_once()

    def test_unknown_voice_keeps_default(self):
        self.assertTrue(speak("Hello", settings=SpeechSettings(voice="missing")))
        self.assertFalse(any(call.args[0] == "voice" for call in self.engine.setProperty.call_args_list))

    def test_voice_listing_and_cleanup(self):
        self.assertEqual(list_voices()[0]["id"], "voice-1")
        self.engine.say.assert_not_called()
        self.engine.stop.assert_called_once()

    def test_empty_and_invalid_chunk_limit(self):
        self.assertFalse(speak(None))
        self.assertEqual(split_text("  "), [])
        self.module.init.assert_not_called()
        with self.assertRaises(ValueError):
            split_text("Hello", 0)

    def test_response_stage_retains_text_on_unexpected_failure(self):
        with patch.object(responses, "speak", side_effect=RuntimeError("unexpected")), redirect_stdout(io.StringIO()) as output:
            self.assertFalse(responses.safe_speak("Still visible"))
        self.assertIn("Assistant: Still visible", output.getvalue())


if __name__ == "__main__":
    unittest.main()
