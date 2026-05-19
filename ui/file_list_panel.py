from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QFileDialog,
)
from PySide6.QtCore import Signal

SUPPORTED_FILTER = (
    "Supported files (*.heif *.heic *.jpg *.jpeg *.png *.pdf);;"
    "All files (*)"
)


class FileListPanel(QWidget):
    selection_changed = Signal(str)  # emits selected file path (or "" if empty)
    files_changed = Signal()         # emits whenever the list contents change

    def __init__(self, multi: bool = True, parent=None):
        super().__init__(parent)
        self._multi = multi
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        open_btn = QPushButton("Open File(s)..." if self._multi else "Open File...")
        open_btn.clicked.connect(self._open_files)
        layout.addWidget(open_btn)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, stretch=1)

        if self._multi:
            btn_row = QHBoxLayout()
            add_btn = QPushButton("+ Add")
            remove_btn = QPushButton("- Remove")
            add_btn.clicked.connect(self._open_files)
            remove_btn.clicked.connect(self._remove_selected)
            btn_row.addWidget(add_btn)
            btn_row.addWidget(remove_btn)
            layout.addLayout(btn_row)

    def _open_files(self):
        if self._multi:
            paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", SUPPORTED_FILTER)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", "", SUPPORTED_FILTER)
            paths = [path] if path else []

        if not paths:
            return

        if not self._multi:
            self._list.clear()

        existing = {self._list.item(i).data(0) for i in range(self._list.count())}
        for path in paths:
            if path not in existing:
                item = QListWidgetItem(Path(path).name)
                item.setData(256, path)  # Qt.UserRole = 256
                self._list.addItem(item)

        if self._list.count() > 0 and self._list.currentItem() is None:
            self._list.setCurrentRow(0)

        self.files_changed.emit()

    def _remove_selected(self):
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))
        self.files_changed.emit()

    def _on_selection_changed(self, current, _previous):
        if current:
            self.selection_changed.emit(current.data(256))
        else:
            self.selection_changed.emit("")

    # --- Public API ---

    def open_files(self):
        self._open_files()

    def all_paths(self) -> list[str]:
        return [self._list.item(i).data(256) for i in range(self._list.count())]

    def selected_path(self) -> str:
        item = self._list.currentItem()
        return item.data(256) if item else ""

    def clear(self):
        self._list.clear()
        self.files_changed.emit()
