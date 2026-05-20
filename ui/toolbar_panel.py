from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QSlider, QPushButton, QFileDialog, QFrame,
)
from PySide6.QtCore import Qt, Signal

FORMATS = ["JPEG", "PNG", "HEIF", "PDF"]
NO_QUALITY_FORMATS = {"PDF"}


class ToolbarPanel(QWidget):
    """Horizontal settings bar for Compact Toolbar and Preview-First layouts."""

    convert_requested = Signal()
    tab_changed = Signal(int)  # 0 = single, 1 = batch

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_dir = ""
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        # Tab toggle buttons
        self._btn_single = QPushButton("Single File")
        self._btn_single.setObjectName("tabBtn")
        self._btn_single.setCheckable(True)
        self._btn_single.setChecked(True)
        self._btn_single.clicked.connect(lambda: self.switch_tab(0))

        self._btn_batch = QPushButton("Batch")
        self._btn_batch.setObjectName("tabBtn")
        self._btn_batch.setCheckable(True)
        self._btn_batch.clicked.connect(lambda: self.switch_tab(1))

        layout.addWidget(self._btn_single)
        layout.addWidget(self._btn_batch)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Format
        layout.addWidget(QLabel("Format"))
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(FORMATS)
        self._fmt_combo.currentTextChanged.connect(self._on_format_changed)
        layout.addWidget(self._fmt_combo)

        # Quality
        self._quality_label = QLabel("Quality  85")
        layout.addWidget(self._quality_label)
        self._quality_slider = QSlider(Qt.Orientation.Horizontal)
        self._quality_slider.setRange(1, 100)
        self._quality_slider.setValue(85)
        self._quality_slider.setFixedWidth(110)
        self._quality_slider.valueChanged.connect(self._on_quality_changed)
        layout.addWidget(self._quality_slider)

        # Output folder
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setFixedWidth(90)
        self._browse_btn.clicked.connect(self._browse_folder)
        layout.addWidget(self._browse_btn)

        layout.addStretch()

        # Convert button
        self._convert_btn = QPushButton("Convert")
        self._convert_btn.setMinimumWidth(100)
        self._convert_btn.setMinimumHeight(34)
        self._convert_btn.clicked.connect(self.convert_requested)
        layout.addWidget(self._convert_btn)

    def switch_tab(self, index: int):
        self._btn_single.setChecked(index == 0)
        self._btn_batch.setChecked(index == 1)
        self.tab_changed.emit(index)

    def _on_format_changed(self, fmt: str):
        disabled = fmt in NO_QUALITY_FORMATS
        self._quality_slider.setEnabled(not disabled)
        self._quality_label.setEnabled(not disabled)
        label = "Compression" if fmt == "PNG" else "Quality"
        self._quality_label.setText(f"{label}  {self._quality_slider.value()}")

    def _on_quality_changed(self, value: int):
        fmt = self._fmt_combo.currentText()
        label = "Compression" if fmt == "PNG" else "Quality"
        self._quality_label.setText(f"{label}  {value}")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir = folder

    # ── Public API (mirrors SettingsPanel) ────────────────────────────────

    def output_format(self) -> str:
        return self._fmt_combo.currentText()

    def quality(self) -> int:
        return self._quality_slider.value()

    def output_dir(self) -> str:
        return self._output_dir

    def set_convert_button_enabled(self, enabled: bool):
        self._convert_btn.setEnabled(enabled)

    def set_convert_button_text(self, text: str):
        self._convert_btn.setText(text)

    def active_tab(self) -> int:
        return 1 if self._btn_batch.isChecked() else 0
