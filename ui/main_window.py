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

from settings import load_appearance, AppearanceSettings
from ui.theme_manager import ThemeManager
from ui.toolbar_panel import ToolbarPanel
from ui.appearance_dialog import AppearanceDialog


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self._worker: ConversionWorker | None = None
        self._appearance = load_appearance()
        self.setWindowTitle(f"PhotoConverter {VERSION}")
        self.resize(1100, 680)
        ThemeManager.apply(self._app, self._appearance.style, self._appearance.accent)
        self._rebuild_ui(self._appearance)

    def _rebuild_ui(self, appearance: AppearanceSettings):
        old = self.centralWidget()
        if old:
            old.deleteLater()

        if not hasattr(self, "_status"):
            self._status = QStatusBar()
            self.setStatusBar(self._status)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)

        if appearance.layout == "compact_toolbar":
            self._build_compact_toolbar_ui()
        elif appearance.layout == "three_panel":
            self._build_three_panel_ui()
        else:
            self._build_preview_first_ui()

        self._build_menu()

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

    def _open_appearance(self):
        if hasattr(self, "_appearance_dlg") and self._appearance_dlg.isVisible():
            self._appearance_dlg.raise_()
            self._appearance_dlg.activateWindow()
            return
        self._appearance_dlg = AppearanceDialog(self._app, self._appearance, self)
        self._appearance_dlg.appearance_changed.connect(self._on_appearance_changed)
        self._appearance_dlg.show()

    def _on_appearance_changed(self, new_settings: AppearanceSettings):
        if self._worker and self._worker.isRunning():
            return  # ignore appearance changes while a conversion is in progress
        layout_changed = new_settings.layout != self._appearance.layout
        self._appearance = new_settings
        if layout_changed:
            ThemeManager.apply(self._app, new_settings.style, new_settings.accent)
            self._rebuild_ui(new_settings)
        else:
            ThemeManager.apply(self._app, new_settings.style, new_settings.accent)

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

    def _build_compact_toolbar_ui(self):
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
        self._toolbar.set_convert_button_text("Convert All" if index == 1 else "Convert")

    def _start_conversion_from_toolbar(self):
        body = self._batch_body if self._toolbar.active_tab() == 1 else self._single_body
        self._start_conversion(body["file_list"], self._toolbar)

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

        self._preview_pf = PreviewPanel()
        main_layout.addWidget(self._framed(self._preview_pf), stretch=1)

        strip_container = QWidget()
        strip_container.setFixedHeight(72)
        strip_layout = QHBoxLayout(strip_container)
        strip_layout.setContentsMargins(0, 0, 0, 0)

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
        self._toolbar.set_convert_button_text("Convert All" if index == 1 else "Convert")

    def _start_conversion_from_preview_first(self):
        fl = self._batch_file_list if self._toolbar.active_tab() == 1 else self._single_file_list
        self._start_conversion(fl, self._toolbar)

    @staticmethod
    def _framed(widget: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panelFrame")
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

    def _on_tab_changed(self, _index: int):
        self._single_panel["settings"].set_convert_button_text("Convert")
        self._batch_panel["settings"].set_convert_button_text("Convert All")

    def _menu_open_file(self):
        if self._appearance.layout == "three_panel":
            self._tabs.setCurrentIndex(0)
            self._single_panel["file_list"].open_files()
        elif self._appearance.layout == "compact_toolbar":
            self._toolbar.switch_tab(0)
            self._single_body["file_list"].open_files()
        else:
            self._toolbar.switch_tab(0)
            self._single_file_list.open_files()

    def _menu_open_batch(self):
        if self._appearance.layout == "three_panel":
            self._tabs.setCurrentIndex(1)
            self._batch_panel["file_list"].open_files()
        elif self._appearance.layout == "compact_toolbar":
            self._toolbar.switch_tab(1)
            self._batch_body["file_list"].open_files()
        else:
            self._toolbar.switch_tab(1)
            self._batch_file_list.open_files()

    def _start_conversion(self, file_list: FileListPanel, settings):
        paths = file_list.all_paths()
        if not paths:
            QMessageBox.warning(self, "No Files", "Please add at least one file to convert.")
            return

        output_format = settings.output_format()
        quality = settings.quality()
        dst_dir = settings.output_dir()
        rotation = settings.rotation() if hasattr(settings, "rotation") else 0

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
            jobs.append(ConversionJob(path, effective_dst, output_format, quality, pages, rotation=rotation))

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
        if self._appearance.layout == "three_panel":
            for panel in (self._single_panel, self._batch_panel):
                panel["settings"].set_convert_button_enabled(not active)
        else:
            self._toolbar.set_convert_button_enabled(not active)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About PhotoConverter",
            f"PhotoConverter  v{VERSION}\n\n"
            f"Created by {AUTHOR}\n\n"
            "Convert between HEIF, JPEG, PNG, and PDF.\n\n"
            "Built with Python, PySide6, Pillow, pillow-heif, and PyMuPDF.",
        )
