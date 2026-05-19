# GUI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace qt-material with a custom `ThemeManager`, implement three switchable visual styles (Modern Glass / Minimal Dark / Light Professional), three switchable layouts (Compact Toolbar / 3-Panel / Preview-First), a per-user accent color picker, and a live Appearance dialog — all persisted to `~/.photoconverter/appearance.json`.

**Architecture:** A new `ThemeManager` generates QSS from string templates keyed by style name, injecting the user's accent color at apply time. `AppearanceSettings` (a dataclass in `settings.py`) is the single source of truth; it is loaded at startup, mutated by the Appearance dialog, applied immediately to the running app, and atomically saved to disk. Layout switching rebuilds the main window's central widget from scratch.

**Tech Stack:** Python 3.11+, PySide6 6.6+, Pillow, pillow-heif, PyMuPDF, PyInstaller. `qt-material` is removed; no new runtime dependencies.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `settings.py` | **Create** | `AppearanceSettings` dataclass; `load_appearance()` / `save_appearance()` |
| `ui/theme_manager.py` | **Create** | QSS template strings; `ThemeManager.apply(app, style, accent)` |
| `ui/toolbar_panel.py` | **Create** | Horizontal settings bar (format, quality, dir, convert, tab toggle) |
| `ui/appearance_dialog.py` | **Create** | Live Appearance QDialog (style / layout / accent) |
| `ui/main_window.py` | **Modify** | `_rebuild_ui()`, layout switching, Appearance menu, startup load |
| `requirements.txt` | **Modify** | Remove `qt-material`; add `pytest` + `pytest-qt` dev deps |
| `tests/conftest.py` | **Create** | Session-scoped `QApplication` fixture |
| `tests/test_settings.py` | **Create** | Unit tests for `settings.py` |
| `tests/test_theme_manager.py` | **Create** | Unit tests for `ThemeManager` accent helpers |

---

## Dependency Matrix

| Task | Depends on | Parallel with |
|---|---|---|
| **Task 1** — AppearanceSettings + persistence | — | Task 2 |
| **Task 2** — Remove qt-material | — | Task 1 |
| **Task 3** — ThemeManager | Task 1, Task 2 | Task 4 |
| **Task 4** — ToolbarPanel | Task 2 | Task 3 |
| **Task 5** — AppearanceDialog | Task 1, Task 3 | — |
| **Task 6** — MainWindow integration | Task 3, Task 4, Task 5 | — |

### Execution waves

```
Wave 1 ──► Task 1  ╮
            Task 2  ╯  (parallel)

Wave 2 ──► Task 3  ╮  (both need Wave 1 complete)
            Task 4  ╯  (parallel)

Wave 3 ──► Task 5      (needs Task 1 + Task 3)

Wave 4 ──► Task 6      (needs Task 3 + Task 4 + Task 5)
```

---

## Task 1: AppearanceSettings and persistence

**Files:**
- Create: `settings.py`
- Create: `tests/conftest.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1.1 — Create `tests/conftest.py`**

```python
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app
```

- [ ] **Step 1.2 — Write failing tests for `settings.py`**

```python
# tests/test_settings.py
import json
import pytest
from settings import AppearanceSettings, load_appearance, save_appearance


def test_defaults_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("settings.CONFIG_FILE", tmp_path / "nonexistent.json")
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path / "nonexistent")
    result = load_appearance()
    assert result == AppearanceSettings()


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("settings.CONFIG_FILE", tmp_path / "appearance.json")
    original = AppearanceSettings(style="minimal_dark", layout="three_panel", accent="#ff0088")
    save_appearance(original)
    assert load_appearance() == original


def test_invalid_style_falls_back_to_default(tmp_path, monkeypatch):
    cfg = tmp_path / "appearance.json"
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("settings.CONFIG_FILE", cfg)
    cfg.write_text(json.dumps({"style": "NOPE", "layout": "three_panel", "accent": "#ff0000"}))
    assert load_appearance().style == "modern_glass"


def test_invalid_layout_falls_back_to_default(tmp_path, monkeypatch):
    cfg = tmp_path / "appearance.json"
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("settings.CONFIG_FILE", cfg)
    cfg.write_text(json.dumps({"style": "minimal_dark", "layout": "NOPE", "accent": "#ff0000"}))
    assert load_appearance().layout == "compact_toolbar"


def test_atomic_save_no_tmp_leftover(tmp_path, monkeypatch):
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("settings.CONFIG_FILE", tmp_path / "appearance.json")
    save_appearance(AppearanceSettings())
    assert not (tmp_path / "appearance.tmp").exists()


