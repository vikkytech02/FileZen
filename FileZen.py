import os
import shutil
import json
import threading
import sys
from pathlib import Path
from tkinter import Tk, Button, Label, filedialog

# File type categories
DEFAULT_DIRECTORIES = {
    "HTML": [".html5", ".html", ".htm", ".xhtml"],
    "IMAGES": [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".svg", ".tiff"],
    "VIDEOS": [".mp4", ".mov", ".avi", ".flv", ".wmv"],
    "DOCUMENTS": [".pdf", ".docx", ".doc", ".ppt", ".pptx", ".xls", ".xlsx"],
    "ARCHIVES": [".zip", ".rar", ".tar", ".gz", ".7z"],
    "AUDIO": [".mp3", ".wav", ".aac"],
    "PLAINTEXT": [".txt", ".log", ".csv"],
    "PYTHON": [".py"],
    "EXE": [".exe"],
    "SHELL": [".sh"]
}

# Config and log files
CONFIG_FILE = "file_tidy_config.json"
LOG_FILE = "file_tidy_log.json"
UNDO_FILE = "file_tidy_undo.json"

# Load custom or default config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        return DEFAULT_DIRECTORIES

# Save config
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Organize files into folders
def organize_files(directory, dry_run=False):
    file_formats = {ext: category for category, extensions in load_config().items() for ext in extensions}
    moved_files = {}

    for item in os.scandir(directory):
        if item.is_dir():
            continue

        file_path = Path(item)
        file_format = file_path.suffix.lower()

        if file_format in file_formats:
            target_dir = Path(directory) / file_formats[file_format]
            target_dir.mkdir(exist_ok=True)
            new_path = target_dir / file_path.name

            if not dry_run:
                shutil.move(str(file_path), str(new_path))
                moved_files[str(file_path)] = str(new_path)
            else:
                print(f"[DRY RUN] {file_path} -> {new_path}")

    if moved_files:
        with open(LOG_FILE, "w") as log:
            json.dump(moved_files, log, indent=4)
        with open(UNDO_FILE, "w") as undo:
            json.dump(moved_files, undo, indent=4)

# Undo last file organization
def undo_last_operation():
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            moved_files = json.load(f)

        for old_path, new_path in moved_files.items():
            if os.path.exists(new_path):
                shutil.move(new_path, old_path)
        os.remove(UNDO_FILE)
        print("Undo successful.")
    else:
        print("No operation to undo.")

# GUI interface
def start_gui():
    def on_organize_click():
        directory = filedialog.askdirectory()
        if directory:
            threading.Thread(target=organize_files, args=(directory,)).start()

    def on_undo_click():
        undo_last_operation()

    def on_close():
        root.destroy()
        sys.exit()

    root = Tk()
    root.title("FileZen")
    root.geometry("300x150")

    Label(root, text="Welcome to FileZen", font=("Arial", 14)).pack(pady=10)
    Button(root, text="Organize Files", command=on_organize_click).pack(pady=5)
    Button(root, text="Undo Last Operation", command=on_undo_click).pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# Run the app
if __name__ == "__main__":
    start_gui()
