# filezen.py
import os
import shutil
import json
import joblib
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ======== DEFAULT CATEGORIES ========
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

CONFIG_FILE = "file_tidy_config.json"
LOG_FILE = "file_tidy_log.json"
UNDO_FILE = "file_tidy_undo.json"
REVIEW_LOG = "file_tidy_review.json"
MODEL_FILE = "filezen_model.pkl"

# ======== CONFIG ========
DEFAULT_CONFIG = {
    "confidence_threshold": 0.75,
    "review_folder_name": "REVIEW",
    "model_file": MODEL_FILE
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    else:
        return DEFAULT_CONFIG.copy()

config = load_config()

# ======== LOAD MODEL ========
ml_model = None
if os.path.exists(config["model_file"]):
    try:
        ml_model = joblib.load(config["model_file"])
        print("[INFO] Loaded ML model:", config["model_file"])
    except Exception as e:
        print("[WARN] Failed to load model:", e)
else:
    print("[INFO] No model found. Running rule-based only.")

# ======== UTIL ========
def _unique_target(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path
    base = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    i = 1
    while True:
        candidate = parent / f"{base}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def move_file_safe(src: Path, dest: Path):
    dest = _unique_target(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return dest

def predict_category(file_path: Path):
    if ml_model is None:
        return None, 0.0
    data = pd.DataFrame([{
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
        "size": file_path.stat().st_size
    }])
    try:
        proba = ml_model.predict_proba(data)[0]
        pred = ml_model.predict(data)[0]
        conf = float(proba.max())
        return pred, conf
    except Exception as e:
        print("[ML ERROR]", e)
        return None, 0.0

# ======== ORGANIZE FILES ========
def organize_files(directory, dry_run=False, confidence_threshold=None):
    if confidence_threshold is None:
        confidence_threshold = config["confidence_threshold"]

    file_formats = {ext: cat for cat, exts in DEFAULT_DIRECTORIES.items() for ext in exts}
    files_moved = {}
    review_entries = {}
    dry_run_results = []

    review_folder = Path(directory) / config["review_folder_name"]

    moved_count = 0
    skipped_count = 0
    review_count = 0

    for entry in os.scandir(directory):
        if entry.is_dir():
            continue
        file_path = Path(entry.path)
        ext = file_path.suffix.lower()

        # Determine category
        if ext in file_formats:
            category = file_formats[ext]
            conf = 1.0
            reason = "rule"
        else:
            predicted, conf = predict_category(file_path)
            if predicted is None:
                category = "Unsorted"
                reason = "no_model"
            else:
                if conf >= confidence_threshold:
                    category = predicted
                    reason = "ml_confident"
                else:
                    category = None
                    reason = "ml_low_confidence"

        # Review or Move
        if category is None:
            target_dir = review_folder
            new_path = target_dir / file_path.name
            review_count += 1
            if not dry_run:
                new_path = move_file_safe(file_path, new_path)
                review_entries[str(file_path)] = {
                    "review_path": str(new_path),
                    "predicted": predicted,
                    "confidence": conf,
                    "time": datetime.now().isoformat()
                }
            else:
                dry_run_results.append((file_path.name, str(new_path), f"{conf:.2f}"))
            continue

        target_dir = Path(directory) / category
        new_path = target_dir / file_path.name
        if dry_run:
            dry_run_results.append((file_path.name, str(new_path), f"{conf:.2f}"))
        else:
            moved_to = move_file_safe(file_path, new_path)
            files_moved[str(file_path)] = str(moved_to)
            moved_count += 1

    # Save logs only for real move
    if not dry_run:
        if files_moved:
            op = {"time": datetime.now().isoformat(), "moves": files_moved}
            data = []
            if os.path.exists(LOG_FILE):
                try:
                    data = json.load(open(LOG_FILE))
                except:
                    pass
            data.append(op)
            with open(LOG_FILE, "w") as f:
                json.dump(data, f, indent=2)
            with open(UNDO_FILE, "w") as f:
                json.dump(op, f, indent=2)

        if review_entries:
            existing = []
            if os.path.exists(REVIEW_LOG):
                try:
                    existing = json.load(open(REVIEW_LOG))
                except:
                    pass
            existing.extend([{"original_path": k, **v} for k, v in review_entries.items()])
            with open(REVIEW_LOG, "w") as f:
                json.dump(existing, f, indent=2)

    summary = {
        "moved": moved_count,
        "skipped": skipped_count,
        "review": review_count
    }

    if dry_run:
        return dry_run_results, summary
    else:
        return None, summary

# ======== UNDO ========
def undo_last_operation():
    if not os.path.exists(UNDO_FILE):
        messagebox.showinfo("Undo", "No undo information found.")
        return
    with open(UNDO_FILE) as f:
        op = json.load(f)
    moves = op.get("moves", {})
    for src, dst in moves.items():
        if os.path.exists(dst):
            try:
                move_file_safe(Path(dst), Path(src))
            except Exception as e:
                print("Failed to move back", dst, "->", src, e)
    os.remove(UNDO_FILE)
    messagebox.showinfo("Undo", "Undo completed.")

# ======== GUI ========
class FileZenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FileZen — Rule + ML Hybrid")
        self.root.geometry("600x420")
        self.dark_theme = tk.BooleanVar(value=False)
        self.conf_val = tk.DoubleVar(value=config["confidence_threshold"])
        self.dry_run_enabled = tk.BooleanVar(value=True)
        self.setup_ui()
    
    def open_duplicate_finder(self, button):
        """Open the Duplicate Finder tool and disable the button while it's running."""
        import subprocess
        button.config(state="disabled")

        process = subprocess.Popen(["python", "filezen_duplicate_finder.py"])

        def check_process():
            if process.poll() is None:
                button.after(1000, check_process)
            else:
                button.config(state="normal")

        check_process()

    def setup_ui(self):
        self.apply_theme()

        # ===== Title =====
        ttk.Label(self.root, text="FileZen — Hybrid Organizer",
                  font=("Arial", 16, "bold")).pack(pady=(15, 10))

        # ===== Confidence Frame =====
        conf_frame = ttk.LabelFrame(self.root, text="ML Confidence Settings", padding=10)
        conf_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(conf_frame, text="Confidence Threshold:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        slider = ttk.Scale(conf_frame, from_=0.0, to=1.0, orient="horizontal",
                           variable=self.conf_val, command=self.update_conf_label)
        slider.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        conf_frame.columnconfigure(1, weight=1)
        self.conf_label = ttk.Label(conf_frame, text=f"{self.conf_val.get():.2f}", width=5, anchor="center")
        self.conf_label.grid(row=0, column=2, padx=5, pady=5)

        # ===== Controls =====
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.btn_organize = ttk.Button(btn_frame, text="Organize Files", command=self.on_organize_click)
        self.btn_undo = ttk.Button(btn_frame, text="Undo Last Operation", command=undo_last_operation)
        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=self.root.quit)

        for i, btn in enumerate([self.btn_organize, self.btn_undo, self.btn_exit]):
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            btn_frame.columnconfigure(i, weight=1)

        # ===== Options =====
        options_frame = ttk.Frame(self.root)
        options_frame.pack(fill="x", padx=20, pady=(5, 15))

        ttk.Checkbutton(options_frame, text="Dry Run Preview", variable=self.dry_run_enabled,
                        command=self.on_preview_toggle).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(options_frame, text="Dark Theme", variable=self.dark_theme,
                        command=self.apply_theme).grid(row=0, column=1, padx=5, pady=5, sticky="e")
        find_duplicates_button = ttk.Button(options_frame, text="Find Duplicates",command=lambda: self.open_duplicate_finder(find_duplicates_button))
        find_duplicates_button.grid(row=0, column=2, padx=10, pady=5)

    def apply_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        if self.dark_theme.get():
            self.root.configure(bg="#2e2e2e")
            # Labels / Frames
            style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
            style.configure("TFrame", background="#2e2e2e")
            style.configure("TLabelframe", background="#2e2e2e", foreground="#ffffff")
            style.configure("TLabelframe.Label", background="#2e2e2e", foreground="#ffffff")
            # Buttons
            style.configure("TButton", background="#444444", foreground="#ffffff", padding=6, relief="flat")
            style.map("TButton",
                      background=[("active", "#666666")],
                      foreground=[("active", "#ffffff")])
            # Checkbuttons (✔ fixed hover readability)
            style.configure("TCheckbutton", background="#2e2e2e", foreground="#ffffff")
            style.map("TCheckbutton",
                      background=[("active", "#2e2e2e")],
                      foreground=[("active", "#ffffff"),
                                  ("selected", "#ffffff"),
                                  ("!selected", "#ffffff")])
            # Treeview
            style.configure("Treeview",
                            background="#333333",
                            foreground="#ffffff",
                            fieldbackground="#333333",
                            bordercolor="#444444",
                            borderwidth=1)
            style.map("Treeview",
                      background=[("selected", "#555555")],
                      foreground=[("selected", "#ffffff")])
        else:
            self.root.configure(bg="#f0f0f0")
            style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabelframe", background="#f0f0f0", foreground="#000000")
            style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#000000")

            style.configure("TButton", background="#e0e0e0", foreground="#000000", padding=6, relief="flat")
            style.map("TButton", background=[("active", "#c0c0c0")], foreground=[("active", "#000000")])

            style.configure("TCheckbutton", background="#f0f0f0", foreground="#000000")

            style.configure("Treeview", background="#ffffff", foreground="#000000",
                            fieldbackground="#ffffff", bordercolor="#cccccc", borderwidth=1)
            style.map("Treeview", background=[("selected", "#c0c0c0")], foreground=[("selected", "#000000")])

    def update_conf_label(self, val):
        self.conf_label.config(text=f"{float(val):.2f}")

    def on_organize_click(self):
        directory = filedialog.askdirectory()
        if not directory:
            return

        dry_run = self.dry_run_enabled.get()
        logs, summary = organize_files(directory, dry_run=dry_run, confidence_threshold=self.conf_val.get())

        if dry_run:
            if not logs:
                messagebox.showinfo("Dry Run", "No files to preview.")
            else:
                self.show_preview(logs)
        else:
            messagebox.showinfo(
                "Organization Complete",
                f"Files organized successfully!\n\n"
                f"Moved: {summary.get('moved', 0)}\n"
                f"Skipped: {summary.get('skipped', 0)}\n"
                f"Review: {summary.get('review', 0)}"
            )
            self.conf_val.set(config["confidence_threshold"])
            self.dry_run_enabled.set(True)
            self.apply_theme()
            self.root.update_idletasks()

    def show_preview(self, logs):
        preview = tk.Toplevel(self.root)
        preview.title("Dry Run Preview")
        preview.geometry("700x400")

        columns = ("Filename", "Target", "Confidence")
        tree = ttk.Treeview(preview, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=220, anchor="w")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for row in logs:
            tree.insert("", "end", values=row)

        summary = ttk.Label(preview,
                            text=f"Total files: {len(logs)} | Files in REVIEW: {sum(1 for x in logs if config['review_folder_name'] in x[1])}")
        summary.pack(pady=5)

    def on_preview_toggle(self):
        if self.dry_run_enabled.get():
            messagebox.showinfo("Mode", "Dry Run mode enabled — files will not actually move.")
        else:
            messagebox.showinfo("Mode", "Dry Run mode disabled — files will be organized for real.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileZenApp(root)
    root.mainloop()
