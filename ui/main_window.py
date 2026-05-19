from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget,
    QHBoxLayout, QVBoxLayout, QSplitter,
    QProgressBar, QStatusBar, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from ui.file_list_panel import FileListPanel
from ui.preview_panel import PreviewPanel
from ui.settings_panel import SettingsPanel
from converter.worker import ConversionWorker, ConversionJob
from converter.pdf_handler import PagePickerDialog, pdf_page_count
from version import VERSION, AUTHOR


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self._worker: ConversionWorker | None = None
        self.setWindowTitle(f"PhotoConverter {VERSION}")
        self.resize(1100, 680)
        self._build_ui()

    def _build_ui(self):
        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Tabs ---
        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs, stretch=1)

        # Single file tab
        self._single_panel = self._build_mode_panel(multi=False)
        self._tabs.addTab(self._single_panel["widget"], "Single File")

        # Batch tab
        self._batch_panel = self._build_mode_panel(multi=True)
        self._tabs.addTab(self._batch_panel["widget"], "Batch")

        # Connect after both panels exist
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # --- Progress bar ---
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        main_layout.addWidget(self._progress)

        # --- Status bar ---
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        # --- Menu bar ---
        menu = self.menuBar()

        # File menu
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

        # Help menu
        help_menu = menu.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    @staticmethod
    def _framed(widget: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panelFrame")
        frame.setStyleSheet(
            "QFrame#panelFrame { border: 1px solid rgba(128,128,128,0.35);"
            " border-radius: 6px; }"
        )
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.addWidget(widget)
        return frame

    def _build_mode_panel(self, multi: bool) -> dict:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)

        file_list = FileListPanel(multi=multi)
        preview = PreviewPanel()
        settings = SettingsPanel()
        settings.set_convert_button_text("Convert All" if multi else "Convert")

        file_list.setMinimumWidth(180)
        file_list.setMaximumWidth(260)
        settings.setMinimumWidth(200)
        settings.setMaximumWidth(280)

        splitter.addWidget(self._framed(file_list))
        splitter.addWidget(self._framed(preview))
        splitter.addWidget(self._framed(settings))
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        file_list.selection_changed.connect(
            lambda path: preview.load_file(path) if path else preview.clear()
        )
        settings.convert_requested.connect(
            lambda: self._start_conversion(file_list, settings)
        )

        return {"widget": widget, "file_list": file_list, "preview": preview, "settings": settings}

    def _active_panel(self) -> dict:
        return self._single_panel if self._tabs.currentIndex() == 0 else self._batch_panel

    def _on_tab_changed(self, _index: int):
        self._single_panel["settings"].set_convert_button_text("Convert")
        self._batch_panel["settings"].set_convert_button_text("Convert All")

    def _menu_open_file(self):
        self._tabs.setCurrentIndex(0)
        self._single_panel["file_list"].open_files()

    def _menu_open_batch(self):
        self._tabs.setCurrentIndex(1)
        self._batch_panel["file_list"].open_files()

    def _start_conversion(self, file_list: FileListPanel, settings: SettingsPanel):
        paths = file_list.all_paths()
        if not paths:
            QMessageBox.warning(self, "No Files", "Please add at least one file to convert.")
            return

        output_format = settings.output_format()
        quality = settings.quality()
        dst_dir = settings.output_dir()

        jobs: list[ConversionJob] = []
        for path in paths:
            ext = Path(path).suffix.lower()
            if ext == ".pdf":
                count = pdf_page_count(path)
                if count > 1:
                    dlg = PagePickerDialog(path, self)
                    if dlg.exec() != dlg.DialogCode.Accepted:
                        continue
                    pages = dlg.selected_page_indices()
                    if not pages:
                        continue
                else:
                    pages = [0]
            else:
                pages = None

            effective_dst = dst_dir if dst_dir else str(Path(path).parent)
            jobs.append(ConversionJob(path, effective_dst, output_format, quality, pages))

        if not jobs:
            return

        self._set_converting(True, len(jobs))
        self._worker = ConversionWorker(jobs, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(lambda src, dst: self._status.showMessage(f"Done: {Path(dst).name}"))
        self._worker.file_error.connect(self._on_file_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        self._progress.setFormat(f"{current} / {total} files")

    def _on_file_error(self, src: str, msg: str):
        self._status.showMessage(f"Error converting {Path(src).name}: {msg}")

    def _on_finished(self):
        self._set_converting(False)
        self._status.showMessage("Conversion complete.")

    def _set_converting(self, active: bool, total: int = 0):
        self._progress.setVisible(active)
        if active:
            self._progress.setMaximum(total)
            self._progress.setValue(0)
        for panel in (self._single_panel, self._batch_panel):
            panel["settings"].set_convert_button_enabled(not active)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About PhotoConverter",
            f"PhotoConverter  v{VERSION}\n\n"
            f"Created by {AUTHOR}\n\n"
            "Convert between HEIF, JPEG, PNG, and PDF.\n\n"
            "Built with Python, PySide6, Pillow, pillow-heif, and PyMuPDF.",
        )
