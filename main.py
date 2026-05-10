from voice.listen import listen
from voice.speak import speak
from automation.app_control import open_website, open_app, search_google, search_youtube
from automation.system_control import open_folder, shutdown_computer, restart_computer, cancel_shutdown
from ai.wikipedia_search import get_wikipedia_summary
from ai.memory import save_memory, read_memory, clear_memory
from ai.notes import save_note, read_notes, clear_notes
import datetime


pending_action = None


def process_command(command):
    global pending_action

    # Confirmation system for shutdown/restart
    if pending_action:
        if "confirm" in command or "yes" in command:
            if pending_action == "shutdown":
                response = shutdown_computer()
                speak(response)

            elif pending_action == "restart":
                response = restart_computer()
                speak(response)

            pending_action = None
            return True

        elif "cancel" in command or "no" in command:
            speak("Action cancelled.")
            pending_action = None
            return True

        else:
            speak("Please say confirm or cancel.")
            return True

    if command == "":
        speak("I did not understand. Please say again.")

    # Help command
    elif command == "help" or "what can you do" in command:
        help_text = """
        I can help you with these commands:

        Say youtube search followed by a topic.
        Say search followed by a topic.
        Say who is followed by a person's name.
        Say what is followed by a topic.

        Say remember followed by something to save memory.
        Say what do you remember to hear saved memory.
        Say clear memory to delete memory.

        Say take note followed by your note.
        Say show notes to hear your notes.
        Say clear notes to delete notes.

        Say open downloads folder.
        Say open desktop folder.
        Say open documents folder.
        Say open pictures folder.
        Say open music folder.
        Say open videos folder.

        Say shutdown computer.
        Say restart computer.
        Say cancel shutdown.

        Say open youtube.
        Say open google.
        Say open chrome.
        Say open notepad.
        Say open calculator.

        Say what is the time.
        Say stop to close me.
        """
        speak(help_text)

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

    elif command.startswith("take note") or command.startswith("add note"):
        if command.startswith("take note"):
            note_text = command.replace("take note", "", 1).strip()
        else:
            note_text = command.replace("add note", "", 1).strip()

        if note_text:
            response = save_note(note_text)
            speak(response)
        else:
            speak("What note should I save?")

    elif "show notes" in command or "read notes" in command:
        notes = read_notes()
        speak(notes)

    elif "clear notes" in command or "delete notes" in command:
        response = clear_notes()
        speak(response)

    elif "open downloads folder" in command or "open download folder" in command:
        response = open_folder("downloads")
        speak(response)

    elif "open desktop folder" in command or "open desktop" in command:
        response = open_folder("desktop")
        speak(response)

    elif "open documents folder" in command or "open document folder" in command:
        response = open_folder("documents")
        speak(response)

    elif "open pictures folder" in command or "open picture folder" in command:
        response = open_folder("pictures")
        speak(response)

    elif "open music folder" in command:
        response = open_folder("music")
        speak(response)

    elif "open videos folder" in command or "open video folder" in command:
        response = open_folder("videos")
        speak(response)

    # Safe shutdown / restart commands
    elif "shutdown computer" in command or "shut down computer" in command:
        pending_action = "shutdown"
        speak("Are you sure? Say confirm shutdown to continue or cancel to stop.")

    elif "restart computer" in command or "reboot computer" in command:
        pending_action = "restart"
        speak("Are you sure? Say confirm restart to continue or cancel to stop.")

    elif "cancel shutdown" in command or "abort shutdown" in command:
        response = cancel_shutdown()
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