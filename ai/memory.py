from pathlib import Path


MEMORY_FILE = Path(__file__).resolve().parent.parent / "memory.txt"


def save_memory(text):
    with open(MEMORY_FILE, "a", encoding="utf-8") as file:
        file.write(text + "\n")

    return "I have saved that in memory."


def read_memory():
    if not MEMORY_FILE.exists():
        return "I don't remember anything yet."

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        memories = file.read().strip()

    if memories:
        return memories
    else:
        return "I don't remember anything yet."


def clear_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        file.write("")

    return "Memory has been cleared."