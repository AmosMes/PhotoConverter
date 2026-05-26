import math
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QSize, QPointF, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF


def _make_rotation_icon(clockwise: bool, size: int = 22) -> QIcon:
    """Draw a circular arrow icon using QPainter — no font dependency."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor(230, 230, 255)
    # Arc line thickness scales with icon size
    pen = QPen(color, max(1.5, size * 0.1))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    m = max(2, size // 8)
    d = size - 2 * m
    cx = size / 2.0
    cy = size / 2.0
    r = d / 2.0

    # Arrowhead proportional to circle radius
    ah_len = r * 0.58       # length of arrowhead along tangent
    ah_half_w = r * 0.20    # half-width at base — pointed ratio ~3:1
    # Reduce arc span so arc ends at arrowhead base, not tip
    arc_trim = math.degrees(ah_len / r)  # degrees to cut from arc end

    if not clockwise:
        # CCW (rotate left): arc from upper-right going CCW, arrowhead at lower-right
        p.drawArc(m, m, d, d, 45 * 16, int((270 - arc_trim) * 16))
        end_a = 315.0
        tx = -math.sin(math.radians(end_a))
        ty = -math.cos(math.radians(end_a))
    else:
        # CW (rotate right): arc from upper-left going CW, arrowhead at lower-left
        p.drawArc(m, m, d, d, 135 * 16, int(-(270 - arc_trim) * 16))
        end_a = -135.0  # same as 225°
        tx = math.sin(math.radians(end_a))
        ty = math.cos(math.radians(end_a))

    # Tip of arrowhead sits on the circle edge
    tip_x = cx + r * math.cos(math.radians(end_a))
    tip_y = cy - r * math.sin(math.radians(end_a))

    # Base of arrowhead is ah_len back along the tangent
    nx, ny = -ty, tx  # perpendicular to tangent
    base_x = tip_x - ah_len * tx
    base_y = tip_y - ah_len * ty
    tip = QPointF(tip_x, tip_y)
    p1 = QPointF(base_x + ah_half_w * nx, base_y + ah_half_w * ny)
    p2 = QPointF(base_x - ah_half_w * nx, base_y - ah_half_w * ny)

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(230, 230, 255))
    p.drawPolygon(QPolygonF([tip, p1, p2]))

    p.end()
    return QIcon(px)


class RotationWidget(QWidget):
    rotation_changed = Signal(int)

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
        self.rotation_changed.emit(self._rotation)

    def rotate_right(self):
        self._rotation = (self._rotation - 90) % 360
        self._label.setText(f"{self._rotation}°")
        self.rotation_changed.emit(self._rotation)

    def rotation(self) -> int:
        return self._rotation

    def reset(self):
        self._rotation = 0
        self._label.setText("0°")
