"""Feature adapter boundary; no recording or model loading at import time."""
from automation.app_control import (
    open_website,
    open_app,
    search_google,
    search_youtube,
)

from automation.system_control import (
    open_folder,
    shutdown_computer,
    restart_computer,
    cancel_shutdown,
)

from ai.memory import save_memory, read_memory, clear_memory
from ai.notes import save_note, read_notes, clear_notes

from cyber.password_checker import check_password_strength

from vision.vision_logger import read_vision_logs, clear_vision_logs



def get_wikipedia_summary(*args, **kwargs):
    from ai.wikipedia_search import get_wikipedia_summary as handler
    return handler(*args, **kwargs)


def start_face_detection(*args, **kwargs):
    from vision.face_detection import start_face_detection as handler
    return handler(*args, **kwargs)


def start_age_gender_detection(*args, **kwargs):
    from vision.age_gender_detection import start_age_gender_detection as handler
    return handler(*args, **kwargs)


def start_hand_tracking(*args, **kwargs):
    from vision.hand_tracking import start_hand_tracking as handler
    return handler(*args, **kwargs)


def analyze_voice_emotion():
    from audio_intelligence.emotion_recognition import analyze_voice_emotion as handler
    from audio_intelligence.emotion_recognition import format_emotion_result
    return format_emotion_result(handler())


def analyze_audio_events(path=None):
    from audio_intelligence.audio_event_classifier import analyze_audio_events as handler
    from audio_intelligence.audio_event_classifier import format_event_result
    return format_event_result(handler(path))
