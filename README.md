# 📂 FileZen — Intelligent File Organizer

FileZen is a **hybrid file organizer** that combines **rule-based sorting** with an **ML-powered classifier** to keep your directories neat and clean.  
It automatically organizes files into categories (Documents, Images, Audio, Video, etc.) and sends uncertain predictions to a **Review folder**.

---

## ✨ Features

- 🔹 **Rule + ML Hybrid** → uses file extensions & ML predictions  
- 🔹 **Dry Run Preview** → table view of (filename / target / confidence) before moving files  
- 🔹 **Confidence Threshold Control** → slider to adjust ML certainty level  
- 🔹 **Review System** → low-confidence files are sent to a dedicated `Review` folder  
- 🔹 **Undo Last Operation** → revert last file move with one click  
- 🔹 **Logs** → all operations saved (`log.json`, `undo.json`, `review_log.json`)  
- 🔹 **Dark/Light Theme** → toggleable modern UI  
- 🔹 **Summary Report** → shows how many files were moved vs. sent to review  

---

## 🖥️ GUI Preview

### Light Mode
![Light Mode Screenshot](assets/light_mode.png)

### Dark Mode
![Dark Mode Screenshot](assets/dark_mode.png)

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/filezen.git
cd filezen

# 2. (Optional) Create a virtual environment
python -m venv filezen
source filezen/bin/activate   # Linux/Mac
filezen\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** `tkinter` usually comes with Python, but if missing, install via your package manager.

---

## 🚀 Usage

Run FileZen with:

```bash
python filezen.py
```

### Modes

- **Dry Run Preview** → See how files will be organized before actually moving them  
- **Organize Files** → Moves files into category folders  
- **Undo** → Restores last moved files to their original locations  

---

## 📂 Project Structure

```
filezen/
├── filezen.py          # Main application
├── config.json         # Custom rules (if exists)
├── log.json            # History of operations
├── undo.json           # Last operation (for undo)
├── review_log.json     # Files sent to Review folder
├── requirements.txt    # Dependencies
└── assets/             # Screenshots for README
```

---

## 🧠 ML Model

- The ML classifier is trained on a dataset of file extensions and their categories  
- Predictions are used when the file extension is unknown  
- Low-confidence predictions (below threshold) go into the **Review folder**  

---

## 🛠️ Tech Stack

- **Python 3.10+**  
- **Tkinter** → GUI  
- **scikit-learn** → ML model  
- **joblib** → Model persistence  
- **pandas** → Data handling  

---

## 📜 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute.

---

## 💡 Future Enhancements

- [ ] Log Viewer Tab inside GUI  
- [ ] Drag & Drop support  
- [ ] More granular ML categories (sub-categories for code, media, etc.)  
- [ ] Cross-platform installer  

---

👨‍💻 Developed with ❤️ by **Vikas Yadav**
