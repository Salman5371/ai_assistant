import os
import platform
import subprocess
from pathlib import Path


def open_folder(folder_name):
    home = Path.home()

    folders = {
        "desktop": home / "Desktop",
        "downloads": home / "Downloads",
        "documents": home / "Documents",
        "pictures": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
    }

    folder_path = folders.get(folder_name.lower())

    if not folder_path:
        return f"I don't know the folder {folder_name}."

    if not folder_path.exists():
        return f"The {folder_name} folder was not found."

    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(folder_path)

        elif system == "Darwin":
            subprocess.Popen(["open", str(folder_path)])

        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(folder_path)])

        return f"Opening {folder_name} folder."

    except Exception as e:
        return f"Could not open {folder_name} folder. Error: {e}"


def shutdown_computer():
    system = platform.system()

    try:
        if system == "Windows":
            subprocess.Popen(["shutdown", "/s", "/t", "10"])
            return "Shutdown scheduled in 10 seconds."

        elif system == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "System Events" to shut down'])
            return "Shutting down the computer."

        elif system == "Linux":
            subprocess.Popen(["systemctl", "poweroff"])
            return "Shutting down the computer."

        else:
            return "Shutdown is not supported on this system."

    except Exception as e:
        return f"Could not shutdown computer. Error: {e}"


def restart_computer():
    system = platform.system()

    try:
        if system == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "10"])
            return "Restart scheduled in 10 seconds."

        elif system == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "System Events" to restart'])
            return "Restarting the computer."

        elif system == "Linux":
            subprocess.Popen(["systemctl", "reboot"])
            return "Restarting the computer."

        else:
            return "Restart is not supported on this system."

    except Exception as e:
        return f"Could not restart computer. Error: {e}"


def cancel_shutdown():
    system = platform.system()

    try:
        if system == "Windows":
            subprocess.Popen(["shutdown", "/a"])
            return "Shutdown or restart has been cancelled."

        else:
            return "Cancel shutdown is only supported on Windows for now."

    except Exception as e:
        return f"Could not cancel shutdown. Error: {e}"