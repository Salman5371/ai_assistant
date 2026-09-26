"""Default terminal session and compatibility facade; UIs can own a Pipeline."""
import datetime
from .pipeline import AssistantPipeline
from .models import Session
from .normalization import normalize_command
from .responses import safe_speak
from .input import get_user_command as _get_user_command, listen
from .services import (
    search_google, search_youtube, save_memory, read_memory, clear_memory,
    save_note, read_notes, clear_notes, check_password_strength,
    get_wikipedia_summary, start_face_detection, start_age_gender_detection,
    start_hand_tracking, analyze_voice_emotion, analyze_audio_events,
    read_vision_logs, clear_vision_logs, open_folder, open_website, open_app,
    shutdown_computer, restart_computer, cancel_shutdown,
)

session = Session()
_pipeline = AssistantPipeline(session=session, emit=lambda text: safe_speak(text),
                              resolve=lambda name: globals()[name])


def get_user_command():
    return _get_user_command(listen_handler=listen)


def process_command(command):
    return _pipeline.step(command)


def safe_process_command(command):
    return process_command(command)


def get_greeting():
    """
    Return greeting based on current time.
    """
    current_hour = datetime.datetime.now().hour

    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 21:
        return "Good evening"
    else:
        return "Good night"
