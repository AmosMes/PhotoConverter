from dataclasses import replace

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QColorDialog, QFrame, QButtonGroup, QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from settings import AppearanceSettings, save_appearance
from ui.theme_manager import ThemeManager

STYLE_LABELS = {
    "modern_glass":  "Modern Glass",
    "minimal_dark":  "Minimal Dark",
    "light_pro":     "Light Professional",
}
LAYOUT_LABELS = {
    "compact_toolbar": "Compact Toolbar",
    "three_panel":     "3-Panel",
    "preview_first":   "Preview-First",
}
PRESET_ACCENTS = ["#6450ff", "#0088dd", "#cc1177"]


class AppearanceDialog(QDialog):
    appearance_changed = Signal(AppearanceSettings)

    def __init__(self, app, settings: AppearanceSettings, parent=None):
        super().__init__(parent)
        self._app = app
        self._settings = replace(settings)  # local mutable copy
        self.setWindowTitle("Appearance")
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._section_style())
        layout.addWidget(self._divider())
        layout.addWidget(self._section_layout())
        layout.addWidget(self._divider())
        layout.addWidget(self._section_accent())

        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    # ── Section builders ─────────────────────────────────────────────────

    def _section_style(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(self._section_label("Style"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self._style_group = QButtonGroup(self)
        for key, label in STYLE_LABELS.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == self._settings.style)
            btn.setObjectName("tabBtn")
            btn.clicked.connect(lambda _, k=key: self._set_style(k))
            self._style_group.addButton(btn)
            row.addWidget(btn)
        v.addLayout(row)
        return box

    def _section_layout(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(self._section_label("Layout"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self._layout_group = QButtonGroup(self)
        for key, label in LAYOUT_LABELS.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == self._settings.layout)
            btn.setObjectName("tabBtn")
            btn.clicked.connect(lambda _, k=key: self._set_layout(k))
            self._layout_group.addButton(btn)
            row.addWidget(btn)
        v.addLayout(row)
        return box

    def _section_accent(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(self._section_label("Accent Color"))
        row = QHBoxLayout()
        row.setSpacing(10)
        for hex_color in PRESET_ACCENTS:
            swatch = self._swatch(hex_color)
            swatch.clicked.connect(lambda _, c=hex_color: self._set_accent(c))
            row.addWidget(swatch)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        row.addWidget(sep)
        custom_btn = self._swatch(None)
        custom_btn.setToolTip("Custom color")
        custom_btn.clicked.connect(self._pick_custom_accent)
        row.addWidget(custom_btn)
        row.addWidget(QLabel("Custom"))
        row.addStretch()
        v.addLayout(row)
        return box

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet("font-size: 9px; letter-spacing: 1.2px; font-weight: 600;")
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    @staticmethod
    def _swatch(hex_color: "str | None") -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(28, 28)
        if hex_color:
            c = QColor(hex_color)
            lighter = c.lighter(145).name()
            btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                f"stop:0 {hex_color},stop:1 {lighter});"
                f"border-radius: 14px; border: none; }}"
                f"QPushButton:hover {{ border: 2px solid white; }}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton { background: conic-gradient(red,yellow,green,cyan,blue,magenta,red);"
                "border-radius: 14px; border: 1px solid rgba(255,255,255,0.3); }"
                "QPushButton:hover { border: 2px solid white; }"
            )
        return btn

    # ── Live apply ────────────────────────────────────────────────────────

    def _set_style(self, style: str):
        self._settings = replace(self._settings, style=style)
        self._emit()

    def _set_layout(self, layout: str):
        self._settings = replace(self._settings, layout=layout)
        self._emit()

    def _set_accent(self, accent: str):
        self._settings = replace(self._settings, accent=accent)
        self._emit()

    def _pick_custom_accent(self):
        color = QColorDialog.getColor(QColor(self._settings.accent), self, "Pick Accent Color")
        if color.isValid():
            self._set_accent(color.name())

    def _emit(self):
        ThemeManager.apply(self._app, self._settings.style, self._settings.accent)
        save_appearance(self._settings)
        self.appearance_changed.emit(self._settings)
