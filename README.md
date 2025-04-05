🗂️ File Organizer (with Undo & GUI)

A simple Python application that helps you organize files into categorized folders based on file extensions.
It features a user-friendly GUI and supports undoing the last organization operation with a single click.
🚀 Features

    Organize files into folders like Images, Documents, Videos, etc.

    GUI with buttons for:

        Organizing files

        Undoing the last operation

    Automatically creates folders and moves files based on type

    Safe Undo: Restores files to their original locations

    Configuration file for custom extension mappings

    Clean exit when window is closed

🛠️ Installation & Usage
1. Clone the Repository

git clone https://github.com/yourusername/file-organizer.git
cd file-organizer

2. Run the Application

python file_organizer.py

✅ Note: Python and tkinter must be installed (included by default in most Python distributions).
📁 File Overview
File	Purpose
file_organizer.py	Main script with GUI
file_tidy_config.json	(Auto-generated) File type to extension mapping
file_tidy_log.json	(Auto-generated) Log of moved files
file_tidy_undo.json	(Auto-generated) Stores info for undoing
🔄 Undo Feature

If you've organized files and want to revert the changes,
just click the "Undo Last Operation" button in the app.

It will restore files to their original locations as long as they haven't been modified or deleted.
⚙️ Custom File Type Mappings

On first run, a file_tidy_config.json file will be created.
You can customize it to define which file extensions go into which folders.

Example:

{
  "IMAGES": [".jpg", ".png"],
  "DOCUMENTS": [".pdf", ".docx", ".txt"]
}

Add or remove categories and extensions however you like.
💡 Future Ideas

    Add a progress bar

    Dark mode for the GUI

    Exclude specific folders or file types

    Drag-and-drop folder selection

📄 License

This project is licensed under the MIT License.
Feel free to use, modify, and share!
🙌 Author

Made with ❤️ by [Your Name]# 🗂️ File Organizer (with Undo & GUI)

A simple Python application that helps you organize files into categorized folders based on file extensions.  
It features a user-friendly GUI and supports undoing the last organization operation with a single click.

---

## 🚀 Features

- Organize files into folders like Images, Documents, Videos, etc.
- GUI with buttons for:
  - Organizing files
  - Undoing the last operation
- Automatically creates folders and moves files based on type
- Safe Undo: Restores files to their original locations
- Configuration file for custom extension mappings
- Clean exit when window is closed

---

## 🛠️ Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/file-organizer.git
cd file-organizer
```

### 2. Run the Application

```bash
python file_organizer.py
```

✅ **Note:** Python and `tkinter` must be installed (included by default in most Python distributions).

---

## 📁 File Overview

| File                   | Purpose                                         |
|------------------------|-------------------------------------------------|
| `file_organizer.py`    | Main script with GUI                            |
| `file_tidy_config.json`| (Auto-generated) File type to extension mapping |
| `file_tidy_log.json`   | (Auto-generated) Log of moved files             |
| `file_tidy_undo.json`  | (Auto-generated) Stores info for undoing        |

---

## 🔄 Undo Feature

If you've organized files and want to revert the changes,  
just click the **"Undo Last Operation"** button in the app.  

It will restore files to their original locations as long as they haven't been modified or deleted.

---

## ⚙️ Custom File Type Mappings

On first run, a `file_tidy_config.json` file will be created.  
You can customize it to define which file extensions go into which folders.

Example:

```json
{
  "IMAGES": [".jpg", ".png"],
  "DOCUMENTS": [".pdf", ".docx", ".txt"]
}
```

Add or remove categories and extensions however you like.

---

## 💡 Future Ideas

- Add a progress bar  
- Dark mode for the GUI  
- Exclude specific folders or file types  
- Drag-and-drop folder selection  

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and share!

---

## 🙌 Author

Made with ❤️ by VikkyTech
