from pathlib import Path
from datetime import datetime


NOTES_FILE = Path(__file__).resolve().parent.parent / "notes.txt"


def save_note(text):
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    with open(NOTES_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{current_time}] {text}\n")

    return "I have saved your note."


def read_notes():
    if not NOTES_FILE.exists():
        return "You don't have any notes yet."

    with open(NOTES_FILE, "r", encoding="utf-8") as file:
        notes = file.read().strip()

    if notes:
        return notes
    else:
        return "You don't have any notes yet."


def clear_notes():
    with open(NOTES_FILE, "w", encoding="utf-8") as file:
        file.write("")

    return "All notes have been cleared."