# AI Virtual Assistant

A Python-based AI Virtual Assistant with text commands, voice commands, automation, cybersecurity tools, and computer vision features.

This assistant can open apps and websites, search online, save notes and memory, check password strength, detect faces, estimate age/gender, track hands, and control actions using hand gestures.

## Features

### Input System

- Text command input from terminal
- Voice command input
- Text fallback support if microphone is not available

### Search and AI Assistant Commands

- Google search
- YouTube search
- Wikipedia summary
- Current time
- Current date and day

### Personal Assistant Features

- Save memory
- Read saved memory
- Clear memory
- Take notes
- Read notes
- Clear notes

### Automation Features

- Open common folders
- Open websites
- Open desktop apps
- Shutdown computer with confirmation
- Restart computer with confirmation
- Cancel shutdown

### Cybersecurity Features

- Password strength checker
- Gives password feedback
- Checks length, uppercase, lowercase, number, and special character

### Computer Vision Features

- Face detection
- Age and gender prediction
- Hand tracking
- Finger counting
- Gesture-controlled assistant
- Vision event logging

### Gesture Control

Right hand gestures:

```text
Open Palm  = Activate gesture assistant
One Finger = Open Google
Two Fingers = Open YouTube
Thumbs Up  = Confirm
```

Left hand gesture:

```text
Fist = Stop camera
```

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
├── cyber/
│   ├── __init__.py
│   └── password_checker.py
│
├── vision/
│   ├── __init__.py
│   ├── face_detection.py
│   ├── age_gender_detection.py
│   ├── hand_tracking.py
│   └── vision_logger.py
│
├── models/
│   ├── opencv_face_detector.pbtxt
│   ├── opencv_face_detector_uint8.pb
│   ├── age_deploy.prototxt
│   ├── age_net.caffemodel
│   ├── gender_deploy.prototxt
│   ├── gender_net.caffemodel
│   └── hand_landmarker.task
│
└── logs/
    └── vision_log.txt
```

## Technologies Used

- Python
- SpeechRecognition
- pyttsx3
- Wikipedia
- OpenCV
- MediaPipe
- NumPy
- pathlib
- subprocess
- webbrowser

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/ai_assistant.git
cd ai_assistant
```

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
python -m pip install -r requirements.txt
```

If you are using a custom environment like `.venv-1`, activate it like this:

```bash
.\.venv-1\Scripts\Activate.ps1
```

## Requirements

Example `requirements.txt`:

```txt
SpeechRecognition==3.16.1
pyttsx3==2.99
wikipedia==1.4.0
opencv-python
mediapipe==0.10.35
numpy
sounddevice
```

Note: PyAudio may fail on Python 3.14. This project supports text command input, so the assistant can still be used even if microphone input is not available.

## Model Files

Computer vision features need model files inside the `models/` folder.

Required model files:

```text
opencv_face_detector.pbtxt
opencv_face_detector_uint8.pb
age_deploy.prototxt
age_net.caffemodel
gender_deploy.prototxt
gender_net.caffemodel
hand_landmarker.task
```

The model files are not uploaded to GitHub because some of them are large. Download them separately and place them inside the `models/` folder.

Add this to `.gitignore`:

```gitignore
models/
logs/
memory.txt
notes.txt
tasks.txt
.env
.venv/
.venv-1/
__pycache__/
*.pyc
```

## Run Project

```bash
python main.py
```

After running, you will see:

```text
Type command or press Enter for voice:
```

Use text command:

```text
open google
```

Or press Enter without typing to use voice command.

## Example Commands

### General Commands

```text
help
stop
what is the time
what is the date
what day is today
```

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
show memory
clear memory
```

### Notes Commands

```text
take note I have to practice Python today
show notes
clear notes
```

### Cybersecurity Commands

```text
check password strength hello123
check password strength Hello@123
check password Hello@123
```

Do not test real passwords. Use demo passwords only.

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

### System Commands

```text
shutdown computer
restart computer
cancel shutdown
```

Shutdown and restart commands ask for confirmation before running.

### Computer Vision Commands

```text
start face detection
face detection
start age detection
start gender detection
age gender detection
start hand tracking
hand tracking
gesture control
gesture assistant
show vision logs
clear vision logs
```

## Gesture Control Guide

Run:

```text
gesture control
```

Then use these gestures:

```text
Right Open Palm  = Activate assistant
Right One Finger = Open Google
Right Two Fingers = Open YouTube
Right Thumbs Up  = Confirm
Left Fist        = Stop camera
```

Press `Q` to close camera windows manually.

## Direct Vision Tests

Face detection:

```bash
python -m vision.face_detection
```

Age and gender detection:

```bash
python -m vision.age_gender_detection
```

Hand tracking and gesture control:

```bash
python -m vision.hand_tracking
```

Vision logger:

```bash
python -m vision.vision_logger
```

## Important Notes

- Use text command mode if microphone input is not working.
- Press Enter without typing to use voice mode.
- Use demo passwords only.
- Do not upload `.env`, virtual environment folders, logs, or model files to GitHub.
- Age and gender detection is only an approximate model prediction.
- Gesture detection is rule-based and may not be 100% accurate in every camera angle.
- Good lighting improves vision accuracy.

## Current Features Completed

```text
✅ Text command input
✅ Voice command input
✅ Google search
✅ YouTube search
✅ Wikipedia summary
✅ Memory system
✅ Notes system
✅ Password strength checker
✅ Folder automation
✅ Website automation
✅ App automation
✅ Time and date command
✅ Shutdown/restart confirmation
✅ Face detection
✅ Age and gender detection
✅ Hand tracking
✅ Gesture-controlled assistant
✅ Vision logs
```

## Future Improvements

- AI chat mode
- PDF reader
- Smart command suggestion
- Security lock mode
- Face recognition
- Attendance system
- Study focus guardian
- Virtual drawing board
- Virtual mouse
- Object detection
- Emotion detection
- Project dashboard GUI

## Author

Salman Farshi