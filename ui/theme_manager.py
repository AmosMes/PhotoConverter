from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor


# Utility for callers that need rgba strings (e.g. swatch colours in AppearanceDialog).
def _rgba(r: int, g: int, b: int, alpha: float) -> str:
    return f"rgba({r},{g},{b},{alpha})"


class ThemeManager:
    @staticmethod
    def _accent_pair(hex_color: str) -> tuple[str, str]:
        c = QColor(hex_color)
        return hex_color, c.lighter(145).name()

    @staticmethod
    def apply(app: QApplication, style: str, accent: str) -> None:
        template = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["modern_glass"])
        c = QColor(accent)
        a1, a2 = accent, c.lighter(145).name()
        r, g, b = c.red(), c.green(), c.blue()
        app.setStyleSheet(template.format(a1=a1, a2=a2, ar=r, ag=g, ab=b))


# All literal { } in QSS must be doubled {{ }} because str.format() is used.
# Accent placeholders: {a1} primary colour, {a2} lighter variant, {ar}/{ag}/{ab} RGB ints.

MODERN_GLASS_TEMPLATE = """
QMainWindow {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0f0f1a,stop:1 #1a1040);
}}
QWidget {{
    background-color: transparent;
    color: #ccbbff;
    font-family: system-ui, sans-serif;
}}
QDialog {{
    background: #13102a;
}}
QFrame#panelFrame {{
    background-color: rgba({ar},{ag},{ab},0.06);
    border: 1px solid rgba({ar},{ag},{ab},0.22);
    border-radius: 8px;
}}
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {a1},stop:1 {a2});
    border: none;
    border-radius: 5px;
    color: white;
    padding: 6px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {a2},stop:1 {a1});
}}
QPushButton:disabled {{
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.28);
}}
QPushButton#tabBtn {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #8877bb;
    padding: 4px 14px;
    border-radius: 4px;
    font-weight: normal;
}}
QPushButton#tabBtn:checked {{
    background: rgba({ar},{ag},{ab},0.22);
    border: 1px solid rgba({ar},{ag},{ab},0.5);
    color: #ddccff;
    font-weight: 600;
}}
QComboBox {{
    background-color: rgba({ar},{ag},{ab},0.09);
    border: 1px solid rgba({ar},{ag},{ab},0.28);
    border-radius: 4px;
    color: #ccbbff;
    padding: 4px 8px;
    min-width: 80px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: #18103a;
    border: 1px solid rgba({ar},{ag},{ab},0.35);
    color: #ccbbff;
    selection-background-color: rgba({ar},{ag},{ab},0.28);
    outline: none;
}}
QSlider::groove:horizontal {{
    background: rgba(255,255,255,0.09);
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {a1};
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {a1},stop:1 {a2});
    border-radius: 2px;
}}
QListWidget {{
    background-color: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    color: #ccbbff;
    outline: none;
}}
QListWidget::item {{ padding: 3px 6px; border-radius: 3px; }}
QListWidget::item:selected {{
    background-color: rgba({ar},{ag},{ab},0.22);
    color: #ddccff;
}}
QListWidget::item:hover {{ background-color: rgba({ar},{ag},{ab},0.11); }}
QProgressBar {{
    background-color: rgba(255,255,255,0.07);
    border: none;
    border-radius: 3px;
    max-height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {a1},stop:1 {a2});
    border-radius: 3px;
}}
QTabWidget::pane {{
    border: 1px solid rgba({ar},{ag},{ab},0.22);
    border-radius: 6px;
    background: transparent;
}}
QTabBar::tab {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    color: #8877bb;
    padding: 5px 16px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: rgba({ar},{ag},{ab},0.2);
    border-color: rgba({ar},{ag},{ab},0.42);
    color: #ddccff;
}}
QLineEdit {{
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #ccbbff;
    padding: 4px 8px;
}}
QLabel {{ color: #8877bb; background: transparent; }}
QStatusBar {{
    background-color: rgba(0,0,0,0.35);
    color: #665588;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
QMenuBar {{
    background-color: rgba(0,0,0,0.45);
    color: #aa99ff;
    border-bottom: 1px solid rgba({ar},{ag},{ab},0.18);
}}
QMenuBar::item:selected {{ background-color: rgba({ar},{ag},{ab},0.22); border-radius: 3px; }}
QMenu {{
    background-color: #160f32;
    border: 1px solid rgba({ar},{ag},{ab},0.32);
    color: #ccbbff;
}}
QMenu::item:selected {{ background-color: rgba({ar},{ag},{ab},0.28); }}
QSplitter::handle {{ background-color: rgba({ar},{ag},{ab},0.18); }}
QScrollBar:vertical {{
    background: rgba(255,255,255,0.04);
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: rgba({ar},{ag},{ab},0.35);
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

MINIMAL_DARK_TEMPLATE = """
QMainWindow, QDialog {{ background-color: #1a1a2e; }}
QWidget {{ background-color: transparent; color: #c8c8e0; font-family: system-ui, sans-serif; }}
QFrame#panelFrame {{
    background-color: #20203a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
}}
QPushButton {{
    background-color: {a1};
    border: none;
    border-radius: 4px;
    color: white;
    padding: 6px 16px;
}}
QPushButton:hover {{ background-color: {a2}; }}
QPushButton:disabled {{ background-color: #2a2a4a; color: #555577; }}
QPushButton#tabBtn {{
    background: #252540;
    border: 1px solid #3a3a5a;
    color: #8888aa;
    padding: 4px 14px;
    border-radius: 4px;
}}
QPushButton#tabBtn:checked {{
    background: {a1};
    border-color: {a1};
    color: white;
}}
QComboBox {{
    background-color: #252540;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    color: #c8c8e0;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: #1e1e38;
    border: 1px solid #3a3a5a;
    color: #c8c8e0;
    selection-background-color: #3a3a6a;
    outline: none;
}}
QSlider::groove:horizontal {{ background: #2a2a4a; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {a1};
    width: 12px; height: 12px;
    border-radius: 6px; margin: -4px 0;
}}
QSlider::sub-page:horizontal {{ background: {a1}; border-radius: 2px; }}
QListWidget {{
    background-color: #141428;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    color: #c8c8e0;
    outline: none;
}}
QListWidget::item {{ padding: 3px 6px; border-radius: 2px; }}
QListWidget::item:selected {{ background-color: {a1}; color: white; }}
QListWidget::item:hover {{ background-color: #2a2a4a; }}
QProgressBar {{
    background-color: #2a2a4a;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    color: transparent;
}}
QProgressBar::chunk {{ background-color: {a1}; border-radius: 3px; }}
QTabWidget::pane {{ border: 1px solid #2a2a4a; border-radius: 4px; background: transparent; }}
QTabBar::tab {{
    background: #252540;
    border: 1px solid #2a2a4a;
    border-bottom: none;
    color: #8888aa;
    padding: 5px 16px;
    margin-right: 2px;
    border-radius: 3px 3px 0 0;
}}
QTabBar::tab:selected {{ background: #3a3a6a; color: #c8c8e0; }}
QLineEdit {{
    background-color: #252540;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    color: #c8c8e0;
    padding: 4px 8px;
}}
QLabel {{ color: #8888aa; background: transparent; }}
QStatusBar {{ background-color: #141428; color: #666688; }}
QMenuBar {{ background-color: #141428; color: #c8c8e0; }}
QMenuBar::item:selected {{ background-color: #3a3a6a; }}
QMenu {{ background-color: #1e1e38; border: 1px solid #3a3a5a; color: #c8c8e0; }}
QMenu::item:selected {{ background-color: #3a3a6a; }}
QSplitter::handle {{ background-color: #2a2a4a; }}
QScrollBar:vertical {{ background: #1e1e38; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #3a3a5a; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

LIGHT_PRO_TEMPLATE = """
QMainWindow, QDialog {{ background-color: #f0f2f5; }}
QWidget {{ background-color: transparent; color: #1a1a2e; font-family: system-ui, sans-serif; }}
QFrame#panelFrame {{
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 8px;
}}
QPushButton {{
    background-color: {a1};
    border: none;
    border-radius: 5px;
    color: white;
    padding: 6px 16px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {a2}; }}
QPushButton:disabled {{ background-color: #e9ecef; color: #adb5bd; }}
QPushButton#tabBtn {{
    background: #e9ecef;
    border: 1px solid #d0d5dd;
    color: #667085;
    padding: 4px 14px;
    border-radius: 4px;
    font-weight: normal;
}}
QPushButton#tabBtn:checked {{
    background: {a1};
    border-color: {a1};
    color: white;
    font-weight: 600;
}}
QComboBox {{
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    color: #1a1a2e;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    color: #1a1a2e;
    selection-background-color: #e9ecef;
    outline: none;
}}
QSlider::groove:horizontal {{ background: #e9ecef; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {a1};
    width: 14px; height: 14px;
    border-radius: 7px; margin: -5px 0;
}}
QSlider::sub-page:horizontal {{ background: {a1}; border-radius: 2px; }}
QListWidget {{
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    color: #1a1a2e;
    outline: none;
}}
QListWidget::item {{ padding: 3px 6px; border-radius: 3px; }}
QListWidget::item:selected {{ background-color: {a1}; color: white; }}
QListWidget::item:hover {{ background-color: #f0f2f5; }}
QProgressBar {{
    background-color: #e9ecef;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    color: transparent;
}}
QProgressBar::chunk {{ background-color: {a1}; border-radius: 3px; }}
QTabWidget::pane {{ border: 1px solid #d0d5dd; border-radius: 6px; background: transparent; }}
QTabBar::tab {{
    background: #e9ecef;
    border: 1px solid #d0d5dd;
    border-bottom: none;
    color: #667085;
    padding: 5px 16px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
}}
QTabBar::tab:selected {{ background: #ffffff; color: {a1}; }}
QLineEdit {{
    background-color: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    color: #1a1a2e;
    padding: 4px 8px;
}}
QLabel {{ color: #667085; background: transparent; }}
QStatusBar {{ background-color: #e9ecef; color: #667085; border-top: 1px solid #d0d5dd; }}
QMenuBar {{ background-color: #ffffff; color: #1a1a2e; border-bottom: 1px solid #d0d5dd; }}
QMenuBar::item:selected {{ background-color: #e9ecef; border-radius: 3px; }}
QMenu {{ background-color: #ffffff; border: 1px solid #d0d5dd; color: #1a1a2e; }}
QMenu::item:selected {{ background-color: #e9ecef; }}
QSplitter::handle {{ background-color: #d0d5dd; }}
QScrollBar:vertical {{ background: #f0f2f5; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: #d0d5dd; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

STYLE_TEMPLATES: dict[str, str] = {
    "modern_glass": MODERN_GLASS_TEMPLATE,
    "minimal_dark": MINIMAL_DARK_TEMPLATE,
    "light_pro": LIGHT_PRO_TEMPLATE,
}
