from voice.listen import listen
from voice.speak import speak
from automation.app_control import open_website, open_app
import datetime

def process_command(command):
    if command == "":
        speak("I did not understand. Please say again.")

    elif "youtube" in command:
        speak("Opening YouTube")
        open_website("https://www.youtube.com")

    elif "google" in command:
        speak("Opening Google")
        open_website("https://www.google.com")

    elif "chrome" in command:
        speak("Opening Chrome")
        open_app("chrome")

    elif "notepad" in command:
        speak("Opening Notepad")
        open_app("notepad")

    elif "calculator" in command:
        speak("Opening Calculator")
        open_app("calculator")

    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")

    elif "stop" in command or "exit" in command or "quit" in command:
        speak("Goodbye")
        return False

    else:
        speak("This command is not available yet.")

    return True


def main():
    speak("Hello Faisal. Your AI assistant is ready.")

    running = True

    while running:
        command = listen()
        running = process_command(command)


if __name__ == "__main__":
    main()