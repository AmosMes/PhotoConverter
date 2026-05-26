from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QComboBox, QSlider, QPushButton, QFileDialog, QLineEdit,
)
from PySide6.QtCore import Qt, Signal
from ui.rotation_widget import RotationWidget

FORMATS = ["JPEG", "PNG", "HEIF", "PDF"]
# PDF and PNG have no meaningful lossy quality; PNG uses compression level
NO_QUALITY_FORMATS = {"PDF"}


class SettingsPanel(QWidget):
    convert_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_dir = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # --- Output format ---
        layout.addWidget(QLabel("Output Format"))
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(FORMATS)
        self._fmt_combo.currentTextChanged.connect(self._on_format_changed)
        layout.addWidget(self._fmt_combo)

        # --- Quality ---
        self._quality_label = QLabel("Quality  85")
        layout.addWidget(self._quality_label)

        self._quality_slider = QSlider(Qt.Orientation.Horizontal)
        self._quality_slider.setRange(1, 100)
        self._quality_slider.setValue(85)
        self._quality_slider.valueChanged.connect(self._on_quality_changed)
        layout.addWidget(self._quality_slider)

        # --- Output folder ---
        layout.addWidget(QLabel("Output Folder"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        layout.addWidget(browse_btn)
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText("Same as source")
        self._folder_edit.setReadOnly(True)
        layout.addWidget(self._folder_edit)

        # --- Rotation ---
        layout.addWidget(QLabel("Rotation"))
        self._rotation_widget = RotationWidget()
        layout.addWidget(self._rotation_widget)

        layout.addStretch()

        # --- Convert button ---
        self._convert_btn = QPushButton("Convert")
        self._convert_btn.setMinimumHeight(40)
        self._convert_btn.clicked.connect(self.convert_requested)
        layout.addWidget(self._convert_btn)

    def _on_format_changed(self, fmt: str):
        disabled = fmt in NO_QUALITY_FORMATS
        self._quality_slider.setEnabled(not disabled)
        self._quality_label.setEnabled(not disabled)
        if fmt == "PNG":
            self._quality_label.setText(f"Compression  {self._quality_slider.value()}")
        else:
            self._quality_label.setText(f"Quality  {self._quality_slider.value()}")

    def _on_quality_changed(self, value: int):
        fmt = self._fmt_combo.currentText()
        label = "Compression" if fmt == "PNG" else "Quality"
        self._quality_label.setText(f"{label}  {value}")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir = folder
            self._folder_edit.setText(folder)

    # --- Public API ---

    def output_format(self) -> str:
        return self._fmt_combo.currentText()

    def quality(self) -> int:
        return self._quality_slider.value()

    def output_dir(self) -> str:
        return self._output_dir

    def rotation(self) -> int:
        return self._rotation_widget.rotation()

    def set_convert_button_text(self, text: str):
        self._convert_btn.setText(text)

    def set_convert_button_enabled(self, enabled: bool):
        self._convert_btn.setEnabled(enabled)
