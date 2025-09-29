import os
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ===== Dummy ML Prediction (replace with real model) =====
def predict_category(file_path):
    # Example stub: put real ML model inference here
    name = file_path.name.lower()
    if name.endswith(".jpg") or name.endswith(".png"):
        return "Images", 0.92
    elif name.endswith(".pdf") or name.endswith(".docx"):
        return "Documents", 0.88
    else:
        return None, 0.40

# ===== Config =====
CONFIG_FILE = "config.json"
LOG_FILE = "log.json"
UNDO_FILE = "undo.json"
REVIEW_LOG = "review_log.json"

config = {
    "confidence_threshold": 0.75,
    "review_folder_name": "Review"
}

DEFAULT_DIRECTORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt"],
    "Videos": [".mp4", ".avi", ".mov"],
    "Music": [".mp3", ".wav"],
}


# ===== Helpers =====
def move_file_safe(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    counter = 1
    new_dst = dst
    while new_dst.exists():
        new_dst = dst.with_stem(f"{dst.stem}_{counter}")
        counter += 1
    src.replace(new_dst)
    return new_dst


# ===== Core Organize Logic =====
def organize_files(directory, dry_run=False, confidence_threshold=0.75):
    file_formats = {ext: category for category, exts in DEFAULT_DIRECTORIES.items() for ext in exts}
    files_moved = {}
    review_entries = {}
    summary = {"moved": 0, "review": 0}

    review_folder = Path(directory) / config["review_folder_name"]

    for entry in os.scandir(directory):
        if entry.is_dir():
            continue

        file_path = Path(entry.path)
        ext = file_path.suffix.lower()

        if ext in file_formats:
            category = file_formats[ext]
            reason = "rule"
            conf = 1.0
        else:
            predicted, conf = predict_category(file_path)
            if predicted is None:
                category = "Unsorted"
                reason = "no_model"
            elif conf >= confidence_threshold:
                category = predicted
                reason = "ml_confident"
            else:
                category = None
                reason = "ml_low_confidence"

        if category is None:
            target_dir = review_folder
            new_path = target_dir / file_path.name
            if not dry_run:
                new_path = move_file_safe(file_path, new_path)
                review_entries[str(file_path)] = {
                    "review_path": str(new_path),
                    "predicted": predicted,
                    "confidence": conf,
                    "time": datetime.now().isoformat()
                }
                summary["review"] += 1
            continue

        target_dir = Path(directory) / category
        new_path = target_dir / file_path.name
        if not dry_run:
            moved_to = move_file_safe(file_path, new_path)
            files_moved[str(file_path)] = str(moved_to)
            summary["moved"] += 1

    # Save logs
    if not dry_run and files_moved:
        op = {"time": datetime.now().isoformat(), "moves": files_moved}
        if os.path.exists(LOG_FILE):
            try:
                data = json.load(open(LOG_FILE))
            except:
                data = []
        else:
            data = []
        data.append(op)
        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        with open(UNDO_FILE, "w") as f:
            json.dump(op, f, indent=2)

    if not dry_run and review_entries:
        if os.path.exists(REVIEW_LOG):
            try:
                existing = json.load(open(REVIEW_LOG))
            except:
                existing = []
        else:
            existing = []
        existing.extend([{"original_path": k, **v} for k, v in review_entries.items()])
        with open(REVIEW_LOG, "w") as f:
            json.dump(existing, f, indent=2)

    # Logs for dry run (preview)
    logs = []
    if dry_run:
        for file_path in files_moved.keys():
            logs.append((Path(file_path).name, files_moved[file_path], 1.0))
        for file_path, v in review_entries.items():
            logs.append((Path(file_path).name, "Review Folder", v["confidence"]))

    return logs if dry_run else summary


def undo_last_operation():
    if not os.path.exists(UNDO_FILE):
        messagebox.showinfo("Undo", "No last operation found.")
        return
    with open(UNDO_FILE, "r") as f:
        last_op = json.load(f)
    for src, dst in last_op["moves"].items():
        src_p = Path(src)
        dst_p = Path(dst)
        if dst_p.exists():
            move_file_safe(dst_p, src_p)
    messagebox.showinfo("Undo", "Last operation reverted.")


# ===== GUI =====
class FileZenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FileZen — Rule + ML Hybrid")
        self.root.geometry("650x460")
        self.dark_theme = tk.BooleanVar(value=False)
        self.conf_val = tk.DoubleVar(value=config["confidence_threshold"])
        self.dry_run_var = tk.BooleanVar(value=False)
        self.setup_ui()

    def setup_ui(self):
        self.apply_theme()

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

        ttk.Checkbutton(options_frame, text="Dry Run Preview", variable=self.dry_run_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(options_frame, text="Dark Theme", variable=self.dark_theme,
                        command=self.apply_theme).grid(row=0, column=1, padx=5, pady=5, sticky="e")

    def update_conf_label(self, val):
        self.conf_label.config(text=f"{float(val):.2f}")

    def on_organize_click(self):
        directory = filedialog.askdirectory()
        if not directory:
            return

        dry_run = self.dry_run_var.get()
        logs_or_summary = organize_files(directory, dry_run=dry_run, confidence_threshold=self.conf_val.get())

        if dry_run:
            if not logs_or_summary:
                messagebox.showinfo("Dry Run", "No files to organize.")
                return
            self.show_preview(logs_or_summary)
        else:
            moved = logs_or_summary["moved"]
            review = logs_or_summary["review"]
            messagebox.showinfo("Organize",
                                f"Files organized successfully in:\n{directory}\n\n"
                                f"Summary:\n - {moved} moved\n - {review} sent to Review")

    def show_preview(self, logs):
        preview = tk.Toplevel(self.root)
        preview.title("Dry Run Preview")
        preview.geometry("600x400")

        cols = ("Filename", "Target", "Confidence")
        tree = ttk.Treeview(preview, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="w", width=180 if col != "Confidence" else 100)

        for fname, target, conf in logs:
            tree.insert("", "end", values=(fname, target, f"{conf:.2f}"))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

    def apply_theme(self):
        style = ttk.Style(self.root)
        if self.dark_theme.get():
            self.root.configure(bg="#2b2b2b")
            style.theme_use("clam")
            style.configure("TLabel", background="#2b2b2b", foreground="white")
            style.configure("TButton", background="#444", foreground="white")
            style.map("TButton",
                      background=[("active", "#666")],
                      foreground=[("active", "white")])
            style.configure("TCheckbutton", background="#2b2b2b", foreground="white")
            style.configure("TLabelFrame", background="#2b2b2b", foreground="white")
        else:
            self.root.configure(bg="SystemButtonFace")
            style.theme_use("clam")
            style.configure("TLabel", background="SystemButtonFace", foreground="black")
            style.configure("TButton", background="SystemButtonFace", foreground="black")
            style.map("TButton",
                      background=[("active", "#e0e0e0")],
                      foreground=[("active", "black")])
            style.configure("TCheckbutton", background="SystemButtonFace", foreground="black")
            style.configure("TLabelFrame", background="SystemButtonFace", foreground="black")


# ===== Run GUI =====
def start_gui():
    root = tk.Tk()
    app = FileZenApp(root)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