def test_corrupt_json_returns_defaults(tmp_path, monkeypatch):
    cfg = tmp_path / "appearance.json"
    monkeypatch.setattr("settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("settings.CONFIG_FILE", cfg)
    cfg.write_text("not json {{{")
    assert load_appearance() == AppearanceSettings()
```

- [ ] **Step 1.3 — Run tests to confirm they fail**

```
pytest tests/test_settings.py -v
```
Expected: `ModuleNotFoundError: No module named 'settings'` (or similar import error).

- [ ] **Step 1.4 — Create `settings.py`**

```python
import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".photoconverter"
CONFIG_FILE = CONFIG_DIR / "appearance.json"

VALID_STYLES = {"modern_glass", "minimal_dark", "light_pro"}
VALID_LAYOUTS = {"compact_toolbar", "three_panel", "preview_first"}


@dataclass
class AppearanceSettings:
    style: str = "modern_glass"
    layout: str = "compact_toolbar"
    accent: str = "#6450ff"


def load_appearance() -> AppearanceSettings:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        style = data.get("style", "modern_glass")
        layout = data.get("layout", "compact_toolbar")
        accent = data.get("accent", "#6450ff")
        if style not in VALID_STYLES:
            style = "modern_glass"
        if layout not in VALID_LAYOUTS:
            layout = "compact_toolbar"
        return AppearanceSettings(style=style, layout=layout, accent=accent)
    except (FileNotFoundError, json.JSONDecodeError):
        return AppearanceSettings()


def save_appearance(s: AppearanceSettings) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(s), indent=2), encoding="utf-8")
    tmp.replace(CONFIG_FILE)
```

- [ ] **Step 1.5 — Run tests to confirm they pass**

```
pytest tests/test_settings.py -v
```
Expected: 6 tests PASSED.

- [ ] **Step 1.6 — Commit**

```
git add settings.py tests/conftest.py tests/test_settings.py
git commit -m "feat: add AppearanceSettings dataclass and persistence"
```

---

## Task 2: Remove qt-material

**Files:**
- Modify: `requirements.txt`
- Modify: `ui/main_window.py`

- [ ] **Step 2.1 — Update `requirements.txt`**

Remove `qt-material>=2.14.0`. Add dev deps comment block at the bottom:

```
PySide6>=6.6.0
Pillow>=10.0.0
pillow-heif>=0.15.0
PyMuPDF>=1.23.0
PyInstaller>=6.0.0

# dev
# pytest>=8.0.0
# pytest-qt>=4.4.0
```

- [ ] **Step 2.2 — Uninstall qt-material from the active environment**

```
pip uninstall qt-material -y
pip install pytest pytest-qt
```

- [ ] **Step 2.3 — Strip qt-material from `ui/main_window.py`**

Remove this import at the top of `ui/main_window.py`:
```python
from qt_material import apply_stylesheet
```

Remove the `THEMES` dict (lines near top of file):
```python
THEMES = {
    "Dark":  "dark_blue.xml",
    "Light": "light_blue.xml",
}
```

Remove the `_apply_theme` method:
```python
def _apply_theme(self, name: str):
    if name in THEMES:
        apply_stylesheet(self._app, theme=THEMES[name])
        self._current_theme = name
```

In `__init__`, remove the call `self._apply_theme("Dark")` and the attribute `self._current_theme = "Dark"`.

In `_build_ui`, remove the entire Theme menu block:
```python
# Theme menu
theme_menu = menu.addMenu("Theme")
theme_group = QActionGroup(self)
theme_group.setExclusive(True)

for name in THEMES:
    action = QAction(name, self)
    action.setCheckable(True)
    action.setChecked(name == "Dark")
    action.triggered.connect(lambda checked, n=name: self._apply_theme(n))
    theme_group.addAction(action)
    theme_menu.addAction(action)
```

Also remove `QActionGroup` from the `PySide6.QtGui` import line (keep `QAction`):
```python
from PySide6.QtGui import QAction
```

- [ ] **Step 2.4 — Verify the app still launches (unstyled)**

```
python main.py
```
Expected: window opens with default Qt styling and no import errors.

- [ ] **Step 2.5 — Commit**

```
git add requirements.txt ui/main_window.py
git commit -m "chore: remove qt-material dependency"
```

---

## Task 3: ThemeManager

**Files:**
- Create: `ui/theme_manager.py`
- Create: `tests/test_theme_manager.py`

- [ ] **Step 3.1 — Write failing tests**

```python
# tests/test_theme_manager.py
import pytest
from PySide6.QtGui import QColor
from ui.theme_manager import ThemeManager


