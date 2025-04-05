# 🗂️ FileZen

**FileZen** is a lightweight and user-friendly Python app that helps you keep your folders clean and organized.  
It automatically sorts files into categorized folders based on their extensions — and you can undo it anytime with just one click.

---

## 🚀 Features

- 📁 Organize files into folders (Images, Documents, Videos, etc.)
- 🖱️ Simple GUI interface — no command line needed
- 🔄 Undo the last file organization operation safely
- 🛠️ Configurable extension-to-folder mapping
- ✅ Clean exit when the window is closed
- 💡 Fast and multithreaded file moving

---

## 🛠️ Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/FileZen.git
cd FileZen
```

### 2. Run the App

```bash
python file_organizer.py
```

✅ **Note:** Requires Python 3.6+ with `tkinter` (usually comes built-in).

---

## 🖥️ How It Works

- When you click **"Organize Files"**, it asks you to select a folder.
- It automatically moves files into new subfolders like:
  - `IMAGES`, `DOCUMENTS`, `VIDEOS`, `AUDIO`, etc.
- File types are mapped via the config (`file_tidy_config.json`)
- You can undo everything using the **"Undo Last Operation"** button.

---

## 🔄 Undo Feature

Made a mistake?  
Click the **Undo Last Operation** button and all files will go back to where they were — as long as they weren’t changed or deleted.

---

## ⚙️ Customize File Categories

A config file (`file_tidy_config.json`) is auto-created the first time you run FileZen.

You can customize file type mappings like this:

```json
{
  "IMAGES": [".jpg", ".png"],
  "DOCUMENTS": [".pdf", ".docx", ".txt"],
  "VIDEOS": [".mp4", ".avi"]
}
```

Add or remove categories and extensions however you like.

---

## 📁 File Structure

| File                    | Purpose                                       |
|-------------------------|-----------------------------------------------|
| `file_organizer.py`     | Main script (runs the GUI & file logic)       |
| `file_tidy_config.json` | (Auto-generated) Extension mappings           |
| `file_tidy_log.json`    | (Auto-generated) Log of moved files           |
| `file_tidy_undo.json`   | (Auto-generated) Stores undo operation info   |

---

## 💡 Future Enhancements

- ⏳ Progress bar while organizing
- 🌙 Dark mode
- 🗂️ Exclude specific folders
- 📦 Drag-and-drop support

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Feel free to use, modify, and share!

---

## 🙌 Author

Made with ❤️ by VikkyTech  
