import importlib.util
import sys
from pathlib import Path
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from assistant import runtime as main
from automation import app_control, system_control


class CommandTests(unittest.TestCase):
    def setUp(self):
        main.session.pending_action = None
        self.speech = patch.object(main, "safe_speak").start()
        self.addCleanup(patch.stopall)

    def test_payloads_preserved_and_not_treated_as_commands(self):
        cases = [
            ("take note Stop buying milk at 5:30!", "save_note", "Stop buying milk at 5:30!"),
            ("remember Alice uses C++", "save_memory", "Alice uses C++"),
            ("search time management", "search_google", "time management"),
            ("you tube search C++", "search_youtube", "C++"),
        ]
        for command, handler, payload in cases:
            with self.subTest(command=command), patch.object(main, handler) as mock:
                mock.return_value = None
                self.assertTrue(main.process_command(command))
                mock.assert_called_once_with(payload)

    def test_all_password_aliases_preserve_payload(self):
        for prefix in ("check password", "check password strength", "password strength"):
            with patch.object(main, "check_password_strength", return_value="checked") as checker:
                main.process_command(prefix + " Hello@123")
                checker.assert_called_once_with("Hello@123")

    def test_confirmation_rejects_negation_and_wrong_action(self):
        main.session.pending_action = "shutdown"
        with patch.object(main, "shutdown_computer") as shutdown:
            for command in ("do not confirm", "yesterday", "confirm restart"):
                main.process_command(command)
                shutdown.assert_not_called()
            main.process_command("confirm shutdown")
            shutdown.assert_called_once()
            self.assertIsNone(main.session.pending_action)

    def test_negated_shutdown_does_not_schedule(self):
        main.process_command("do not shutdown computer")
        self.assertIsNone(main.session.pending_action)

    def test_voice_empty_falls_back_to_text(self):
        with patch("builtins.input", side_effect=["", "help"]), patch.object(main, "listen", return_value=""):
            self.assertEqual(main.get_user_command(), "help")

    def test_eof_exits(self):
        with patch("builtins.input", side_effect=EOFError):
            self.assertEqual(main.get_user_command(), "stop")

    def test_optional_import_error_does_not_end_loop(self):
        with patch.object(main, "start_face_detection", side_effect=ImportError("missing cv2")):
            self.assertTrue(main.safe_process_command("face detection"))

    def test_wikipedia_is_not_hijacked_by_website_name(self):
        with patch.object(main, "get_wikipedia_summary", return_value="summary") as lookup:
            main.process_command("what is Google")
            lookup.assert_called_once_with("Google")


class AutomationTests(unittest.TestCase):
    def test_browser_failure_is_reported(self):
        with patch.object(app_control.webbrowser, "open", return_value=False):
            with self.assertRaises(RuntimeError):
                app_control.open_website("https://example.com")

    def test_unknown_windows_app_fails(self):
        with patch.object(app_control.platform, "system", return_value="Windows"), patch.object(app_control.subprocess, "Popen") as spawn:
            self.assertFalse(app_control.open_app("unknown"))
            spawn.assert_not_called()

    def test_failed_shutdown_is_not_reported_as_success(self):
        with patch.object(system_control.platform, "system", return_value="Windows"), patch.object(system_control.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "shutdown")):
            self.assertIn("Could not shutdown", system_control.shutdown_computer())


class CameraCleanupTests(unittest.TestCase):
    def test_camera_released_on_capture_error(self):
        root = Path(__file__).resolve().parent.parent
        for filename, entrypoint in (
            ("face_detection", "start_face_detection"),
            ("age_gender_detection", "start_age_gender_detection"),
            ("hand_tracking", "start_hand_tracking"),
        ):
            with self.subTest(feature=filename):
                cv2 = MagicMock()
                cv2.CascadeClassifier.return_value.empty.return_value = False
                camera = cv2.VideoCapture.return_value
                camera.read.side_effect = RuntimeError("capture failed")
                modules = {name: MagicMock() for name in (
                    "mediapipe", "mediapipe.tasks", "mediapipe.tasks.python",
                    "mediapipe.tasks.python.vision",
                )}
                modules["cv2"] = cv2
                spec = importlib.util.spec_from_file_location("camera_under_test", root / "vision" / (filename + ".py"))
                module = importlib.util.module_from_spec(spec)
                with patch.dict(sys.modules, modules):
                    spec.loader.exec_module(module)
                module.log_vision_event = MagicMock()
                module.check_model_files = lambda: (True, [])
                module.HAND_MODEL = MagicMock()
                module.HAND_MODEL.stat.return_value.st_size = 2000000
                with self.assertRaisesRegex(RuntimeError, "capture failed"):
                    getattr(module, entrypoint)()
                camera.release.assert_called_once()
                cv2.destroyAllWindows.assert_called_once()

    def test_startup_without_optional_libraries(self):
        root = Path(__file__).resolve().parent.parent
        script = (
            "import sys; "
            "sys.modules.update({name: None for name in "
            "('cv2', 'mediapipe', 'speech_recognition', 'sounddevice', 'pyttsx3', 'wikipedia')}); "
            "import main; assert main.normalize_command('Chat GPT') == 'chatgpt'"
        )
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