def test_accent_pair_returns_two_strings():
    a1, a2 = ThemeManager._accent_pair("#6450ff")
    assert a1.startswith("#")
    assert a2.startswith("#")
    assert a1 != a2


def test_accent_pair_lighter_has_higher_value():
    a1, a2 = ThemeManager._accent_pair("#6450ff")
    c1 = QColor(a1)
    c2 = QColor(a2)
    assert c2.value() >= c1.value()


def test_rgba_helper():
    from ui.theme_manager import _rgba
    assert _rgba(100, 80, 255, 0.2) == "rgba(100,80,255,0.2)"


def test_apply_modern_glass_does_not_raise(qapp):
    ThemeManager.apply(qapp, "modern_glass", "#6450ff")
    assert qapp.styleSheet() != ""


def test_apply_minimal_dark_does_not_raise(qapp):
    ThemeManager.apply(qapp, "minimal_dark", "#0088dd")
    assert qapp.styleSheet() != ""


def test_apply_light_pro_does_not_raise(qapp):
    ThemeManager.apply(qapp, "light_pro", "#cc1177")
    assert qapp.styleSheet() != ""


def test_apply_unknown_style_falls_back_to_modern_glass(qapp):
    ThemeManager.apply(qapp, "unknown_style", "#6450ff")
    assert qapp.styleSheet() != ""


def test_accent_injected_in_stylesheet(qapp):
    ThemeManager.apply(qapp, "modern_glass", "#abcdef")
    assert "#abcdef" in qapp.styleSheet().lower() or "abcdef" in qapp.styleSheet().lower()
```

- [ ] **Step 3.2 — Run tests to confirm they fail**

```
pytest tests/test_theme_manager.py -v
```
Expected: `ModuleNotFoundError: No module named 'ui.theme_manager'`.

- [ ] **Step 3.3 — Create `ui/theme_manager.py`**

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor


def _rgba(r: int, g: int, b: int, alpha: float) -> str:
    return f"rgba({r},{g},{b},{alpha})"


class ThemeManager:
    @staticmethod
    def _accent_pair(hex_color: str) -> tuple[str, str]:
        c = QColor(hex_color)
        return hex_color, c.lighter(145).name()

    @staticmethod
    def apply(app: QApplication, style: str, accent: str) -> None:
        from ui.theme_manager import STYLE_TEMPLATES
        template = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["modern_glass"])
        a1, a2 = ThemeManager._accent_pair(accent)
        c = QColor(accent)
        r, g, b = c.red(), c.green(), c.blue()
        app.setStyleSheet(template.format(a1=a1, a2=a2, ar=r, ag=g, ab=b))


# ── Stylesheet templates ────────────────────────────────────────────────────
# All literal { } in QSS must be doubled {{ }} because str.format() is used.
# Accent placeholders: {a1} primary, {a2} lighter, {ar}/{ag}/{ab} RGB ints.

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
```

- [ ] **Step 3.4 — Run tests to confirm they pass**

```
pytest tests/test_theme_manager.py -v
```
Expected: 8 tests PASSED.

- [ ] **Step 3.5 — Verify accent injection visually**

```
python -c "
from PySide6.QtWidgets import QApplication
from ui.theme_manager import ThemeManager
app = QApplication([])
ThemeManager.apply(app, 'modern_glass', '#6450ff')
print(app.styleSheet()[:200])
"
```
Expected: first 200 chars of generated QSS printed without error.

- [ ] **Step 3.6 — Commit**

```
git add ui/theme_manager.py tests/test_theme_manager.py
git commit -m "feat: add ThemeManager with Modern Glass, Minimal Dark, Light Pro templates"
```

---

## Task 4: ToolbarPanel

**Files:**
- Create: `ui/toolbar_panel.py`

ToolbarPanel is used by the Compact Toolbar and Preview-First layouts. It exposes the same public API as `SettingsPanel` so `MainWindow._start_conversion()` works without changes.

- [ ] **Step 4.1 — Create `ui/toolbar_panel.py`**

```python
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
        self._btn_single.clicked.connect(lambda: self._switch_tab(0))

        self._btn_batch = QPushButton("Batch")
        self._btn_batch.setObjectName("tabBtn")
        self._btn_batch.setCheckable(True)
        self._btn_batch.clicked.connect(lambda: self._switch_tab(1))

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

    def _switch_tab(self, index: int):
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
```

