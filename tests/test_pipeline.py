import unittest
from unittest.mock import MagicMock, patch
from assistant.models import Response
from assistant.pipeline import AssistantPipeline
from assistant.router import route
import main


class PipelineTests(unittest.TestCase):
    def test_sessions_do_not_share_confirmation(self):
        calls = MagicMock(return_value="scheduled")
        first = AssistantPipeline(resolve=lambda name: calls)
        second = AssistantPipeline(resolve=lambda name: calls)
        first.handle("shutdown computer")
        self.assertIsNone(second.session.pending_action)
        second.handle("confirm shutdown")
        calls.assert_not_called()
        self.assertEqual(first.handle("confirm shutdown").text, "scheduled")
        calls.assert_called_once_with()

    def test_failed_power_action_consumes_confirmation(self):
        action = MagicMock(side_effect=OSError("failure"))
        pipeline = AssistantPipeline(resolve=lambda name: action)
        pipeline.handle("shutdown computer")
        self.assertTrue(pipeline.handle("confirm shutdown").continue_running)
        self.assertIsNone(pipeline.session.pending_action)
        pipeline.handle("confirm shutdown")
        action.assert_called_once()

    def test_response_can_be_consumed_without_tts(self):
        pipeline = AssistantPipeline()
        response = pipeline.handle("help")
        self.assertIsInstance(response, Response)
        self.assertIn("classify audio", response.text)
        self.assertTrue(response.continue_running)

    def test_pre_action_and_final_response_order(self):
        events = []
        def service():
            events.append("camera")
            return "finished"
        pipeline = AssistantPipeline(emit=events.append, resolve=lambda name: service)
        self.assertTrue(pipeline.step("face detection"))
        self.assertEqual(events, ["Starting face detection. Press Q to stop.", "camera", "finished"])

    def test_route_preserves_feature_aliases(self):
        cases = {
            "start face detection": "start_face_detection",
            "age and gender detection": "start_age_gender_detection",
            "gesture assistant": "start_hand_tracking",
            "show vision logs": "read_vision_logs",
            "clear vision logs": "clear_vision_logs",
            "open document folder": "open_folder",
            "open chat g p t": "open_website",
            "what is the time": "time", "what day is today": "date",
            "remember Stop at 5:30!": "save_memory",
            "analyze my voice emotion": "analyze_voice_emotion",
            "classify microphone audio": "analyze_audio_events",
            "cancel shutdown": "cancel_shutdown",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(route(command).name, expected)
        self.assertEqual(route('classify wav "C:/My Audio/Test.wav"').payload, "C:/My Audio/Test.wav")

    def test_terminal_orchestration_exits(self):
        with patch.object(main, "safe_speak"), patch.object(main, "get_user_command", side_effect=["help", "stop"]), patch.object(main, "safe_process_command", side_effect=[True, False]) as handle:
            main.main()
            self.assertEqual([call.args[0] for call in handle.call_args_list], ["help", "stop"])

    def test_keyboard_interrupt_during_feature_exits_cleanly(self):
        with patch.object(main, "safe_speak") as output, patch.object(main, "get_user_command", return_value="face detection"), patch.object(main, "safe_process_command", side_effect=KeyboardInterrupt):
            main.main()
            self.assertEqual(output.call_args.args, ("Goodbye",))


if __name__ == "__main__":
    unittest.main()
