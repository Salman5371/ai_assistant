import re


def normalize_command(command):
    """
    Clean command text and fix common speech recognition issues.
    """
    command = str(command).lower().strip()

    # Remove punctuation
    command = re.sub(r"[^\w\s]", "", command)

    # Remove extra spaces
    command = re.sub(r"\s+", " ", command).strip()

    replacements = [
        ("you tube", "youtube"),
        ("chat gpt", "chatgpt"),
        ("chat g p t", "chatgpt"),
        ("g mail", "gmail"),
        ("stack over flow", "stackoverflow"),
        ("stack overflow", "stackoverflow"),
        ("shut down", "shutdown"),
        ("re boot", "reboot"),
        ("download folder", "downloads folder"),
        ("document folder", "documents folder"),
        ("picture folder", "pictures folder"),
        ("video folder", "videos folder"),
    ]

    for old, new in replacements:
        command = command.replace(old, new)

    return command
