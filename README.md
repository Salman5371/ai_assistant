# AI Virtual Assistant

A Python-based voice-controlled AI Virtual Assistant that can listen to voice commands, speak responses, search online, open apps/websites, manage memory and notes, and check password strength.

## Features

- Voice command recognition
- Text-to-speech response
- Google search
- YouTube search
- Wikipedia summary
- Save and read memory
- Take and read notes
- Open folders
- Open websites
- Open apps
- Tell current time
- Tell current date and day
- Shutdown/restart confirmation
- Password strength checker
- Safe microphone error handling

## Technologies Used

- Python
- SpeechRecognition
- PyAudio
- pyttsx3
- Wikipedia
- webbrowser
- subprocess
- pathlib
- re

## Project Structure

```text
ai_assistant/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── voice/
│   ├── __init__.py
│   ├── listen.py
│   └── speak.py
│
├── automation/
│   ├── __init__.py
│   ├── app_control.py
│   └── system_control.py
│
├── ai/
│   ├── __init__.py
│   ├── memory.py
│   ├── notes.py
│   └── wikipedia_search.py
│
└── cyber/
    ├── __init__.py
    └── password_checker.py
```

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate virtual environment on Windows PowerShell:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install required packages:

```bash
python -m pip install SpeechRecognition pyttsx3 wikipedia pyaudio
```

If PyAudio gives an installation error, use Python 3.12 or Python 3.13 for best compatibility.

## Run Project

```bash
python main.py
```

## Example Voice Commands

### Search Commands

```text
search python tutorial
youtube search python full course
who is Albert Einstein
what is artificial intelligence
```

### Memory Commands

```text
remember my favorite language is Python
what do you remember
clear memory
```

### Notes Commands

```text
take note I have to practice Python today
show notes
clear notes
```

### Folder Commands

```text
open downloads folder
open desktop folder
open documents folder
open pictures folder
open music folder
open videos folder
```

### Website Commands

```text
open youtube
open google
open github
open gmail
open chatgpt
open facebook
open stack overflow
```

### App Commands

```text
open chrome
open notepad
open calculator
```

### Time and Date Commands

```text
what is the time
what is the date
what day is today
```

### Cybersecurity Commands

```text
check password strength hello123
check password strength Hello@123
```

### System Commands

```text
shutdown computer
restart computer
cancel shutdown
```

Shutdown and restart commands ask for confirmation before running.

## Important Notes

- Do not test real passwords with the password checker.
- Use demo passwords only.
- Do not push `.env` files to GitHub.
- Python 3.12 or 3.13 is recommended for PyAudio.

## Future Improvements

- AI chat mode
- PDF reader
- Website status checker
- Face detection
- Hand tracking
- Virtual mouse

## Author

Salman Farshi