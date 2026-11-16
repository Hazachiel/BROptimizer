"""Tabla interactiva con soporte completo para Drag & Drop y menú contextual."""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCursor, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView
)


class DropTableWidget(QTableWidget):
    """QTableWidget adaptado para aceptar archivos y carpetas mediante arrastrar y soltar."""

    items_dropped = Signal(list)  # Lista de paths absolutos como strings

    COL_NAME = 0
    COL_TYPE = 1
    COL_ORIG_SIZE = 2
    COL_FINAL_SIZE = 3
    COL_STATUS = 4

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)

        self._setup_columns()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_columns(self) -> None:
        headers = [
            "Elemento / Carpeta",
            "Motor / Tipo",
            "Tamaño Orig.",
            "Tamaño Final",
            "Estado / Progreso",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ORIG_SIZE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_FINAL_SIZE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        paths: list[str] = []
        for url in urls:
            path = url.toLocalFile()
            if path:
                paths.append(str(Path(path).resolve()))

        if paths:
            self.items_dropped.emit(paths)
            event.acceptProposedAction()

    def _show_context_menu(self, position) -> None:
        row = self.rowAt(position.y())
        if row < 0:
            return

        item = self.item(row, self.COL_NAME)
        if not item:
            return

        path_str = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        act_open_folder = QAction("📂 Abrir ubicación en explorador", self)
        act_open_folder.triggered.connect(lambda: self._open_location(path_str))
        menu.addAction(act_open_folder)

        act_remove = QAction("❌ Quitar de la lista", self)
        act_remove.triggered.connect(lambda: self._remove_selected_rows())
        menu.addAction(act_remove)

        menu.exec(QCursor.pos())

    def _open_location(self, path_str: str) -> None:
        p = Path(path_str)
        target = p.parent if p.is_file() else p
        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _remove_selected_rows(self) -> None:
        selected_rows = sorted({idx.row() for idx in self.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            self.removeRow(r)

