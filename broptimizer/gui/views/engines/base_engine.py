"""Clase base reutilizable para las vistas de cola de cada motor."""

from pathlib import Path
from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QProgressBar, QGroupBox, QTableWidgetItem
)

from broptimizer.config import Config, TargetCategory
from broptimizer.engines.detector import EngineDetector
from broptimizer.gui.widgets.drop_table import DropTableWidget
from broptimizer.gui.workers.detector_worker import SequentialDetectorQueue
from broptimizer.gui.workers.batch_worker import BatchOptimizationWorker


def format_bytes(size: int) -> str:
    """Convierte bytes a formato legible."""
    if size <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class BaseEngineQueueView(QWidget):
    """Clase base con tabla interactiva, botones comunes y ejecución secuencial."""

    folder_dropped_mismatch = Signal(str, str)  # folder_path, detected_engine_id

    def __init__(self, engine_id: str, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine_id = engine_id
        self.view_title = title
        self.detector_queue = SequentialDetectorQueue(self)
        self.batch_worker: BatchOptimizationWorker | None = None
        self._row_data: dict[str, dict[str, Any]] = {}

        self._setup_base_ui()
        self._connect_base_signals()

    def _setup_base_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(14, 12, 14, 12)
        self.main_layout.setSpacing(10)

        # 1. Barra superior de adición y limpieza
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.btn_add_files = QPushButton("➕ Añadir Archivos")
        self.btn_add_folder = QPushButton("📁 Añadir Carpeta")
        self.btn_remove = QPushButton("➖ Quitar Seleccionado")
        self.btn_clear = QPushButton("🧹 Limpiar Todo")

        action_bar.addWidget(self.btn_add_files)
        action_bar.addWidget(self.btn_add_folder)
        action_bar.addWidget(self.btn_remove)
        action_bar.addWidget(self.btn_clear)
        action_bar.addStretch()

        self.main_layout.addLayout(action_bar)

        # 2. Tabla central con Drag & Drop
        self.table = DropTableWidget()
        self.main_layout.addWidget(self.table, stretch=1)

        # 3. Contenedor de Opciones Rápidas Específicas
        self.options_group = QGroupBox(f"Opciones Rápidas: {self.view_title}")
        self.options_layout = QVBoxLayout(self.options_group)
        self.options_layout.setSpacing(8)
        self.setup_engine_options(self.options_layout)
        self.main_layout.addWidget(self.options_group)

        # 4. Barra Inferior de Ejecución
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Listo")

        self.btn_pause = QPushButton("⏸️ Pausar")
        self.btn_pause.setEnabled(False)
        self.btn_cancel = QPushButton("⏹️ Cancelar")
        self.btn_cancel.setEnabled(False)
        self.btn_start = QPushButton("▶️ INICIAR PROCESO")
        self.btn_start.setObjectName("PrimaryButton")

        bottom_bar.addWidget(self.progress_bar, stretch=1)
        bottom_bar.addWidget(self.btn_pause)
        bottom_bar.addWidget(self.btn_cancel)
        bottom_bar.addWidget(self.btn_start)

        self.main_layout.addLayout(bottom_bar)

    def setup_engine_options(self, layout: QVBoxLayout) -> None:
        """Método para ser sobreescrito por las subclases de cada motor."""
        pass

    def _connect_base_signals(self) -> None:
        self.btn_add_files.clicked.connect(self._on_add_files)
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        self.btn_remove.clicked.connect(self.table._remove_selected_rows)
        self.btn_clear.clicked.connect(self.clear_table)
        self.table.items_dropped.connect(self.handle_dropped_paths)

        # Worker detector
        self.detector_queue.signals.item_analysis_started.connect(self._on_analysis_started)
        self.detector_queue.signals.item_analysis_finished.connect(self._on_analysis_finished)

        # Botones de ejecución
        self.btn_start.clicked.connect(self.start_optimization)
        self.btn_pause.clicked.connect(self._pause_batch)
        self.btn_cancel.clicked.connect(self._cancel_batch)

    def clear_table(self) -> None:
        self.table.setRowCount(0)
        self._row_data.clear()

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos multimedia", "",
            "Multimedia (*.png *.jpg *.jpeg *.webp *.ogg *.mp3 *.wav *.mp4 *.webm *.mkv);;Todos los archivos (*.*)"
        )
        if files:
            self.handle_dropped_paths(files)

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder:
            self.handle_dropped_paths([folder])

    def handle_dropped_paths(self, paths: list[str]) -> None:
        """Verifica compatibilidad de motor y delega la inserción o redirección."""
        for p_str in paths:
            path = Path(p_str)
            if not path.exists():
                continue

            if path.is_dir():
                detected = EngineDetector.detect(path)
                target_view_id = self._map_engine_to_view_id(detected)

                # Si es una carpeta de juego que pertenece a otra vista, emitir redirección
                if target_view_id != self.engine_id and target_view_id != "engine_generic" and self.engine_id != "engine_generic":
                    self.folder_dropped_mismatch.emit(str(path), target_view_id)
                    continue

            self._insert_row(path)

    def _map_engine_to_view_id(self, detected_engine) -> str:
        if not detected_engine:
            return "engine_generic"
        ename = detected_engine.name.lower()
        if "mv" in ename or "mz" in ename:
            return "engine_rpgmaker"
        elif "xp" in ename or "vx" in ename or "rgss" in ename:
            return "engine_legacy_rpg"
        elif "renpy" in ename or "ren'py" in ename:
            return "engine_renpy"
        elif "wolf" in ename:
            return "engine_wolfrpg"
        return "engine_generic"

    def _insert_row(self, path: Path) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        item_name = QTableWidgetItem(f"📁 {path.name}" if path.is_dir() else f"📄 {path.name}")
        item_name.setData(Qt.ItemDataRole.UserRole, str(path))
        self.table.setItem(row, DropTableWidget.COL_NAME, item_name)

        item_type = QTableWidgetItem("En espera...")
        self.table.setItem(row, DropTableWidget.COL_TYPE, item_type)

        item_orig = QTableWidgetItem("Calculando...")
        self.table.setItem(row, DropTableWidget.COL_ORIG_SIZE, item_orig)

        item_final = QTableWidgetItem("--")
        self.table.setItem(row, DropTableWidget.COL_FINAL_SIZE, item_final)

        item_status = QTableWidgetItem("En cola de análisis")
        self.table.setItem(row, DropTableWidget.COL_STATUS, item_status)

        item_id = str(row)
        self._row_data[item_id] = {"path": str(path), "row": row, "orig_size": 0}
        self.detector_queue.add_item(item_id, str(path))

    def _on_analysis_started(self, item_id: str) -> None:
        if item_id in self._row_data:
            row = self._row_data[item_id]["row"]
            status_item = self.table.item(row, DropTableWidget.COL_STATUS)
            if status_item:
                status_item.setText("Analizando motor y peso...")

    def _on_analysis_finished(self, item_id: str, engine_name: str, total_size: int) -> None:
        if item_id in self._row_data:
            row = self._row_data[item_id]["row"]
            self._row_data[item_id]["orig_size"] = total_size

            type_item = self.table.item(row, DropTableWidget.COL_TYPE)
            if type_item:
                type_item.setText(engine_name)

            orig_item = self.table.item(row, DropTableWidget.COL_ORIG_SIZE)
            if orig_item:
                orig_item.setText(format_bytes(total_size))

            status_item = self.table.item(row, DropTableWidget.COL_STATUS)
            if status_item:
                status_item.setText("Listo")

    def get_engine_specific_options(self) -> dict[str, Any]:
        """Devuelve diccionario con las opciones marcadas en los checkboxes."""
        return {
            "decrypt": False,
            "delete_encrypted": False,
            "overwrite_smaller": True,
            "apply_nwjs_clean": False,
        }

    def start_optimization(self) -> None:
        total_rows = self.table.rowCount()
        if total_rows == 0:
            return

        jobs = []
        for r in range(total_rows):
            name_item = self.table.item(r, DropTableWidget.COL_NAME)
            if not name_item:
                continue
            path_str = name_item.data(Qt.ItemDataRole.UserRole)
            orig_size = 0
            for item_id, data in self._row_data.items():
                if data["row"] == r:
                    orig_size = data["orig_size"]
                    break

            jobs.append({
                "row": r,
                "path": path_str,
                "orig_size": orig_size,
            })

        options = self.get_engine_specific_options()

        # Determinar overrides si la vista específica provee preferencias
        overrides = {}
        if "preserve_extension" in options:
            overrides["preserve_extension"] = options["preserve_extension"]
        if "target_video_codec" in options and options["target_video_codec"]:
            codec_raw = options["target_video_codec"].lower()
            if "h.264" in codec_raw or "h264" in codec_raw:
                overrides["video_codec"] = "h264"
            elif "vp9" in codec_raw:
                overrides["video_codec"] = "vp9"
            elif "vp8" in codec_raw:
                overrides["video_codec"] = "vp8"

        # Cargar configuración desde broptimizer_settings.json con fallback robusto a defaults (h264, crf 26)
        cfg = Config.load_from_settings(**overrides)

        # Directorio temporal personalizado si está configurado en las preferencias de sistema
        from broptimizer.gui.views.preferences.pref_storage import load_all_settings
        sys_settings = load_all_settings()
        custom_temp = (
            sys_settings.get("temp_folder_custom")
            if sys_settings.get("use_custom_temp") and sys_settings.get("temp_folder_custom")
            else None
        )

        self.batch_worker = BatchOptimizationWorker(
            jobs=jobs,
            base_config=cfg,
            custom_temp_dir=custom_temp,
            apply_nwjs_clean=options.get("apply_nwjs_clean", False),
            overwrite_smaller=options.get("overwrite_smaller", True),
            parent=self,
        )

        self.batch_worker.item_started.connect(self._on_job_started)
        self.batch_worker.item_status_update.connect(self._on_job_status)
        self.batch_worker.item_finished.connect(self._on_job_finished)
        self.batch_worker.item_error.connect(self._on_job_error)
        self.batch_worker.batch_finished.connect(self._on_batch_complete)

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Procesando lote...")

        self.batch_worker.start()

    def _on_job_started(self, row: int, item_name: str) -> None:
        self.table.selectRow(row)

    def _on_job_status(self, row: int, status_text: str) -> None:
        item = self.table.item(row, DropTableWidget.COL_STATUS)
        if item:
            item.setText(status_text)

    def _on_job_finished(self, row: int, final_size: int, savings: float) -> None:
        final_item = self.table.item(row, DropTableWidget.COL_FINAL_SIZE)
        if final_item:
            final_item.setText(f"{format_bytes(final_size)} (-{savings:.1f}%)")
            final_item.setForeground(Qt.GlobalColor.green)

        status_item = self.table.item(row, DropTableWidget.COL_STATUS)
        if status_item:
            status_item.setText("✔ Completado")
            status_item.setForeground(Qt.GlobalColor.green)

    def _on_job_error(self, row: int, error_msg: str) -> None:
        status_item = self.table.item(row, DropTableWidget.COL_STATUS)
        if status_item:
            status_item.setText("❌ Error")
            status_item.setForeground(Qt.GlobalColor.red)
            status_item.setToolTip(error_msg)

    def _on_batch_complete(self) -> None:
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Lote completado con éxito")

    def _pause_batch(self) -> None:
        if self.batch_worker:
            if self.btn_pause.text().startswith("⏸️"):
                self.batch_worker.pause()
                self.btn_pause.setText("▶️ Reanudar")
            else:
                self.batch_worker.resume()
                self.btn_pause.setText("⏸️ Pausar")

    def _cancel_batch(self) -> None:
        if self.batch_worker:
            self.batch_worker.cancel()
            self.btn_cancel.setEnabled(False)
            self.progress_bar.setFormat("Cancelación solicitada...")

