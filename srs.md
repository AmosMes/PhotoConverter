# PhotoConverter — Software Requirements Specification

## Overview

Cross-platform (Windows / macOS / Linux) desktop image converter with a native GUI. Converts between HEIF/HEIC and common formats (JPEG, PNG, PDF) in both directions, with a live preview and quality control.

---

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| GUI framework | PySide6 (official Qt6 binding, LGPL) |
| Theme | `qdarktheme` — modern flat dark/light/system |
| HEIF read/write | `pillow-heif` (registers with Pillow) |
| JPEG / PNG read/write | `Pillow` |
| PDF input (render pages) | `PyMuPDF` (fitz) |
| PDF output | `Pillow` (built-in PDF writer) |
| Packaging | `PyInstaller` |

---

## Supported Formats

**Input:** HEIF, HEIC, JPEG, JPG, PNG, PDF
**Output:** HEIF, JPEG, PNG, PDF

---

## Conversion Matrix

| Input | Output | Library path |
|---|---|---|
| HEIF/HEIC | JPEG / PNG | pillow-heif reads → Pillow writes |
| HEIF/HEIC | PDF | pillow-heif reads → Pillow writes PDF |
| JPEG / PNG | HEIF | Pillow reads → pillow-heif writes |
| JPEG / PNG | PDF | Pillow reads → Pillow writes PDF |
| PDF | HEIF / JPEG / PNG | PyMuPDF renders pages → pillow-heif / Pillow writes |

---

## Quality Control

| Output Format | Control | Behaviour |
|---|---|---|
| JPEG | Slider 1–100 | Lossy compression |
| HEIF | Slider 1–100 | Lossy compression |
| PNG | Slider 0–9 | Lossless — affects file size only |
| PDF | Disabled | Lossless — no quality setting |

---

## Multi-page PDF Input

When a PDF with more than one page is opened, a dialog is shown at conversion time. The user selects which pages to convert. Each selected page produces one output file, e.g. `document-page-1.heic`, `document-page-2.heic`.

---

## Theme

The user can manually switch between **Dark**, **Light**, and **System** (follows OS preference) via a dropdown in the top-right of the menu bar. Default: System.

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [File]  [Help]                          [◐ Theme: Dark ▾]  │
├─────────────────────────────────────────────────────────────┤
│  [ Single File ]  [ Batch ]                                  │
├──────────────────┬──────────────────────┬───────────────────┤
│                  │                      │  Output Format    │
│  📂 Open File(s) │                      │  [ JPEG      ▾]   │
│                  │    Preview           │                   │
│  ┌────────────┐  │    (centered,        │  Quality          │
│  │ file1.heic │  │     scaled to fit)   │  ──●────────  85  │
│  │ file2.jpg  │  │                      │                   │
│  │ file3.png  │  │  filename.heic       │  Output Folder    │
│  │            │  │  2048 × 1536 · HEIC  │  [📁 Browse... ]  │
│  └────────────┘  │                      │                   │
│  [+ Add] [- Del] │                      │  [ Convert ]      │
│                  │                      │                   │
├──────────────────┴──────────────────────┴───────────────────┤
│  ████████████████████░░░░░░░░  6 / 10 files   [Cancel]      │
└─────────────────────────────────────────────────────────────┘
```

- **Single File tab:** file list shows one item; button reads "Convert"
- **Batch tab:** multi-select file list; button reads "Convert All"
- **Progress bar:** hidden until conversion starts
- Clicking a file in the list updates the preview

---

## Project Structure

```
PhotoConverter/
├── main.py
├── srs.md
├── requirements.txt
├── ui/
│   ├── main_window.py
│   ├── preview_panel.py
│   ├── file_list_panel.py
│   └── settings_panel.py
└── converter/
    ├── worker.py
    ├── heif_converter.py
    └── pdf_handler.py
```