- [ ] **Step 4.2 — Smoke-test the widget**

```
python -c "
from PySide6.QtWidgets import QApplication
from ui.toolbar_panel import ToolbarPanel
app = QApplication([])
tb = ToolbarPanel()
tb.show()
print('format:', tb.output_format())
print('quality:', tb.quality())
app.exec()
"
```
Expected: a horizontal toolbar appears; format is `JPEG`, quality is `85`.

- [ ] **Step 4.3 — Commit**

```
git add ui/toolbar_panel.py
git commit -m "feat: add ToolbarPanel for compact and preview-first layouts"
```

---

## Task 5: AppearanceDialog

**Files:**
- Create: `ui/appearance_dialog.py`

The dialog reads the current `AppearanceSettings`, lets the user change style / layout / accent live, and saves on close.

- [ ] **Step 5.1 — Create `ui/appearance_dialog.py`**

```python
from dataclasses import replace

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QColorDialog, QFrame, QButtonGroup,
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
    def _swatch(hex_color: str | None) -> QPushButton:
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
```

- [ ] **Step 5.2 — Smoke-test the dialog**

```
python -c "
from PySide6.QtWidgets import QApplication
from settings import AppearanceSettings
from ui.appearance_dialog import AppearanceDialog
app = QApplication([])
dlg = AppearanceDialog(app, AppearanceSettings())
dlg.show()
app.exec()
"
```
Expected: dialog opens showing Style / Layout / Accent sections. Clicking style/layout/accent buttons applies changes live and saves to `~/.photoconverter/appearance.json`.

- [ ] **Step 5.3 — Commit**

```
git add ui/appearance_dialog.py
git commit -m "feat: add AppearanceDialog with live style/layout/accent controls"
```

---

## Task 6: MainWindow integration

**Files:**
- Modify: `ui/main_window.py`

This task wires everything together: load saved appearance at startup, apply theme, build the correct layout, add the Appearance menu item, and handle live layout switches from the dialog.

- [ ] **Step 6.1 — Add imports to `ui/main_window.py`**

Add at the top of `ui/main_window.py`, alongside the existing imports:

```python
from settings import load_appearance, save_appearance, AppearanceSettings
from ui.theme_manager import ThemeManager
from ui.toolbar_panel import ToolbarPanel
from ui.appearance_dialog import AppearanceDialog
```

- [ ] **Step 6.2 — Replace `__init__` to load appearance and call `_rebuild_ui`**

Replace the existing `__init__` with:

```python
def __init__(self, app):
    super().__init__()
    self._app = app
    self._worker: ConversionWorker | None = None
    self._appearance = load_appearance()
    self.setWindowTitle(f"PhotoConverter {VERSION}")
    self.resize(1100, 680)
    ThemeManager.apply(self._app, self._appearance.style, self._appearance.accent)
    self._rebuild_ui(self._appearance)
```

- [ ] **Step 6.3 — Add `_rebuild_ui` dispatcher**

Add this method to `MainWindow`:

```python
def _rebuild_ui(self, appearance: AppearanceSettings):
    old = self.centralWidget()
    if old:
        old.deleteLater()
    if hasattr(self, "_status"):
        pass  # status bar persists — do not recreate
    else:
        self._status = QStatusBar()
        self.setStatusBar(self._status)

    self._progress = QProgressBar()
    self._progress.setVisible(False)
    self._progress.setTextVisible(True)

    if appearance.layout == "compact_toolbar":
        self._build_compact_toolbar_ui()
    elif appearance.layout == "three_panel":
        self._build_three_panel_ui()
    else:  # preview_first
        self._build_preview_first_ui()

    self._build_menu()
```

- [ ] **Step 6.4 — Add `_build_menu`**

Extract menu construction into its own method (called by `_rebuild_ui`) so it is recreated on layout switch:

```python
def _build_menu(self):
    self.menuBar().clear()
    menu = self.menuBar()

    file_menu = menu.addMenu("File")
    open_file_action = QAction("Open File...", self)
    open_file_action.setShortcut("Ctrl+O")
    open_file_action.triggered.connect(self._menu_open_file)
    file_menu.addAction(open_file_action)

    open_batch_action = QAction("Open Files (Batch)...", self)
    open_batch_action.setShortcut("Ctrl+Shift+O")
    open_batch_action.triggered.connect(self._menu_open_batch)
    file_menu.addAction(open_batch_action)
    file_menu.addSeparator()

    quit_action = QAction("Quit", self)
    quit_action.setShortcut("Ctrl+Q")
    quit_action.triggered.connect(self.close)
    file_menu.addAction(quit_action)

    appearance_action = QAction("Appearance...", self)
    appearance_action.triggered.connect(self._open_appearance)
    menu.addAction(appearance_action)

    help_menu = menu.addMenu("Help")
    about_action = QAction("About", self)
    about_action.triggered.connect(self._show_about)
    help_menu.addAction(about_action)
```

