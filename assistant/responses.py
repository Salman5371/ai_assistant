"""Response output stage, with terminal fallback when TTS is unavailable."""

def speak(*args, **kwargs):
    from voice.speak import speak as handler
    return handler(*args, **kwargs)


def safe_speak(text, *, settings=None):
    """
    Safely speak text without crashing the assistant.
    """
    try:
        return speak(text, settings=settings)
    except Exception as error:
        print("Speak error:", error)
        print("Assistant:", text)
        return False
