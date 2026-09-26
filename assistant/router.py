"""Pure command routing: no feature execution, recording, file I/O or TTS."""
import re
from .models import Intent
from .normalization import normalize_command


WEBSITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com",
    "github": "https://github.com", "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com", "facebook": "https://www.facebook.com",
    "stackoverflow": "https://stackoverflow.com",
}


def route(raw_command, pending_action=None):
    raw = str(raw_command or "").strip()
    command = normalize_command(raw)
    if not command:
        return Intent("empty")
    if command in {"stop", "exit", "quit"}:
        return Intent("stop")
    if pending_action:
        if command in {"confirm", "yes", f"confirm {pending_action}"}:
            return Intent("confirm", pending_action)
        if command in {"cancel", "no", "cancel shutdown", "cancel restart"}:
            return Intent("cancel_pending")
        return Intent("await_confirmation")
    if command in {"analyze my voice emotion", "analyse my voice emotion", "voice emotion"}:
        return Intent("analyze_voice_emotion")
    match = re.fullmatch(r"(?:classify|analyze)\s+wav(?:\s+(.+))?", raw, re.IGNORECASE)
    if match:
        path = (match.group(1) or "").strip()
        if len(path) >= 2 and path[0] == path[-1] and path[0] in {"'", '"'}:
            path = path[1:-1]
        return Intent("analyze_audio_events", path) if path else Intent("missing_wav")
    if command in {"classify audio", "analyze sounds", "classify microphone audio"}:
        return Intent("analyze_audio_events")
    prefixes = (
        (r"(?:you\s*tube)\s+search", "search_youtube"),
        (r"search", "search_google"), (r"remember", "save_memory"),
        (r"(?:take|add)\s+note", "save_note"),
        (r"(?:check\s+password(?:\s+strength)?|password\s+strength)", "check_password_strength"),
    )
    for prefix, name in prefixes:
        match = re.fullmatch(prefix + r"(?:\s+(.*))?", raw, re.IGNORECASE | re.DOTALL)
        if match:
            return Intent(name, (match.group(1) or "").strip())
    storage = {
        "what do you remember": "read_memory", "show memory": "read_memory", "read memory": "read_memory",
        "clear memory": "clear_memory", "delete memory": "clear_memory",
        "show notes": "read_notes", "read notes": "read_notes",
        "clear notes": "clear_notes", "delete notes": "clear_notes",
    }
    if command in storage:
        return Intent(storage[command])
    if command == "help" or "what can you do" in command:
        return Intent("help")
    if command in {"time", "current time", "what is the time", "tell me the time"}:
        return Intent("time")
    if command in {"date", "today date", "what is the date", "what day is today", "day today"}:
        return Intent("date")
    # Preserve existing vision and folder aliases and matching precedence.
    if command == "face detection" or any(x in command for x in ("start face detection", "detect face")):
        return Intent("start_face_detection")
    if any(x in command for x in ("start age detection", "start gender detection", "age gender detection",
                                  "age and gender detection", "detect age", "detect gender")):
        return Intent("start_age_gender_detection")
    if any(x in command for x in ("start hand tracking", "hand tracking", "detect hand", "track hand",
                                  "gesture control", "gesture assistant")):
        return Intent("start_hand_tracking")
    if any(x in command for x in ("show vision logs", "read vision logs")):
        return Intent("read_vision_logs")
    if any(x in command for x in ("clear vision logs", "delete vision logs")):
        return Intent("clear_vision_logs")
    for folder in ("downloads", "desktop", "documents", "pictures", "music", "videos"):
        if f"open {folder} folder" in command or (folder == "desktop" and "open desktop" in command):
            return Intent("open_folder", folder)
    if command in {"shutdown computer", "shutdown pc", "shutdown laptop"}:
        return Intent("request_power", "shutdown")
    if command in {"restart computer", "reboot computer", "restart pc"}:
        return Intent("request_power", "restart")
    if "cancel shutdown" in command or "abort shutdown" in command:
        return Intent("cancel_shutdown")
    target = command.removeprefix("open ")
    if target in WEBSITES:
        return Intent("open_website", target)
    if target in {"chrome", "notepad", "calculator"}:
        return Intent("open_app", target)
    for prefix in ("who is", "what is"):
        if command.startswith(prefix):
            pattern = r"^who\s+is\b" if prefix == "who is" else r"^what\s+is\b"
            query = re.sub(pattern, "", raw, count=1, flags=re.IGNORECASE).strip()
            return Intent("wikipedia", query) if query else Intent("missing_wikipedia", prefix)
    return Intent("unknown")
