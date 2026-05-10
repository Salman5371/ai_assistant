from voice.listen import listen
from voice.speak import speak
from automation.app_control import open_website, open_app, search_google, search_youtube
from ai.wikipedia_search import get_wikipedia_summary
from ai.memory import save_memory, read_memory, clear_memory
import datetime


def process_command(command):
    if command == "":
        speak("I did not understand. Please say again.")

    elif command.startswith("youtube search"):
        query = command.replace("youtube search", "", 1).strip()

        if query:
            speak(f"Searching YouTube for {query}")
            search_youtube(query)
        else:
            speak("What should I search on YouTube?")

    elif command.startswith("search"):
        query = command.replace("search", "", 1).strip()

        if query:
            speak(f"Searching Google for {query}")
            search_google(query)
        else:
            speak("What should I search for?")

    elif command.startswith("who is"):
        query = command.replace("who is", "", 1).strip()

        if query:
            speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            speak(result)
        else:
            speak("Who should I search for?")

    elif command.startswith("what is"):
        query = command.replace("what is", "", 1).strip()

        if query:
            speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            speak(result)
        else:
            speak("What should I search for?")
    elif command.startswith("remember"):
        memory_text = command.replace("remember", "", 1).strip()

        if memory_text:
            response = save_memory(memory_text)
            speak(response)
        else:
            speak("What should I remember?")

    elif "what do you remember" in command or "show memory" in command:
        memories = read_memory()
        speak(memories)

    elif "clear memory" in command or "delete memory" in command:
        response = clear_memory()
        speak(response)        



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
    speak("Hello Salman Farshi. Your AI assistant is ready.")

    running = True

    while running:
        command = listen()
        running = process_command(command)


if __name__ == "__main__":
    main()