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