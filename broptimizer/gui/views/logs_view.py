"""Vista para historial y visualización del archivo de logs de actividad y errores."""

from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QComboBox
)

from broptimizer.logger import ACTIVITY_LOG_FILE_PATH, LOG_FILE_PATH


class LogsView(QWidget):
    """Visor en tiempo real de broptimizer_activity.log y broptimizer_errors.log."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.activity_log_path = ACTIVITY_LOG_FILE_PATH
        self.error_log_path = LOG_FILE_PATH
        self.current_log_path = self.activity_log_path
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header con selector y acciones
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title = QLabel("📋 Historial y Logs:")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #F8FAFC;")
        top_bar.addWidget(title)

        self.combo_log_type = QComboBox()
        self.combo_log_type.addItem("📄 Registro de Actividad y Conversión", str(self.activity_log_path))
        self.combo_log_type.addItem("⚠️ Registro de Errores y Excepciones", str(self.error_log_path))
        self.combo_log_type.currentIndexChanged.connect(self._on_log_type_changed)
        top_bar.addWidget(self.combo_log_type)

        top_bar.addStretch()

        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.clicked.connect(self.reload_logs)
        top_bar.addWidget(self.btn_refresh)

        self.btn_open_file = QPushButton("📂 Abrir archivo en disco")
        self.btn_open_file.clicked.connect(self._open_log_file)
        top_bar.addWidget(self.btn_open_file)

        self.btn_clear = QPushButton("🧹 Limpiar log")
        self.btn_clear.clicked.connect(self._clear_log)
        top_bar.addWidget(self.btn_clear)

        layout.addLayout(top_bar)

        # Visor de texto
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "background-color: #16181D; border: 1px solid #2D3748; "
            "color: #CBD5E1; font-family: 'Consolas', monospace; font-size: 12px; padding: 8px;"
        )
        layout.addWidget(self.log_text)

        self.reload_logs()

    def _on_log_type_changed(self, index: int) -> None:
        path_str = self.combo_log_type.currentData()
        if path_str:
            self.current_log_path = Path(path_str)
            self.reload_logs()

    def reload_logs(self) -> None:
        """Carga el contenido del archivo de log actualmente seleccionado."""
        if not self.current_log_path.exists():
            self.log_text.setPlainText("El archivo de log está limpio. No se han registrado entradas aún.")
            return

        try:
            content = self.current_log_path.read_text(encoding="utf-8", errors="replace")
            self.log_text.setPlainText(content if content.strip() else "El archivo de log está actualmente vacío.")
            # Mover scroll al final
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
        except Exception as exc:
            self.log_text.setPlainText(f"Error al leer el archivo de log: {exc}")

    def _open_log_file(self) -> None:
        if self.current_log_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_log_path)))

    def _clear_log(self) -> None:
        if self.current_log_path.exists():
            try:
                self.current_log_path.write_text("", encoding="utf-8")
                self.reload_logs()
            except Exception:
                pass


