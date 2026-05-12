from voice.listen import listen
from voice.speak import speak

from automation.app_control import (
    open_website,
    open_app,
    search_google,
    search_youtube,
)

from automation.system_control import (
    open_folder,
    shutdown_computer,
    restart_computer,
    cancel_shutdown,
)

from ai.wikipedia_search import get_wikipedia_summary
from ai.memory import save_memory, read_memory, clear_memory
from ai.notes import save_note, read_notes, clear_notes

from cyber.password_checker import check_password_strength

from vision.face_detection import start_face_detection
from vision.age_gender_detection import start_age_gender_detection
from vision.hand_tracking import start_hand_tracking
from vision.vision_logger import read_vision_logs, clear_vision_logs

import datetime
import re


pending_action = None


def safe_speak(text):
    """
    Safely speak text without crashing the assistant.
    """
    try:
        speak(text)
    except Exception as error:
        print("Speak error:", error)
        print("Assistant:", text)


def get_user_command():
    """
    Let user choose text command or voice command.

    - Type command and press Enter = text command
    - Press Enter without typing = voice command
    - If voice fails, fallback to text command
    """
    try:
        typed_command = input("\nType command or press Enter for voice: ").strip()

        if typed_command:
            print("Typed command:", typed_command)
            return typed_command

        print("Voice mode selected.")
        return listen()

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected.")
        return "stop"

    except Exception as error:
        print("Listening error:", error)
        print("Voice is not available. Switching to text mode.")

        try:
            typed_command = input("Type your command: ").strip()
            return typed_command
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected.")
            return "stop"


def safe_process_command(command):
    """
    Safely process command without crashing the assistant.
    """
    try:
        print("Detected command:", command)
        return process_command(command)
    except Exception as error:
        print("Command processing error:", error)
        safe_speak("Sorry, something went wrong while processing your command.")
        return True


def normalize_command(command):
    """
    Clean command text and fix common speech recognition issues.
    """
    command = str(command).lower().strip()

    # Remove punctuation
    command = re.sub(r"[^\w\s]", "", command)

    # Remove extra spaces
    command = re.sub(r"\s+", " ", command).strip()

    replacements = [
        ("you tube", "youtube"),
        ("chat gpt", "chatgpt"),
        ("chat g p t", "chatgpt"),
        ("g mail", "gmail"),
        ("stack over flow", "stackoverflow"),
        ("stack overflow", "stackoverflow"),
        ("shut down", "shutdown"),
        ("re boot", "reboot"),
        ("download folder", "downloads folder"),
        ("document folder", "documents folder"),
        ("picture folder", "pictures folder"),
        ("video folder", "videos folder"),
    ]

    for old, new in replacements:
        command = command.replace(old, new)

    return command


def get_greeting():
    """
    Return greeting based on current time.
    """
    current_hour = datetime.datetime.now().hour

    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 21:
        return "Good evening"
    else:
        return "Good night"


