import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow

_ICO = Path(__file__).parent / "PhotoConverter.ico"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PhotoConverter")
    if _ICO.exists():
        icon = QIcon(str(_ICO))
        app.setWindowIcon(icon)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
