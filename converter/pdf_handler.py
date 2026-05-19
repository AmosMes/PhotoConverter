from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QDialogButtonBox,
)
from PySide6.QtCore import Qt


def pdf_page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    count = doc.page_count
    doc.close()
    return count


def render_pdf_page(pdf_path: str, page_index: int, dpi: int = 150) -> Image.Image:
    """Render a single PDF page to a PIL Image at the given DPI."""
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


class PagePickerDialog(QDialog):
    """Dialog for selecting pages from a multi-page PDF."""

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Pages to Convert")
        self.setMinimumWidth(320)
        self._page_count = pdf_page_count(pdf_path)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"This PDF has {self._page_count} pages.\nSelect the pages you want to convert:"))

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for i in range(self._page_count):
            item = QListWidgetItem(f"Page {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self._list.addItem(item)
        self._list.selectAll()
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        sel_all = QPushButton("Select All")
        sel_none = QPushButton("Deselect All")
        sel_all.clicked.connect(self._list.selectAll)
        sel_none.clicked.connect(self._list.clearSelection)
        btn_row.addWidget(sel_all)
        btn_row.addWidget(sel_none)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_page_indices(self) -> list[int]:
        return [item.data(Qt.ItemDataRole.UserRole) for item in self._list.selectedItems()]
