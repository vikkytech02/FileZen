import os
import io
import hashlib
import shutil
from collections import defaultdict
from datetime import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None


# ---------------- Worker Thread ----------------
class ScanWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(dict)
    cancelled = QtCore.pyqtSignal()

    def __init__(self, folder, recursive=True):
        super().__init__()
        self.folder = folder
        self.recursive = recursive
        self._cancel = False

    def run(self):
        hash_map = defaultdict(list)
        all_files = []
        # collect file list first
        if self.recursive:
            for root, _, files in os.walk(self.folder):
                for f in files:
                    all_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(self.folder):
                full = os.path.join(self.folder, f)
                if os.path.isfile(full):
                    all_files.append(full)

        total = len(all_files)
        for idx, path in enumerate(all_files, 1):
            if self._cancel:
                self.cancelled.emit()
                return
            try:
                h = self.hash_file(path)
                if h:
                    hash_map[h].append(path)
            except Exception:
                pass
            self.progress.emit(idx, total)

        self.finished.emit(hash_map)

    def hash_file(self, path):
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def cancel(self):
        self._cancel = True


# ---------------- Main App ----------------
class FileZen(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileZen – Duplicate Finder")
        self.resize(1000, 650)

        self.hash_map = defaultdict(list)
        self.groups = []
        self.keep_selection = {}
        self.scan_root = None
        self.worker = None

        main = QtWidgets.QHBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(10)

        self.group_list = QtWidgets.QListWidget()
        self.group_list.setFixedWidth(240)
        self.group_list.itemSelectionChanged.connect(self.load_group)
        self.group_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #DDDDDD;
                border: 1px solid #333;
                font-size: 13px;
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        main.addWidget(self.group_list)

        right_v = QtWidgets.QVBoxLayout()
        main.addLayout(right_v)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Keep", "File Name", "Size (KB)", "Path"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.table.itemSelectionChanged.connect(self.preview_file)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                color: #DDDDDD;
                gridline-color: #333;
                selection-background-color: #007ACC;
            }
            QHeaderView::section {
                background-color: #333;
                color: #CCCCCC;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
        """)
        right_v.addWidget(self.table)

        self.preview_label = QtWidgets.QLabel("Preview will appear here.")
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setFixedHeight(260)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                color: #BBBBBB;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        right_v.addWidget(self.preview_label)

        # Buttons row
        btn_h = QtWidgets.QHBoxLayout()

        self.include_sub = QtWidgets.QCheckBox("Include Subfolders")
        self.include_sub.setChecked(True)
        self.include_sub.setStyleSheet("color: #CCCCCC; font-size: 13px;")

        self.btn_scan = QtWidgets.QPushButton("📂  Scan Folder")
        self.btn_scan.clicked.connect(self.scan_folder)

        self.btn_auto = QtWidgets.QPushButton("🕒  Auto-Select Latest")
        self.btn_auto.clicked.connect(self.auto_select_latest)

        self.btn_move = QtWidgets.QPushButton("📦  Move Duplicates")
        self.btn_move.clicked.connect(self.move_duplicates)

        for btn in (self.btn_scan, self.btn_auto, self.btn_move):
            btn.setFixedHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #0A84FF;
                }
            """)

        btn_h.addWidget(self.btn_scan)
        btn_h.addWidget(self.include_sub)
        btn_h.addWidget(self.btn_auto)
        btn_h.addWidget(self.btn_move)
        right_v.addLayout(btn_h)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        app = QtWidgets.QApplication.instance()
        app.setStyle("Fusion")
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Window, QtGui.QColor(30, 30, 30))
        p.setColor(QtGui.QPalette.WindowText, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        p.setColor(QtGui.QPalette.Text, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 45))
        p.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 122, 204))
        app.setPalette(p)

    def human_size_kb(self, path):
        try:
            return round(os.path.getsize(path) / 1024, 2)
        except Exception:
            return 0.0

    # ---------------- scanning ----------------
    def scan_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder to scan")
        if not folder:
            return

        recursive = self.include_sub.isChecked()
        self.scan_root = folder
        self.hash_map.clear()
        self.groups = []
        self.group_list.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.preview_label.setText("Preview will appear here.")

        # Progress dialog
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Scanning in progress...")
        dlg.setModal(True)
        dlg.resize(400, 120)
        dlg.setStyleSheet("""
            QDialog { background-color: #2D2D2D; color: #DDDDDD; border-radius: 8px; }
            QLabel { color: #CCCCCC; }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #0A84FF; }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                background-color: #1E1E1E;
            }
            QProgressBar::chunk { background-color: #007ACC; width: 10px; }
        """)

        vbox = QtWidgets.QVBoxLayout(dlg)
        label = QtWidgets.QLabel("Preparing to scan...")
        progress = QtWidgets.QProgressBar()
        progress.setRange(0, 100)
        cancel_btn = QtWidgets.QPushButton("Cancel")

        vbox.addWidget(label)
        vbox.addWidget(progress)
        vbox.addWidget(cancel_btn)

        self.worker = ScanWorker(folder, recursive)
        self.worker.progress.connect(lambda i, total: (
            progress.setValue(int(i / total * 100) if total else 0),
            label.setText(f"Scanning {i} / {total} files...")
        ))
        self.worker.finished.connect(lambda result: (dlg.accept(), self.on_scan_complete(result)))
        self.worker.cancelled.connect(lambda: dlg.reject())

        cancel_btn.clicked.connect(lambda: self.worker.cancel())
        self.worker.start()
        dlg.exec_()

    def on_scan_complete(self, result):
        self.hash_map = result
        self.groups = [(h, sorted(paths, key=lambda p: os.path.getmtime(p))) for h, paths in result.items() if len(paths) > 1]

        for idx, (h, files) in enumerate(self.groups, 1):
            ext = os.path.splitext(files[0])[1].upper() or "FILE"
            item = QtWidgets.QListWidgetItem(f"{ext} Group {idx} ({len(files)})")
            item.setData(QtCore.Qt.UserRole, h)
            self.group_list.addItem(item)

        QtWidgets.QMessageBox.information(self, "Scan complete", f"Found {len(self.groups)} duplicate groups.")

    # ---------------- group handling ----------------
    def load_group(self):
        sel = self.group_list.currentItem()
        if not sel:
            return
        file_hash = sel.data(QtCore.Qt.UserRole)
        files = self.hash_map.get(file_hash, [])

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for r, path in enumerate(files):
            self.table.insertRow(r)
            chk_item = QtWidgets.QTableWidgetItem()
            chk_item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            keep_path = self.keep_selection.get(file_hash)
            chk_item.setCheckState(QtCore.Qt.Checked if keep_path == path else QtCore.Qt.Unchecked)
            self.table.setItem(r, 0, chk_item)

            name_item = QtWidgets.QTableWidgetItem(os.path.basename(path))
            size_item = QtWidgets.QTableWidgetItem(str(self.human_size_kb(path)))
            path_item = QtWidgets.QTableWidgetItem(path)
            path_item.setFlags(path_item.flags() & ~QtCore.Qt.ItemIsEditable)

            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, size_item)
            self.table.setItem(r, 3, path_item)
        self.table.blockSignals(False)

    def on_table_item_changed(self, item):
        if item.column() != 0:
            return
        sel = self.group_list.currentItem()
        if not sel:
            return
        file_hash = sel.data(QtCore.Qt.UserRole)
        path = self.table.item(item.row(), 3).text()
        if item.checkState() == QtCore.Qt.Checked:
            for r in range(self.table.rowCount()):
                if r != item.row():
                    other = self.table.item(r, 0)
                    if other and other.checkState() == QtCore.Qt.Checked:
                        other.setCheckState(QtCore.Qt.Unchecked)
            self.keep_selection[file_hash] = path
        elif self.keep_selection.get(file_hash) == path:
            self.keep_selection.pop(file_hash, None)

    # ---------------- auto select ----------------
    def auto_select_latest(self):
        for h, files in self.groups:
            if not files:
                continue
            latest = max(files, key=lambda p: os.path.getmtime(p))
            self.keep_selection[h] = latest
        self.load_group()
        QtWidgets.QMessageBox.information(self, "Auto-Select Done", "Latest files have been auto-selected.")

    # ---------------- preview ----------------
    def preview_file(self):
        row = self.table.currentRow()
        if row < 0:
            self.preview_label.setText("Preview will appear here.")
            return
        path = self.table.item(row, 3).text()
        if not os.path.exists(path):
            self.preview_label.setText("File not found.")
            return

        ext = os.path.splitext(path)[1].lower()
        self.preview_label.clear()

        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"):
            try:
                img = Image.open(path).convert("RGBA")
                preview_w = max(200, self.preview_label.width() - 20)
                preview_h = max(120, self.preview_label.height() - 20)
                img.thumbnail((preview_w, preview_h), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                qimg = QtGui.QImage.fromData(buf.getvalue())
                pix = QtGui.QPixmap.fromImage(qimg)
                scaled = pix.scaled(preview_w, preview_h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
            except Exception as e:
                self.preview_label.setText(f"Image preview error: {e}")
        elif ext in (".txt", ".py", ".md", ".csv", ".log"):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(2000)
                self.preview_label.setText(text or "(empty file)")
            except Exception as e:
                self.preview_label.setText(f"Text preview error: {e}")
        elif ext == ".pdf":
            if PyPDF2:
                try:
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        if reader.pages:
                            text = reader.pages[0].extract_text() or ""
                            self.preview_label.setText(text[:2000] or "(no extractable text)")
                        else:
                            self.preview_label.setText("(empty PDF)")
                except Exception as e:
                    self.preview_label.setText(f"PDF preview error: {e}")
        elif ext == ".docx" and docx:
            try:
                d = docx.Document(path)
                paragraphs = [p.text for p in d.paragraphs[:50]]
                self.preview_label.setText("\n".join(paragraphs) or "(no text found)")
            except Exception as e:
                self.preview_label.setText(f"DOCX preview error: {e}")
        else:
            self.preview_label.setText("Preview not supported for this file type.")

    # ---------------- move duplicates ----------------
    def move_duplicates(self):
        if not self.scan_root:
            QtWidgets.QMessageBox.warning(self, "No scan", "Please scan a folder first.")
            return
    
        dup_root = os.path.join(self.scan_root, "Duplicate_Files")
        os.makedirs(dup_root, exist_ok=True)
    
        moved, errors = 0, []
    
        for h, files in self.groups:
            keeps = [self.keep_selection.get(h)] if h in self.keep_selection else [max(files, key=lambda p: os.path.getmtime(p))]
            for f in files:
                if f in keeps:
                    continue
                dst = os.path.join(dup_root, os.path.basename(f))
                base, ext = os.path.splitext(dst)
                i = 1
                while os.path.exists(dst):
                    dst = f"{base}__dup{i}{ext}"
                    i += 1
                try:
                    shutil.move(f, dst)
                    moved += 1
                except Exception as e:
                    errors.append((f, str(e)))
    
        # UI cleanup
        self.hash_map.clear()
        self.groups.clear()
        self.keep_selection.clear()
        self.scan_root = None
        self.group_list.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.preview_label.setPixmap(QtGui.QPixmap())
        self.preview_label.setText("Preview will appear here.")
    
        # Toast message (auto close in 2 sec)
        toast = QtWidgets.QDialog(self)
        toast.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        toast.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        toast_layout = QtWidgets.QVBoxLayout(toast)
    
        msg = QtWidgets.QLabel(f"✅ Moved {moved} duplicate file(s) successfully!")
        msg.setStyleSheet("""
            background-color: #4caf50;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
        """)
        toast_layout.addWidget(msg)
    
        toast.adjustSize()
        x = self.geometry().center().x() - toast.width() // 2
        y = self.geometry().center().y() - 50
        toast.move(x, y)
        toast.show()
    
        # Auto close after 2 seconds
        QtCore.QTimer.singleShot(2000, toast.close)
    
        if errors:
            print("Move errors:", errors)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = FileZen()
    w.show()
    sys.exit(app.exec_())
