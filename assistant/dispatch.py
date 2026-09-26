"""Intent -> feature service -> Response. Only this stage executes commands."""
import datetime
from . import services
from .help import HELP_TEXT
from .models import Response
from .router import WEBSITES


PROMPTS = {
    "search_youtube": "What should I search on YouTube?", "search_google": "What should I search for?",
    "save_memory": "What should I remember?", "save_note": "What note should I save?",
    "check_password_strength": "Please type a demo password after check password.",
}
VISION_PROMPTS = {
    "start_face_detection": "Starting face detection. Press Q to stop.",
    "start_age_gender_detection": "Starting age and gender detection. Press Q to stop.",
    "start_hand_tracking": "Starting gesture controlled assistant. Press Q to stop.",
}


def dispatch(intent, session, emit=lambda text: None, resolve=None):
    """Return the final response; emit provides pre-action notices to any UI sink."""
    resolve = resolve or (lambda name: getattr(services, name))
    name, payload = intent.name, intent.payload
    if name == "empty":
        return Response()
    if name == "stop":
        session.pending_action = None
        return Response("Goodbye", False)
    if name == "confirm":
        # Consume confirmation before side effects, even if the service fails.
        action = session.pending_action
        session.pending_action = None
        if action not in {"shutdown", "restart"} or payload != action:
            return Response("No matching action is pending.")
        return Response(resolve(action + "_computer")())
    if name == "cancel_pending":
        session.pending_action = None
        return Response("Action cancelled.")
    if name == "await_confirmation":
        return Response("Please say confirm or cancel.")
    if name == "request_power":
        session.pending_action = payload
        return Response(f"Are you sure? Say or type confirm {payload} to continue or cancel to stop.")
    if name in {"analyze_voice_emotion", "analyze_audio_events"}:
        if name == "analyze_voice_emotion":
            emit("This is experimental AI inference, not a psychological or medical diagnosis.")
        try:
            result = resolve(name)() if name == "analyze_voice_emotion" else resolve(name)(payload)
            return Response(result)
        except Exception as error:
            feature = "Voice emotion analysis" if name == "analyze_voice_emotion" else "Audio classification"
            return Response(f"{feature} unavailable: {error}. You can continue typing commands.")
    if name == "missing_wav":
        return Response("Provide a WAV path after classify wav.")
    if name in PROMPTS:
        return Response(resolve(name)(payload) or "") if payload else Response(PROMPTS[name])
    if name == "help":
        return Response(HELP_TEXT)
    if name == "time":
        return Response("The time is " + datetime.datetime.now().strftime("%I:%M %p"))
    if name == "date":
        return Response("Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y"))
    if name in VISION_PROMPTS:
        emit(VISION_PROMPTS[name])
        return Response(resolve(name)())
    if name == "open_folder":
        return Response(resolve(name)(payload))
    if name == "open_website":
        resolve(name)(WEBSITES[payload])
        return Response(f"Opening {payload}")
    if name == "open_app":
        opened = resolve(name)(payload)
        return Response(f"Opening {payload}" if opened else f"Could not open {payload}.")
    if name == "wikipedia":
        emit(f"Searching Wikipedia for {payload}")
        return Response(resolve("get_wikipedia_summary")(payload))
    if name == "missing_wikipedia":
        return Response("Who should I search for?" if payload == "who is" else "What should I search for?")
    if name in {"read_memory", "clear_memory", "read_notes", "clear_notes",
                "read_vision_logs", "clear_vision_logs", "cancel_shutdown"}:
        return Response(resolve(name)())
    return Response("This command is not available yet.")
