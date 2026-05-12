import speech_recognition as sr
import sounddevice as sd
import numpy as np


def listen():
    """
    Listen from microphone using sounddevice instead of PyAudio.
    This works better with Python 3.14 because it avoids PyAudio.
    """

    recognizer = sr.Recognizer()

    sample_rate = 16000
    duration = 5

    print("Listening...")

    try:
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )

        sd.wait()

        audio_bytes = audio_data.tobytes()

        audio = sr.AudioData(
            audio_bytes,
            sample_rate,
            2,
        )

        print("Recognizing...")

        command = recognizer.recognize_google(audio)
        print("You said:", command)

        return command

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""

    except sr.RequestError as error:
        print("Speech recognition request error:", error)
        return ""

    except Exception as error:
        print("Listening error:", error)
        return ""