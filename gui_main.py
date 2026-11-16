"""Punto de entrada de la interfaz gráfica de BROptimizer."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from broptimizer.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("BROptimizer")
    app.setOrganizationName("BROptimizer")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
