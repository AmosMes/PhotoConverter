from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from converter.heif_converter import convert_image
from converter.pdf_handler import pdf_page_count, render_pdf_page


@dataclass
class ConversionJob:
    src_path: str
    dst_dir: str
    output_format: str
    quality: int = 85
    # For PDF input only — None means "ask before starting" (handled by main window)
    pdf_pages: list[int] | None = None
    rotation: int = 0


class ConversionWorker(QThread):
    progress = Signal(int, int)   # current, total
    file_done = Signal(str, str)  # src_path, dst_path
    file_error = Signal(str, str) # src_path, error_message
    finished = Signal()

    def __init__(self, jobs: list[ConversionJob], parent=None):
        super().__init__(parent)
        self._jobs = jobs
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        # Expand PDF jobs into per-page subjobs first to get accurate total
        expanded: list[tuple] = []  # (src, dst_dir, fmt, quality, pil_image_or_none, stem, rotation)
        for job in self._jobs:
            ext = Path(job.src_path).suffix.lower()
            if ext == ".pdf" and job.pdf_pages is not None:
                for idx in job.pdf_pages:
                    stem = f"{Path(job.src_path).stem}-page-{idx + 1}"
                    expanded.append((job.src_path, job.dst_dir, job.output_format, job.quality, idx, stem, job.rotation))
            else:
                expanded.append((job.src_path, job.dst_dir, job.output_format, job.quality, None, None, job.rotation))

        total = len(expanded)
        for i, (src, dst_dir, fmt, quality, pdf_page_idx, stem, rotation) in enumerate(expanded):
            if self._cancelled:
                break
            try:
                pil_image = render_pdf_page(src, pdf_page_idx) if pdf_page_idx is not None else None
                dst = convert_image(src, dst_dir, fmt, quality, pil_image=pil_image, stem_override=stem, rotation=rotation)
                self.file_done.emit(src, dst)
            except Exception as exc:
                self.file_error.emit(src, str(exc))
            self.progress.emit(i + 1, total)

        self.finished.emit()
