# GUI Redesign — Design Spec

**Date:** 2026-05-20  
**Status:** Approved

---

## Overview

Redesign the PhotoConverter desktop UI from the current qt-material flat theme to a premium "Modern Glass" aesthetic, introduce three user-selectable layout modes, and add a live Appearance settings dialog that persists user preferences across launches.

---

## Visual Style

### Modern Glass (new default)
- Background: deep dark gradient (`#0f0f1a` → `#1a1040`)
- Panels: translucent with subtle borders (`rgba(100,80,255,0.08)` fill, `rgba(100,80,255,0.2)` border)
- Typography: system-ui, muted purple-white (`#ccbbff` headings, `#8877bb` labels)
- Accent: configurable gradient (see Accent Color below)
- Shadows/glow: accent-colored glow on interactive elements (`box-shadow: 0 0 12px rgba(accent, 0.4)`)
- Remove qt-material dependency; implement styling via Qt stylesheets directly

### Minimal Dark (option)
- Flat dark panels (`#1a1a2e` / `#2a2a4a`), no glow, muted blue-grey accents
- Closest to the current qt-material dark_blue look

### Light Professional (option)
- White card panels with `1px #d0d5dd` borders, `#f0f2f5` background, solid `#2563eb` accent
- Clean drop shadows instead of glows

---

## Layout Modes

Three layout modes the user can switch between. Each mode reuses the same `FileListPanel`, `PreviewPanel`, and `SettingsPanel` components — only their arrangement changes.

### Compact Toolbar (new default)
- A slim settings toolbar spans the full width above the content area
- Contains: tab switcher (Single / Batch), format dropdown, quality slider, output folder button, Convert button
- Below the toolbar: `FileListPanel` (left, fixed ~200 px) | `PreviewPanel` (center, fills remaining space)
- `SettingsPanel` widget is retired; its controls move into the toolbar

### 3-Panel Horizontal (existing)
- Current layout: `FileListPanel` | `PreviewPanel` | `SettingsPanel` in a `QSplitter`
- Reskinned with the active visual style, no structural change

### Preview-First
- `PreviewPanel` dominates the full content area
- Settings toolbar at top (same as Compact Toolbar)
- Horizontal file thumbnail strip at the bottom (~72 px tall) replaces the vertical file list

---

## Appearance Dialog

### Access
- Menu bar: **Appearance** item (replaces the current **Theme** menu)
- Opens a non-modal `QDialog` subclass: `AppearanceDialog`

### Sections

#### Style
Three clickable cards showing a mini preview swatch:
- Minimal Dark / Modern Glass (default) / Light Professional
- Clicking a card applies the style live to the running app

#### Layout
Three clickable cards showing a schematic wireframe:
- 3-Panel / Compact Toolbar (default) / Preview-First
- Clicking a card reconstructs the main window layout live

#### Accent Color
- Three preset gradient swatches:
  1. Indigo → Violet (`#6450ff` → `#a040ff`) — default
  2. Blue → Cyan (`#0088dd` → `#00cccc`)
  3. Magenta → Rose (`#cc1177` → `#ff4499`)
- A color wheel button that opens `QColorDialog` for a fully custom color
- Custom color is stored as a single hex value; the gradient is generated as `color → color.lighter(130)`
- Clicking any swatch/picker applies the accent live

### Persistence
- All three settings saved to a JSON file: `~/.photoconverter/appearance.json`
- Loaded at startup before the main window is shown
- Schema: `{ "style": "modern_glass", "layout": "compact_toolbar", "accent": "#6450ff" }`

### Live Apply
- All changes apply immediately — no Apply/OK step needed
- Dialog has a single **Close** button

---

## Theming Architecture

Replace qt-material with a custom `ThemeManager` class (`ui/theme_manager.py`):

- `ThemeManager.apply(app, style, accent)` — builds and applies a `QStyleSheet` string to the `QApplication`
- Stylesheet is generated from a template with accent color injected as CSS variables (string substitution)
- Three template strings (one per style): `MINIMAL_DARK_TEMPLATE`, `MODERN_GLASS_TEMPLATE`, `LIGHT_PRO_TEMPLATE`
- `MainWindow` calls `ThemeManager.apply()` on startup and whenever the user changes style/accent

---

## Settings Persistence

New module: `settings.py` (project root)

- `load_appearance() -> AppearanceSettings` — reads `~/.photoconverter/appearance.json`, returns defaults if missing
- `save_appearance(settings: AppearanceSettings)` — writes atomically (write to `.tmp`, then rename)
- `AppearanceSettings` dataclass: `style: str`, `layout: str`, `accent: str`

---

## Components Added / Changed

| Component | Change |
|---|---|
| `ui/theme_manager.py` | New — stylesheet generation and apply logic |
| `ui/appearance_dialog.py` | New — `AppearanceDialog` QDialog |
| `ui/toolbar_panel.py` | New — settings toolbar widget for Compact Toolbar and Preview-First layouts |
| `ui/main_window.py` | Modified — layout switching, Appearance menu, startup settings load |
| `ui/settings_panel.py` | Kept for 3-Panel layout; controls duplicated into toolbar for other layouts |
| `settings.py` | New — persistence of appearance preferences |
| `requirements.txt` | Remove `qt-material`; no new dependencies (QColorDialog is built into Qt) |

---

## Out of Scope

- Animated transitions between layout switches
- Per-panel custom colors
- Exporting / importing theme profiles
