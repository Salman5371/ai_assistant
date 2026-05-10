import pyttsx3
import re


def clean_text(text):
    """
    Remove extra spaces and new lines so pyttsx3 can speak properly.
    """
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text, max_length=180):
    """
    Split long text into smaller parts.
    This helps pyttsx3 speak long answers without stopping.
    """
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 <= max_length:
            current_chunk += " " + word
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def speak(text):
    """
    Speak assistant response safely.
    Engine is created every time to avoid pyttsx3 getting stuck after first speech.
    """
    text = clean_text(text)

    if not text:
        return

    print("Assistant:", text)

    try:
        engine = pyttsx3.init()

        # Voice speed
        engine.setProperty("rate", 165)

        # Volume: 0.0 to 1.0
        engine.setProperty("volume", 1.0)

        # Speak in small chunks
        for chunk in split_text(text):
            engine.say(chunk)

        engine.runAndWait()
        engine.stop()

    except Exception as error:
        print("Text-to-speech error:", error)