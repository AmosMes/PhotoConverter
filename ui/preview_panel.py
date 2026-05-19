from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from PIL import Image
import pillow_heif  # ensures HEIF opener is registered
import fitz


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(300, 300)
        self._image_label.setText("No file selected")
        layout.addWidget(self._image_label, stretch=1)

        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._info_label)

    def load_file(self, path: str):
        p = Path(path)
        ext = p.suffix.lower()
        try:
            if ext == ".pdf":
                self._load_pdf_preview(path)
            else:
                self._load_image_preview(path)
            self._info_label.setText(p.name)
        except Exception as exc:
            self._image_label.setText(f"Preview unavailable\n{exc}")
            self._info_label.setText(p.name)

    def clear(self):
        self._image_label.setPixmap(QPixmap())
        self._image_label.setText("No file selected")
        self._info_label.setText("")

    def _load_image_preview(self, path: str):
        img = Image.open(path)
        w, h = img.size
        fmt = img.format or Path(path).suffix.lstrip(".").upper()
        self._info_label.setText(f"{Path(path).name}   {w} × {h} · {fmt}")
        self._set_pixmap_from_pil(img)

    def _load_pdf_preview(self, path: str):
        doc = fitz.open(path)
        page_count = doc.page_count
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
        pages_str = f"{page_count} page{'s' if page_count != 1 else ''}"
        self._info_label.setText(f"{Path(path).name}   {pages_str} · PDF")
        self._set_pixmap_from_pil(img)

    def _set_pixmap_from_pil(self, img: Image.Image):
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, "PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        self._display_pixmap(pixmap)

    def _display_pixmap(self, pixmap: QPixmap):
        available = self._image_label.size()
        scaled = pixmap.scaled(
            available,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-scale current pixmap when the panel is resized
        if not self._image_label.pixmap() or self._image_label.pixmap().isNull():
            return
        self._display_pixmap(self._image_label.pixmap())
