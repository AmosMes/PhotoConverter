import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


def _resource_base() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def main():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "mesika.photoconverter.1"
        )
    app = QApplication(sys.argv)
    app.setApplicationName("PhotoConverter")
    ico_path = _resource_base() / "PhotoConverter.ico"
    icon = QIcon(str(ico_path)) if ico_path.exists() else QIcon()
    app.setWindowIcon(icon)
    window = MainWindow(app, icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