- [ ] **Step 6.5 — Add `_open_appearance`**

```python
def _open_appearance(self):
    dlg = AppearanceDialog(self._app, self._appearance, self)
    dlg.appearance_changed.connect(self._on_appearance_changed)
    dlg.exec()

def _on_appearance_changed(self, new_settings: AppearanceSettings):
    layout_changed = new_settings.layout != self._appearance.layout
    self._appearance = new_settings
    if layout_changed:
        ThemeManager.apply(self._app, new_settings.style, new_settings.accent)
        self._rebuild_ui(new_settings)
    else:
        ThemeManager.apply(self._app, new_settings.style, new_settings.accent)
```

- [ ] **Step 6.6 — Add `_build_three_panel_ui` (renamed from existing `_build_ui` body)**

Rename the current body of `_build_ui` (after menu construction) into:

```python
def _build_three_panel_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    main_layout = QVBoxLayout(central)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(8)

    self._tabs = QTabWidget()
    main_layout.addWidget(self._tabs, stretch=1)

    self._single_panel = self._build_mode_panel(multi=False)
    self._tabs.addTab(self._single_panel["widget"], "Single File")
    self._batch_panel = self._build_mode_panel(multi=True)
    self._tabs.addTab(self._batch_panel["widget"], "Batch")
    self._tabs.currentChanged.connect(self._on_tab_changed)

    main_layout.addWidget(self._progress)
```

`_build_mode_panel` is unchanged from the original implementation.

- [ ] **Step 6.7 — Add `_build_compact_toolbar_ui`**

```python
def _build_compact_toolbar_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    main_layout = QVBoxLayout(central)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(6)

    self._toolbar = ToolbarPanel()
    main_layout.addWidget(self._toolbar)

    # Separator line below toolbar
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    main_layout.addWidget(sep)

    # Two body panels; only one shown at a time
    self._single_body = self._build_body_panel(multi=False)
    self._batch_body = self._build_body_panel(multi=True)
    self._batch_body["widget"].setVisible(False)

    main_layout.addWidget(self._single_body["widget"], stretch=1)
    main_layout.addWidget(self._batch_body["widget"], stretch=1)
    main_layout.addWidget(self._progress)

    self._toolbar.tab_changed.connect(self._on_toolbar_tab_changed)
    self._toolbar.convert_requested.connect(self._start_conversion_from_toolbar)

def _build_body_panel(self, multi: bool) -> dict:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(6)

    file_list = FileListPanel(multi=multi)
    preview = PreviewPanel()

    file_list.setMinimumWidth(180)
    file_list.setMaximumWidth(260)

    splitter.addWidget(self._framed(file_list))
    splitter.addWidget(self._framed(preview))
    splitter.setStretchFactor(1, 1)
    layout.addWidget(splitter)

    file_list.selection_changed.connect(
        lambda path: preview.load_file(path) if path else preview.clear()
    )
    return {"widget": widget, "file_list": file_list, "preview": preview}

def _on_toolbar_tab_changed(self, index: int):
    self._single_body["widget"].setVisible(index == 0)
    self._batch_body["widget"].setVisible(index == 1)

def _start_conversion_from_toolbar(self):
    body = self._batch_body if self._toolbar.active_tab() == 1 else self._single_body
    self._start_conversion(body["file_list"], self._toolbar)
```

- [ ] **Step 6.8 — Add `_build_preview_first_ui`**

