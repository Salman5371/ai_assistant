from pathlib import Path
from datetime import datetime


LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
VISION_LOG_FILE = LOGS_DIR / "vision_log.txt"


def log_vision_event(event_text):
    """
    Save a vision-related event into logs/vision_log.txt.
    """
    LOGS_DIR.mkdir(exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    with open(VISION_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{current_time}] {event_text}\n")


def read_vision_logs(limit=10):
    """
    Read the latest vision logs.
    """
    if not VISION_LOG_FILE.exists():
        return "No vision logs found yet."

    with open(VISION_LOG_FILE, "r", encoding="utf-8") as file:
        logs = file.readlines()

    if not logs:
        return "No vision logs found yet."

    latest_logs = logs[-limit:]

    return "Latest vision logs: " + " ".join(log.strip() for log in latest_logs)


def clear_vision_logs():
    """
    Clear all vision logs.
    """
    LOGS_DIR.mkdir(exist_ok=True)

    with open(VISION_LOG_FILE, "w", encoding="utf-8") as file:
        file.write("")

    return "Vision logs have been cleared."
