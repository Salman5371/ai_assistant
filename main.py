"""Terminal entry point: input -> STT -> routing/features -> response -> TTS."""
from assistant.runtime import (
    get_greeting, get_user_command, safe_speak, safe_process_command,
    process_command, normalize_command,
)


def main():
    safe_speak(f"{get_greeting()} Salman Farshi. Your AI assistant is ready.")
    print("\nInput guide:")
    print("- Type a command and press Enter to use text command.")
    print("- Press Enter without typing to use voice command.")
    print("- Type stop to close the assistant.")
    try:
        while safe_process_command(get_user_command()):
            pass
    except KeyboardInterrupt:
        safe_speak("Goodbye")


if __name__ == "__main__":
    main()
