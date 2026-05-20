# PhotoConverter

A desktop application for converting images between JPEG, PNG, HEIF, and PDF formats. Supports single-file and batch conversion, PDF page selection, and a fully customisable appearance.

---

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt` (installed automatically by the run scripts)

---

## Running without building

The quickest way to run the app is directly from source — no compilation step needed.

**Windows**

```powershell
.\run_windows.ps1
```

**Linux**

```bash
chmod +x run_linux.sh
./run_linux.sh
```

Both scripts install any missing dependencies from `requirements.txt` and launch the app.

---

## Building a standalone binary

The build scripts use PyInstaller to produce a single self-contained executable.

**Windows** — produces `dist\PhotoConverter.exe`

```powershell
.\build_windows.ps1
```

**Linux** — produces `dist/PhotoConverter`

```bash
chmod +x build_linux.sh
./build_linux.sh
```

> **Linux note:** `pillow-heif` requires `libheif` at runtime. The build script installs it automatically via `apt-get` if it is not already present.

---

## Using the application

### Single conversion

1. Launch the app.
2. Click **Open File…** (or `Ctrl+O`) and select an image or PDF.
3. A preview of the selected file appears in the centre panel.
4. Choose an **Output Format** (JPEG, PNG, HEIF, or PDF).
5. Adjust **Quality** (JPEG/HEIF) or **Compression** (PNG) with the slider. The slider is disabled for PDF output.
6. Optionally set an **Output Folder**; if left blank the converted file is saved next to the source.
7. Click **Convert**.

### Batch conversion

1. Click **Open Files (Batch)…** (or `Ctrl+Shift+O`) and select multiple files.
2. All selected files appear in the file list.
3. Choose format, quality, and output folder as above.
4. Click **Convert All** — files are converted one by one and progress is shown in the status bar.

### PDF input — page selection

When a PDF is opened, a page picker dialog appears before conversion starts. Select which pages to extract; each selected page is saved as a separate image file.

### Appearance

Open **Appearance…** from the menu bar to customise the look of the app. All changes apply instantly — no restart needed.

| Setting | Options |
|---|---|
| **Style** | Modern Glass (default) · Minimal Dark · Light Professional |
| **Layout** | Compact Toolbar (default) · 3-Panel · Preview-First |
| **Accent color** | 3 preset gradients or any custom color via the OS color picker |

Preferences are saved automatically and restored on the next launch.