def process_command(command):
    global pending_action

    command = normalize_command(command)
    print("Normalized command:", command)

    # 1. Empty command
    if command == "":
        print("No command detected.")
        return True

    # 2. Stop assistant
    if "stop" in command or "exit" in command or "quit" in command:
        safe_speak("Goodbye")
        return False

    # 3. Pending confirmation for shutdown/restart
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

    # 4. Help command
    if command == "help" or "what can you do" in command:
        help_text = """
        I can help you with these commands:

        Input commands:
        Type a command in terminal and press Enter.
        Or press Enter without typing to use voice command.

        Search commands:
        Say or type youtube search followed by a topic.
        Say or type search followed by a topic.

        Wikipedia commands:
        Say or type who is followed by a person's name.
        Say or type what is followed by a topic.

        Memory commands:
        Say or type remember followed by something to save memory.
        Say or type what do you remember to hear saved memory.
        Say or type show memory to hear saved memory.
        Say or type clear memory to delete memory.

        Notes commands:
        Say or type take note followed by your note.
        Say or type show notes to hear your notes.
        Say or type clear notes to delete notes.

        Cybersecurity commands:
        Say or type check password strength followed by a demo password.
        Say or type check password followed by a demo password.

        Computer vision commands:
        Say or type start face detection.
        Say or type face detection.
        Say or type start age detection.
        Say or type start gender detection.
        Say or type age gender detection.
        Say or type start hand tracking.
        Say or type hand tracking.
        Say or type gesture control.
        Say or type gesture assistant.
        Say or type show vision logs.
        Say or type clear vision logs.

        Folder commands:
        Say or type open downloads folder.
        Say or type open desktop folder.
        Say or type open documents folder.
        Say or type open pictures folder.
        Say or type open music folder.
        Say or type open videos folder.

        System commands:
        Say or type shutdown computer.
        Say or type restart computer.
        Say or type cancel shutdown.

        App and website commands:
        Say or type open youtube.
        Say or type open google.
        Say or type open github.
        Say or type open gmail.
        Say or type open chatgpt.
        Say or type open facebook.
        Say or type open stack overflow.
        Say or type open chrome.
        Say or type open notepad.
        Say or type open calculator.

        Time and date commands:
        Say or type what is the time.
        Say or type what is the date.
        Say or type what day is today.

        Say or type stop to close me.
        """
        safe_speak(help_text)
        return True

    # 5. Time command
    if (
        "time" in command
        or "current time" in command
        or "what is the time" in command
        or "tell me the time" in command
    ):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        safe_speak(f"The time is {current_time}")
        return True

    # 6. Date and day command
    if (
        "date" in command
        or "today date" in command
        or "what is the date" in command
        or "what day is today" in command
        or "day today" in command
    ):
        today = datetime.datetime.now()
        formatted_date = today.strftime("%A, %B %d, %Y")
        safe_speak(f"Today is {formatted_date}")
        return True

    # 7. YouTube search command
    if command.startswith("youtube search"):
        query = command.replace("youtube search", "", 1).strip()

        if query:
            safe_speak(f"Searching YouTube for {query}")
            search_youtube(query)
        else:
            safe_speak("What should I search on YouTube?")

        return True

    # 8. Google search command
    if command.startswith("search"):
        query = command.replace("search", "", 1).strip()

        if query:
            safe_speak(f"Searching Google for {query}")
            search_google(query)
        else:
            safe_speak("What should I search for?")

        return True

    # 9. Memory system
    if command.startswith("remember"):
        memory_text = command.replace("remember", "", 1).strip()

        if memory_text:
            response = save_memory(memory_text)
            safe_speak(response)
        else:
            safe_speak("What should I remember?")

        return True

    if "what do you remember" in command or "show memory" in command or "read memory" in command:
        memories = read_memory()
        safe_speak(memories)
        return True

    if "clear memory" in command or "delete memory" in command:
        response = clear_memory()
        safe_speak(response)
        return True

    # 10. Notes system
    if command.startswith("take note") or command.startswith("add note"):
        if command.startswith("take note"):
            note_text = command.replace("take note", "", 1).strip()
        else:
            note_text = command.replace("add note", "", 1).strip()

        if note_text:
            response = save_note(note_text)
            safe_speak(response)
        else:
            safe_speak("What note should I save?")

        return True

    if "show notes" in command or "read notes" in command:
        notes = read_notes()
        safe_speak(notes)
        return True

    if "clear notes" in command or "delete notes" in command:
        response = clear_notes()
        safe_speak(response)
        return True

    # 11. Password strength checker
    if command.startswith("check password strength"):
        password = command.replace("check password strength", "", 1).strip()

        if password:
            response = check_password_strength(password)
            safe_speak(response)
        else:
            safe_speak("Please say or type a demo password after check password strength.")

        return True

    if command.startswith("check password"):
        password = command.replace("check password", "", 1).strip()

        if password:
            response = check_password_strength(password)
            safe_speak(response)
        else:
            safe_speak("Please say or type a demo password after check password.")

        return True

    if command.startswith("password strength"):
        password = command.replace("password strength", "", 1).strip()

        if password:
            response = check_password_strength(password)
            safe_speak(response)
        else:
            safe_speak("Please say or type a demo password after password strength.")

        return True

    # 12. Face detection
    if (
        "start face detection" in command
        or command == "face detection"
        or "detect face" in command
    ):
        safe_speak("Starting face detection. Press Q to stop.")
        response = start_face_detection()
        safe_speak(response)
        return True

    # 13. Age and gender detection
    if (
        "start age detection" in command
        or "start gender detection" in command
        or "age gender detection" in command
        or "age and gender detection" in command
        or "detect age" in command
        or "detect gender" in command
    ):
        safe_speak("Starting age and gender detection. Press Q to stop.")
        response = start_age_gender_detection()
        safe_speak(response)
        return True

    # 14. Hand tracking / gesture control
    if (
        "start hand tracking" in command
        or "hand tracking" in command
        or "detect hand" in command
        or "track hand" in command
        or "gesture control" in command
        or "gesture assistant" in command
    ):
        safe_speak("Starting gesture controlled assistant. Press Q to stop.")
        response = start_hand_tracking()
        safe_speak(response)
        return True

    # 15. Vision logs
    if "show vision logs" in command or "read vision logs" in command:
        logs = read_vision_logs()
        safe_speak(logs)
        return True

    if "clear vision logs" in command or "delete vision logs" in command:
        response = clear_vision_logs()
        safe_speak(response)
        return True

    # 16. Folder automation
    if "open downloads folder" in command or "open download folder" in command:
        response = open_folder("downloads")
        safe_speak(response)
        return True

    if "open desktop folder" in command or "open desktop" in command:
        response = open_folder("desktop")
        safe_speak(response)
        return True

    if "open documents folder" in command or "open document folder" in command:
        response = open_folder("documents")
        safe_speak(response)
        return True

    if "open pictures folder" in command or "open picture folder" in command:
        response = open_folder("pictures")
        safe_speak(response)
        return True

    if "open music folder" in command:
        response = open_folder("music")
        safe_speak(response)
        return True

    if "open videos folder" in command or "open video folder" in command:
        response = open_folder("videos")
        safe_speak(response)
        return True

    # 17. Safe shutdown/restart
    if "shutdown computer" in command or "shutdown pc" in command or "shutdown laptop" in command:
        pending_action = "shutdown"
        safe_speak("Are you sure? Say or type confirm shutdown to continue or cancel to stop.")
        return True

    if "restart computer" in command or "reboot computer" in command or "restart pc" in command:
        pending_action = "restart"
        safe_speak("Are you sure? Say or type confirm restart to continue or cancel to stop.")
        return True

    if "cancel shutdown" in command or "abort shutdown" in command:
        response = cancel_shutdown()
        safe_speak(response)
        return True

    # 18. Website commands
    if "youtube" in command:
        safe_speak("Opening YouTube")
        open_website("https://www.youtube.com")
        return True

    if "google" in command:
        safe_speak("Opening Google")
        open_website("https://www.google.com")
        return True

    if "github" in command:
        safe_speak("Opening GitHub")
        open_website("https://github.com")
        return True

    if "gmail" in command:
        safe_speak("Opening Gmail")
        open_website("https://mail.google.com")
        return True

    if "chatgpt" in command or "chat gpt" in command:
        safe_speak("Opening ChatGPT")
        open_website("https://chatgpt.com")
        return True

    if "facebook" in command:
        safe_speak("Opening Facebook")
        open_website("https://www.facebook.com")
        return True

    if "stack overflow" in command or "stackoverflow" in command:
        safe_speak("Opening Stack Overflow")
        open_website("https://stackoverflow.com")
        return True

    # 19. App commands
    if "chrome" in command:
        safe_speak("Opening Chrome")
        open_app("chrome")
        return True

    if "notepad" in command:
        safe_speak("Opening Notepad")
        open_app("notepad")
        return True

    if "calculator" in command:
        safe_speak("Opening Calculator")
        open_app("calculator")
        return True

    # 20. Wikipedia commands kept near the end
    # This prevents "what is the time" from going to Wikipedia
    if command.startswith("who is"):
        query = command.replace("who is", "", 1).strip()

        if query:
            safe_speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            safe_speak(result)
        else:
            safe_speak("Who should I search for?")

        return True

    if command.startswith("what is"):
        query = command.replace("what is", "", 1).strip()

        if query:
            safe_speak(f"Searching Wikipedia for {query}")
            result = get_wikipedia_summary(query)
            safe_speak(result)
        else:
            safe_speak("What should I search for?")

        return True

    # 21. Unknown command
    safe_speak("This command is not available yet.")
    return True


def main():
    greeting = get_greeting()
    safe_speak(f"{greeting} Salman Farshi. Your AI assistant is ready.")

    print("\nInput guide:")
    print("- Type a command and press Enter to use text command.")
    print("- Press Enter without typing to use voice command.")
    print("- Type stop to close the assistant.")

    running = True

    while running:
        command = get_user_command()
        running = safe_process_command(command)


if __name__ == "__main__":
    main()