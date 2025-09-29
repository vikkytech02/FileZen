import csv
import random

categories = {
    "Audio": ["mp3", "wav", "aac", "flac", "ogg"],
    "Video": ["mp4", "avi", "mkv", "mov", "wmv"],
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "webp"],
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md"],
    "Presentations": ["ppt", "pptx", "key", "odp"],
    "Spreadsheets": ["xls", "xlsx", "csv", "ods"],
    "Code Files": ["c", "cpp", "java", "js", "py", "php", "html", "css", "rb", "go", "ts", "cs", "swift"],
    "Database Files": ["db", "sql", "sqlite", "mdb", "accdb", "db3"],
    "Executables": ["exe", "msi", "bin", "sh", "bat", "apk", "app"],
    "System/Config": ["ini", "cfg", "conf", "sys", "log", "yml", "yaml", "toml", "json", "xml"],
    "Compressed/Archives": ["zip", "rar", "7z", "tar", "gz", "bz2"],
    "Unknown/No Extension": ["UNKNOWN"],  # ✅ fixed: no empty string
}

# Special extensionless realistic names
extensionless_examples = {
    "Documents": ["README", "LICENSE", "CHANGELOG", "Notes", "todo"],
    "System/Config": ["Dockerfile", "Makefile", "hosts", "fstab", "shadow"],
    "Code Files": ["CMakeLists", "Makefile"],
    "Unknown/No Extension": ["tempfile", "randomfile", "untitled", "newfile", "datafile"]
}

prefixes = ["project", "backup", "assignment", "holiday", "report", "setup",
            "notes", "config", "user", "sample", "work", "photo", "music", "video"]
suffixes = ["2023", "v1", "final", "draft", "01", "test", "prod", "log",
            "media", "archive", "copy", "backup", "temp"]

def add_noise(name: str) -> str:
    """Add casing variation, typos, and random symbols."""
    if random.random() < 0.3:
        name = name.upper()
    elif random.random() < 0.3:
        name = name.capitalize()

    if random.random() < 0.1 and len(name) > 3:
        idx = random.randint(0, len(name) - 2)
        name = name[:idx] + name[idx+1:]

    if random.random() < 0.1:
        name += random.choice(["~", "-", "_new", "_old"])

    return name

def generate_filename(extension, idx, category):
    if extension == "UNKNOWN":
        base = random.choice(extensionless_examples.get(category, ["file"]))
        return add_noise(f"{base}_{idx}")  # ✅ no extension
    else:
        base = f"{random.choice(prefixes)}_{random.choice(suffixes)}_{idx}"
        return add_noise(base) + "." + extension

rows = []
num_samples = 2000

for i in range(num_samples):
    category = random.choice(list(categories.keys()))
    extension = random.choice(categories[category])

    # Introduce mislabeled/mixed data (simulate messy real-world)
    if random.random() < 0.05:
        category = random.choice(list(categories.keys()))

    # Introduce unknown extensions
    if random.random() < 0.05:
        extension = random.choice(["bak", "tmp", "xyz", "abc", "zzz"])
        category = "Unknown/No Extension"  # ✅ map unknowns properly
        filename = generate_filename("UNKNOWN", i, category)
        rows.append([filename, extension, random.randint(500, 50_000_000), category])
        continue

    filename = generate_filename(extension, i, category)
    size = random.randint(500, 50_000_000)
    rows.append([filename, extension if extension != "UNKNOWN" else "", size, category])

with open("training_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "extension", "size", "category"])
    writer.writerows(rows)

print(f"✅ Generated {num_samples} realistic noisy samples in training_data.csv (with UNKNOWN fixed)")
