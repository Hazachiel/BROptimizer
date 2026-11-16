"""Pruebas unitarias para la nueva GUI de BROptimizer."""

import sys
import unittest
from PySide6.QtWidgets import QApplication

from broptimizer.gui.main_window import MainWindow
from broptimizer.gui.widgets.drop_table import DropTableWidget


class TestNewGUI(unittest.TestCase):
    """Verifica la inicialización, componentes y vistas de la nueva GUI."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_main_window_structure(self):
        win = MainWindow()
        self.assertEqual(win.stack.count(), 4)
        self.assertIsNotNone(win.banner)
        self.assertIsNotNone(win.sidebar)

        # Cambios de vista mediante el sidebar
        win.sidebar.view_changed.emit(1)
        self.assertEqual(win.stack.currentIndex(), 1)
        win.sidebar.view_changed.emit(3)
        self.assertEqual(win.stack.currentIndex(), 3)
        win.sidebar.view_changed.emit(0)
        self.assertEqual(win.stack.currentIndex(), 0)

    def test_queue_view_table_columns(self):
        win = MainWindow()
        table = win.queue_view.table
        self.assertEqual(table.columnCount(), 5)
        self.assertEqual(table.horizontalHeaderItem(DropTableWidget.COL_NAME).text(), "Elemento / Carpeta")
        self.assertEqual(table.horizontalHeaderItem(DropTableWidget.COL_TYPE).text(), "Motor / Tipo")
        self.assertEqual(table.horizontalHeaderItem(DropTableWidget.COL_ORIG_SIZE).text(), "Tamaño Orig.")
        self.assertEqual(table.horizontalHeaderItem(DropTableWidget.COL_FINAL_SIZE).text(), "Tamaño Final")
        self.assertEqual(table.horizontalHeaderItem(DropTableWidget.COL_STATUS).text(), "Estado / Progreso")


if __name__ == "__main__":
    unittest.main()

