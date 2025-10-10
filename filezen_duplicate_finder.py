# filezen_duplicate_finder.py
# Dependencies: PyQt5, Pillow, PyPDF2 (optional), python-docx (optional)
# pip install PyQt5 Pillow PyPDF2 python-docx

import os
import io
import hashlib
import shutil
from collections import defaultdict
from datetime import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image

# Optional libraries for document preview
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None


class FileZen(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileZen – Duplicate Finder")
        self.resize(1000, 650)

        # Data stores
        self.hash_map = defaultdict(list)       # hash -> [paths]
        self.groups = []                        # list of (hash, [paths])
        self.keep_selection = {}                # hash -> keep_path
        self.scan_root = None

        # --- Layout ---
        main = QtWidgets.QHBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(10)

        # Sidebar - groups
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

        # Right side (table + preview + buttons)
        right_v = QtWidgets.QVBoxLayout()
        main.addLayout(right_v)

        # Table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Keep", "File Name", "Size (KB)", "Path"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.itemChanged.connect(self.on_table_item_changed)      # single connection
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
            QTableWidget::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #777;
                border-radius: 3px;
                background: #ccc;
            }
            QTableWidget::indicator:checked {
                background-color: #007ACC;
                border: 2px solid #ccc;
            }
            QTableWidget::indicator:unchecked:hover {
                background: #aaa;
            }
        """)
        
        right_v.addWidget(self.table)

        # Preview area
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
        self.btn_scan = QtWidgets.QPushButton("📂  Scan Folder")
        self.btn_scan.clicked.connect(self.scan_folder)
        self.btn_move = QtWidgets.QPushButton("📦  Move Duplicates")
        self.btn_move.clicked.connect(self.move_duplicates)
        for btn in (self.btn_scan, self.btn_move):
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
        btn_h.addWidget(self.btn_move)
        right_v.addLayout(btn_h)

        # Apply a simple dark Fusion theme for readability
        self.apply_dark_theme()

    # ---------------- utilities ----------------
    def apply_dark_theme(self):
        app = QtWidgets.QApplication.instance()
        if not app:
            return
        app.setStyle("Fusion")
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Window, QtGui.QColor(30, 30, 30))
        p.setColor(QtGui.QPalette.WindowText, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        p.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(35, 35, 35))
        p.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
        p.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(255, 255, 255))
        p.setColor(QtGui.QPalette.Text, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 45))
        p.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 122, 204))
        p.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
        app.setPalette(p)

    def human_size_kb(self, path):
        try:
            return round(os.path.getsize(path) / 1024, 2)
        except Exception:
            return 0.0

    def hash_file(self, path):
        try:
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    # ---------------- scanning ----------------
    def scan_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder to scan")
        if not folder:
            return

        self.scan_root = folder
        self.hash_map.clear()
        self.groups = []
        self.group_list.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.preview_label.setText("Preview will appear here.")

        # collect files recursively
        for root, _, files in os.walk(folder):
            for f in files:
                path = os.path.join(root, f)
                h = self.hash_file(path)
                if h:
                    self.hash_map[h].append(path)

        # build groups of duplicates, stable order by mtime (oldest -> newest)
        self.groups = [(h, sorted(paths, key=lambda p: os.path.getmtime(p))) for h, paths in self.hash_map.items() if len(paths) > 1]

        # populate sidebar
        for idx, (h, files) in enumerate(self.groups, 1):
            ext = os.path.splitext(files[0])[1].upper() or "FILE"
            item = QtWidgets.QListWidgetItem(f"{ext} Group {idx} ({len(files)})")
            item.setData(QtCore.Qt.UserRole, h)
            self.group_list.addItem(item)

        QtWidgets.QMessageBox.information(self, "Scan complete", f"Found {len(self.groups)} duplicate groups.")

    # ---------------- group handling ----------------
    def load_group(self):
        """Populate table for selected group and restore any saved keep selection."""
        sel = self.group_list.currentItem()
        if not sel:
            return
        file_hash = sel.data(QtCore.Qt.UserRole)
        files = self.hash_map.get(file_hash, [])

        # prevent itemChanged signals while populating
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for r, path in enumerate(files):
            self.table.insertRow(r)

            # Keep checkbox as QTableWidgetItem (user-checkable)
            chk_item = QtWidgets.QTableWidgetItem()
            chk_item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            # restore saved keep selection for this group if present
            keep_path = self.keep_selection.get(file_hash)
            chk_item.setCheckState(QtCore.Qt.Checked if keep_path == path else QtCore.Qt.Unchecked)
            self.table.setItem(r, 0, chk_item)

            name_item = QtWidgets.QTableWidgetItem(os.path.basename(path))
            size_item = QtWidgets.QTableWidgetItem(str(self.human_size_kb(path)))
            path_item = QtWidgets.QTableWidgetItem(path)
            # Path cell should not be editable
            path_item.setFlags(path_item.flags() & ~QtCore.Qt.ItemIsEditable)

            self.table.setItem(r, 1, name_item)
            self.table.setItem(r, 2, size_item)
            self.table.setItem(r, 3, path_item)

        self.table.blockSignals(False)
        # ensure any current selection cleared
        self.table.clearSelection()

    def on_table_item_changed(self, item):
        """Handle checkbox changes; ensure only one 'Keep' per group and persist selection."""
        if item is None or item.column() != 0:
            return

        # find current group
        sel = self.group_list.currentItem()
        if not sel:
            return
        file_hash = sel.data(QtCore.Qt.UserRole)

        # path cell at same row
        path_item = self.table.item(item.row(), 3)
        if not path_item:
            return
        path = path_item.text()

        if item.checkState() == QtCore.Qt.Checked:
            # uncheck others in the table
            for r in range(self.table.rowCount()):
                if r != item.row():
                    other = self.table.item(r, 0)
                    if other and other.checkState() == QtCore.Qt.Checked:
                        other.setCheckState(QtCore.Qt.Unchecked)
            # persist
            self.keep_selection[file_hash] = path
        else:
            # if unchecked and it was stored as kept, remove
            if self.keep_selection.get(file_hash) == path:
                self.keep_selection.pop(file_hash, None)

    # ---------------- preview ----------------
    def preview_file(self):
        # use currentRow for clarity
        row = self.table.currentRow()
        if row < 0:
            self.preview_label.setText("Preview will appear here.")
            return
        path_item = self.table.item(row, 3)
        if not path_item:
            self.preview_label.setText("No path.")
            return
        path = path_item.text()
        if not os.path.exists(path):
            self.preview_label.setText("File not found.")
            return

        ext = os.path.splitext(path)[1].lower()
        self.preview_label.clear()

        # IMAGE: Pillow -> PNG bytes -> QImage.fromData (reliable)
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"):
            try:
                img = Image.open(path).convert("RGBA")
                # Fit width to preview area with maintained aspect ratio
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

        # TEXT files
        elif ext in (".txt", ".py", ".md", ".csv", ".log"):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(2000)
                self.preview_label.setText(text or "(empty file)")
            except Exception as e:
                self.preview_label.setText(f"Text preview error: {e}")

        # PDF
        elif ext == ".pdf":
            if PyPDF2 is None:
                self.preview_label.setText("Install PyPDF2 for PDF preview (pip install PyPDF2).")
                return
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

        # DOCX
        elif ext == ".docx":
            if docx is None:
                self.preview_label.setText("Install python-docx for DOCX preview (pip install python-docx).")
                return
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

        # Destination inside scanned folder
        dup_root = os.path.join(self.scan_root, "Duplicate_Files")
        os.makedirs(dup_root, exist_ok=True)

        moved = 0
        errors = []

        # iterate groups (hashes)
        for h, files in self.groups:
            # For each group, checked files are to be kept; unchecked files moved.
            # Determine keep path(s) for this hash (we only expect one, but accept multiple checked)
            keeps = []
            # If user saved a selection for this hash, respect it
            if h in self.keep_selection and os.path.exists(self.keep_selection[h]):
                keeps = [self.keep_selection[h]]
            # Otherwise, default keep = newest
            if not keeps:
                try:
                    keeps = [max(files, key=lambda p: os.path.getmtime(p))]
                except Exception:
                    keeps = [files[0]]

            # Move files not in keeps
            for f in files:
                if f in keeps:
                    continue
                dst = os.path.join(dup_root, os.path.basename(f))
                # avoid overwrite
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

        # After moving, clear UI (no file dialogs) and internal state
        msg = f"Moved {moved} duplicate file(s) to:\n{dup_root}"
        if errors:
            msg += f"\n\n{len(errors)} error(s) occurred. Check console for details."
            for e in errors:
                print("Move error:", e)

        QtWidgets.QMessageBox.information(self, "Move complete", msg)

        # Clear UI and internal data (do not reopen file picker)
        self.hash_map.clear()
        self.groups.clear()
        self.keep_selection.clear()
        self.scan_root = None
        self.group_list.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.preview_label.setPixmap(QtGui.QPixmap())  # clear image
        self.preview_label.setText("Preview will appear here.")

    # ---------------- end ----------------


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = FileZen()
    w.show()
    sys.exit(app.exec_())
