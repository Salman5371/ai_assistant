import shutil
from pathlib import Path


def get_unique_destination(destination):
    """
    If same filename already exists, create a new filename.
    Example:
    file.pdf -> file_1.pdf
    """
    if not destination.exists():
        return destination

    parent = destination.parent
    stem = destination.stem
    suffix = destination.suffix

    counter = 1

    while True:
        new_destination = parent / f"{stem}_{counter}{suffix}"

        if not new_destination.exists():
            return new_destination

        counter += 1


def organize_folder(folder_name):
    """
    Organize Downloads or Desktop files into category folders.
    """

    home = Path.home()

    folders = {
        "downloads": home / "Downloads",
        "desktop": home / "Desktop",
    }

    target_folder = folders.get(folder_name.lower())

    if target_folder is None:
        return f"I can only organize Downloads or Desktop folder."

    if not target_folder.exists():
        return f"The {folder_name} folder was not found."

    file_types = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
        "Videos": [".mp4", ".mkv", ".mov", ".avi", ".wmv"],
        "Music": [".mp3", ".wav", ".aac", ".flac"],
        "Python Files": [".py", ".ipynb"],
        "Zip Files": [".zip", ".rar", ".7z", ".tar", ".gz"],
    }

    moved_count = 0

    for item in target_folder.iterdir():
        # Skip folders
        if item.is_dir():
            continue

        # Skip hidden files
        if item.name.startswith("."):
            continue

        file_extension = item.suffix.lower()
        category_name = "Other Files"

        for category, extensions in file_types.items():
            if file_extension in extensions:
                category_name = category
                break

        category_folder = target_folder / category_name
        category_folder.mkdir(exist_ok=True)

        destination = category_folder / item.name
        destination = get_unique_destination(destination)

        try:
            shutil.move(str(item), str(destination))
            moved_count += 1
        except Exception as error:
            print(f"Could not move {item.name}: {error}")

    return f"Folder organized successfully. I moved {moved_count} files."