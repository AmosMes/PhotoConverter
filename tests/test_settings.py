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