```python
def _build_preview_first_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    main_layout = QVBoxLayout(central)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(6)

    self._toolbar = ToolbarPanel()
    main_layout.addWidget(self._toolbar)

    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    main_layout.addWidget(sep)

    # Large preview
    self._preview_pf = PreviewPanel()
    main_layout.addWidget(self._framed(self._preview_pf), stretch=1)

    # Horizontal file strip
    strip_container = QWidget()
    strip_container.setFixedHeight(72)
    strip_layout = QHBoxLayout(strip_container)
    strip_layout.setContentsMargins(0, 0, 0, 0)

    self._single_body_pf = self._build_body_panel(multi=False)
    self._batch_body_pf = self._build_body_panel(multi=True)

    # For preview-first, show only the file list (no extra preview panel)
    self._single_file_list = FileListPanel(multi=False)
    self._batch_file_list = FileListPanel(multi=True)
    self._batch_file_list.setVisible(False)

    strip_layout.addWidget(self._single_file_list)
    strip_layout.addWidget(self._batch_file_list)
    main_layout.addWidget(self._framed(strip_container))
    main_layout.addWidget(self._progress)

    self._single_file_list.selection_changed.connect(
        lambda p: self._preview_pf.load_file(p) if p else self._preview_pf.clear()
    )
    self._batch_file_list.selection_changed.connect(
        lambda p: self._preview_pf.load_file(p) if p else self._preview_pf.clear()
    )
    self._toolbar.tab_changed.connect(self._on_preview_first_tab_changed)
    self._toolbar.convert_requested.connect(self._start_conversion_from_preview_first)

def _on_preview_first_tab_changed(self, index: int):
    self._single_file_list.setVisible(index == 0)
    self._batch_file_list.setVisible(index == 1)

def _start_conversion_from_preview_first(self):
    fl = self._batch_file_list if self._toolbar.active_tab() == 1 else self._single_file_list
    self._start_conversion(fl, self._toolbar)
```

- [ ] **Step 6.9 — Fix `_menu_open_file` and `_menu_open_batch` to be layout-aware**

Replace the existing two methods:

```python
def _menu_open_file(self):
    if self._appearance.layout == "three_panel":
        self._tabs.setCurrentIndex(0)
        self._single_panel["file_list"].open_files()
    elif self._appearance.layout == "compact_toolbar":
        self._toolbar._switch_tab(0)
        self._single_body["file_list"].open_files()
    else:
        self._toolbar._switch_tab(0)
        self._single_file_list.open_files()

def _menu_open_batch(self):
    if self._appearance.layout == "three_panel":
        self._tabs.setCurrentIndex(1)
        self._batch_panel["file_list"].open_files()
    elif self._appearance.layout == "compact_toolbar":
        self._toolbar._switch_tab(1)
        self._batch_body["file_list"].open_files()
    else:
        self._toolbar._switch_tab(1)
        self._batch_file_list.open_files()
```

- [ ] **Step 6.10 — Remove now-unused `_on_tab_changed` guard and `_active_panel`**

These methods are only valid in the 3-Panel layout. Wrap `_active_panel` to guard:

```python
def _active_panel(self) -> dict:
    return self._single_panel if self._tabs.currentIndex() == 0 else self._batch_panel
```
This is only called for 3-Panel layout via `_start_conversion` in the existing `_build_mode_panel` wiring, so no change needed there.

- [ ] **Step 6.11 — Launch and validate all three layouts**

```
python main.py
```

Check the following manually:
1. App launches with Modern Glass style and Compact Toolbar layout (default).
2. Open **Appearance** from menu bar — dialog appears.
3. Switch Style to Minimal Dark — app re-themes live.
4. Switch Style to Light Professional — app re-themes live.
5. Switch Layout to 3-Panel — main window rebuilds with vertical file list and settings panel on the right.
6. Switch Layout to Preview-First — large preview area appears, file strip at bottom.
7. Close dialog, relaunch — previous settings are restored from `~/.photoconverter/appearance.json`.
8. Change accent to Blue/Cyan preset — buttons, slider, progress bar all change color.
9. Click Custom color wheel — OS color picker opens; selecting a color applies it live.
10. Load a file and run a conversion in each layout — conversion completes successfully.

- [ ] **Step 6.12 — Commit**

```
git add ui/main_window.py
git commit -m "feat: wire ThemeManager, ToolbarPanel, AppearanceDialog into MainWindow"
```

- [ ] **Step 6.13 — Final integration commit**

```
git add -A
git commit -m "feat: GUI redesign — Modern Glass theme, 3 layouts, live Appearance dialog"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Style (3 options) ✓, Layout (3 options) ✓, Accent color (3 presets + wheel) ✓, Appearance dialog ✓, Live apply ✓, Persistence ✓, qt-material removed ✓
- [x] **No placeholders:** All steps contain complete code
- [x] **Type consistency:** `AppearanceSettings` used identically in Tasks 1, 5, 6. `ThemeManager.apply(app, style, accent)` signature consistent across Tasks 3, 5, 6. `ToolbarPanel` public API mirrors `SettingsPanel` in Tasks 4 and 6.
