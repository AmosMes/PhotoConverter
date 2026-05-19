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
