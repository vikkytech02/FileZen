# create_dataset.py
import os
import pandas as pd
from pathlib import Path

DEFAULT_DIRECTORIES = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".odt", ".rtf", ".md"],
    "Spreadsheets": [".xlsx", ".xls", ".ods", ".csv"],
    "Presentations": [".pptx", ".ppt", ".odp"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Video": [".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm"],
    "Compressed/Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"],
    "Code Files": [".py", ".java", ".cpp", ".c", ".js", ".ts", ".html", ".html5", ".htm", ".xhtml", ".css", ".php", ".cs", ".rb", ".swift", ".go", ".rs", ".kt", ".sh", ".sql", ".ipynb"],
    "Executables": [".exe", ".msi", ".bin", ".app", ".deb", ".rpm", ".dmg"],
    "System/Config": [".ini", ".log", ".cfg", ".conf", ".yaml", ".yml", ".json", ".xml"],
    "Database Files": [".db", ".sqlite", ".mdb", ".accdb", ".frm", ".myd", ".ibd"]
}

def create_training_data(base_dir):
    data = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            path = Path(root) / file
            ext = path.suffix.lower()

            # label by extension (only files that match DEFAULT_DIRECTORIES)
            cat = None
            for k, exts in DEFAULT_DIRECTORIES.items():
                if ext in exts:
                    cat = k
                    break
            if cat:
                data.append({
                    "filename": file,
                    "extension": ext,
                    "size": path.stat().st_size,
                    "category": cat
                })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    base = input("Path to folder with labeled files: ").strip()
    df = create_training_data(base)
    if df.empty:
        print("No labeled files found.")
    else:
        out = "training_data-1.csv"
        df.to_csv(out, index=False)
        print(f"Saved {len(df)} rows to {out}")
