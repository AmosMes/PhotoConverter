from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt


class RotationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._left_btn = QPushButton("↺")
        self._left_btn.setFixedWidth(32)
        self._left_btn.clicked.connect(self.rotate_left)

        self._label = QLabel("0°")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFixedWidth(36)

        self._right_btn = QPushButton("↻")
        self._right_btn.setFixedWidth(32)
        self._right_btn.clicked.connect(self.rotate_right)

        layout.addWidget(self._left_btn)
        layout.addWidget(self._label)
        layout.addWidget(self._right_btn)

    def rotate_left(self):
        self._rotation = (self._rotation + 90) % 360
        self._label.setText(f"{self._rotation}°")

    def rotate_right(self):
        self._rotation = (self._rotation - 90) % 360
        self._label.setText(f"{self._rotation}°")

    def rotation(self) -> int:
        return self._rotation

    def reset(self):
        self._rotation = 0
        self._label.setText("0°")
