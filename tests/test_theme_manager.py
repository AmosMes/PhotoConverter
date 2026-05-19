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
