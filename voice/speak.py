try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

engine = pyttsx3.init() if pyttsx3 else None

def speak(text):
    print("Assistant:", text)
    if engine:
        engine.say(text)
        engine.runAndWait()