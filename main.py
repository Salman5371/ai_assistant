from voice.listen import listen
from voice.speak import speak
from automation.app_control import open_website, open_app, search_google, search_youtube
from automation.system_control import open_folder, shutdown_computer, restart_computer, cancel_shutdown
from ai.wikipedia_search import get_wikipedia_summary
from ai.memory import save_memory, read_memory, clear_memory
from ai.notes import save_note, read_notes, clear_notes
import datetime


pending_action = None


def safe_speak(text):
    """
    This function safely speaks text.
    If text-to-speech fails, it will print the error instead of crashing.
    """
    try:
        speak(text)
    except Exception as error:
        print("Speak error:", error)
        print("Assistant:", text)


def safe_listen():
    """
    This function safely listens to user's voice.
    If microphone/listening fails, it will return an empty command.
    """
    try:
        return listen()
    except Exception as error:
        print("Listening error:", error)
        safe_speak("Sorry, I could not listen properly.")
        return ""


def safe_process_command(command):
    """
    This function safely processes commands.
    If any command causes an error, the assistant will not crash.
    """
    try:
        return process_command(command)
    except Exception as error:
        print("Command processing error:", error)
        safe_speak("Sorry, something went wrong while processing your command.")
        return True


def process_command(command):
    global pending_action

    # Confirmation system for shutdown/restart
    if pending_action:
        if "confirm" in command or "yes" in command:
            if pending_action == "shutdown":
                response = shutdown_computer()
                safe_speak(response)

            elif pending_action == "restart":
                response = restart_computer()
                safe_speak(response)

            pending_action = None
            return True

        elif "cancel" in command or "no" in command:
            safe_speak("Action cancelled.")
            pending_action = None
            return True

        else:
            safe_speak("Please say confirm or cancel.")
            return True

    if command == "":
        safe_speak("I did not understand. Please say again.")

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
        safe_speak(help_text)

    elif command.startswith("youtube search"):
        query = command.replace("youtube search", "", 1).strip()

        if query:
            safe_speak(f"Searching YouTube for {query}")
            search_youtube(query)
        else:
            safe_speak("What should I search on YouTube?")

    elif command.startswith("search"):
        query = command.replace("search", "", 1).strip()

        if query:
            safe_speak(f"Searching Google for {query}")
            search_google(query)
        else:
            safe_speak("What should I search for?")

    elif command.startswith("who is"):
        query = command.replace("who is", "", 1).strip()

        if query:
            safe_speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            safe_speak(result)
        else:
            safe_speak("Who should I search for?")

    elif command.startswith("what is"):
        query = command.replace("what is", "", 1).strip()

        if query:
            safe_speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            safe_speak(result)
        else:
            safe_speak("What should I search for?")

    elif command.startswith("remember"):
        memory_text = command.replace("remember", "", 1).strip()

        if memory_text:
            response = save_memory(memory_text)
            safe_speak(response)
        else:
            safe_speak("What should I remember?")

    elif "what do you remember" in command or "show memory" in command:
        memories = read_memory()
        safe_speak(memories)

    elif "clear memory" in command or "delete memory" in command:
        response = clear_memory()
        safe_speak(response)

    elif command.startswith("take note") or command.startswith("add note"):
        if command.startswith("take note"):
            note_text = command.replace("take note", "", 1).strip()
        else:
            note_text = command.replace("add note", "", 1).strip()

        if note_text:
            response = save_note(note_text)
            safe_speak(response)
        else:
            safe_speak("What note should I save?")

    elif "show notes" in command or "read notes" in command:
        notes = read_notes()
        safe_speak(notes)

    elif "clear notes" in command or "delete notes" in command:
        response = clear_notes()
        safe_speak(response)

    elif "open downloads folder" in command or "open download folder" in command:
        response = open_folder("downloads")
        safe_speak(response)

    elif "open desktop folder" in command or "open desktop" in command:
        response = open_folder("desktop")
        safe_speak(response)

    elif "open documents folder" in command or "open document folder" in command:
        response = open_folder("documents")
        safe_speak(response)

    elif "open pictures folder" in command or "open picture folder" in command:
        response = open_folder("pictures")
        safe_speak(response)

    elif "open music folder" in command:
        response = open_folder("music")
        safe_speak(response)

    elif "open videos folder" in command or "open video folder" in command:
        response = open_folder("videos")
        safe_speak(response)

    # Safe shutdown / restart commands
    elif "shutdown computer" in command or "shut down computer" in command:
        pending_action = "shutdown"
        safe_speak("Are you sure? Say confirm shutdown to continue or cancel to stop.")

    elif "restart computer" in command or "reboot computer" in command:
        pending_action = "restart"
        safe_speak("Are you sure? Say confirm restart to continue or cancel to stop.")

    elif "cancel shutdown" in command or "abort shutdown" in command:
        response = cancel_shutdown()
        safe_speak(response)

    elif "youtube" in command:
        safe_speak("Opening YouTube")
        open_website("https://www.youtube.com")

    elif "google" in command:
        safe_speak("Opening Google")
        open_website("https://www.google.com")

    elif "chrome" in command:
        safe_speak("Opening Chrome")
        open_app("chrome")

    elif "notepad" in command:
        safe_speak("Opening Notepad")
        open_app("notepad")

    elif "calculator" in command:
        safe_speak("Opening Calculator")
        open_app("calculator")

    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        safe_speak(f"The time is {current_time}")

    elif "stop" in command or "exit" in command or "quit" in command:
        safe_speak("Goodbye")
        return False

    else:
        safe_speak("This command is not available yet.")

    return True


def main():
    safe_speak("Hello Salman Farshi. Your AI assistant is ready.")

    running = True

    while running:
        command = safe_listen()
        running = safe_process_command(command)


if __name__ == "__main__":
    main()