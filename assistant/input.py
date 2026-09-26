"""Terminal input -> optional capture/STT -> text, including typed fallback."""

def listen(*args, **kwargs):
    from voice.listen import listen as handler
    return handler(*args, **kwargs)


def get_user_command(listen_handler=None):
    """
    Let user choose text command or voice command.

    - Type command and press Enter = text command
    - Press Enter without typing = voice command
    - If voice fails, fallback to text command
    """
    try:
        typed_command = input("\nType command or press Enter for voice: ").strip()

        if typed_command:
            return typed_command

        print("Voice mode selected.")
        return (listen_handler or listen)() or input("Voice unavailable or not understood. Type your command: ").strip()

    except (KeyboardInterrupt, EOFError):
        print("\nInput closed.")
        return "stop"

    except Exception as error:
        print("Listening error:", error)
        print("Voice is not available. Switching to text mode.")

        try:
            typed_command = input("Type your command: ").strip()
            return typed_command
        except (KeyboardInterrupt, EOFError):
            print("\nInput closed.")
            return "stop"
