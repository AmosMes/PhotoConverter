import math
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF


def _make_rotation_icon(clockwise: bool, size: int = 22) -> QIcon:
    """Draw a circular arrow icon using QPainter — no font dependency."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor(230, 230, 255)
    pen = QPen(color, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    m = 3
    d = size - 2 * m
    cx = size / 2.0
    cy = size / 2.0
    r = d / 2.0

    if not clockwise:
        # CCW (rotate left): arc from upper-right, going CCW 270°, ending lower-right
        p.drawArc(m, m, d, d, 45 * 16, 270 * 16)
        end_a = 315.0
        # CCW tangent direction at end angle
        tx = -math.sin(math.radians(end_a))
        ty = -math.cos(math.radians(end_a))
    else:
        # CW (rotate right): arc from upper-left, going CW 270°, ending lower-left
        p.drawArc(m, m, d, d, 135 * 16, -270 * 16)
        end_a = -135.0  # same as 225°
        # CW tangent direction at end angle
        tx = math.sin(math.radians(end_a))
        ty = math.cos(math.radians(end_a))

    # End point on circle
    ex = cx + r * math.cos(math.radians(end_a))
    ey = cy - r * math.sin(math.radians(end_a))

    # Filled arrowhead triangle at end point
    ah = 4.0
    nx, ny = -ty, tx  # perpendicular to tangent
    tip = QPointF(ex, ey)
    p1 = QPointF(ex - ah * tx + ah * 0.5 * nx, ey - ah * ty + ah * 0.5 * ny)
    p2 = QPointF(ex - ah * tx - ah * 0.5 * nx, ey - ah * ty - ah * 0.5 * ny)

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(230, 230, 255))
    p.drawPolygon(QPolygonF([tip, p1, p2]))

    p.end()
    return QIcon(px)


class RotationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._left_btn = QPushButton()
        self._left_btn.setIcon(_make_rotation_icon(clockwise=False))
        self._left_btn.setIconSize(QSize(18, 18))
        self._left_btn.setFixedSize(36, 28)
        self._left_btn.setToolTip("Rotate left (CCW)")
        self._left_btn.clicked.connect(self.rotate_left)

        self._label = QLabel("0°")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFixedWidth(36)

        self._right_btn = QPushButton()
        self._right_btn.setIcon(_make_rotation_icon(clockwise=True))
        self._right_btn.setIconSize(QSize(18, 18))
        self._right_btn.setFixedSize(36, 28)
        self._right_btn.setToolTip("Rotate right (CW)")
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
