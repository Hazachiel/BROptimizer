"""Vista principal de la Cola de Optimización con Drag & Drop, 3 columnas y destino."""

import os
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QComboBox, QSlider, QCheckBox, QRadioButton,
    QProgressBar, QLineEdit, QTableWidgetItem
)

from broptimizer.config import Config, TargetCategory
from broptimizer.gui.widgets.drop_table import DropTableWidget
from broptimizer.gui.workers.detector_worker import SequentialDetectorQueue
from broptimizer.gui.workers.batch_worker import BatchOptimizationWorker


def format_bytes(size: int) -> str:
    """Convierte bytes a formato legible (KB, MB, GB)."""
    if size <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class QueueView(QWidget):
    """Vista de cola por lotes y opciones rápidas."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.detector_queue = SequentialDetectorQueue(self)
        self.batch_worker: BatchOptimizationWorker | None = None
        self._row_data: dict[str, dict] = {}  # row_id -> data

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Barra superior de adición
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

        main_layout.addLayout(action_bar)

        # 2. Tabla central con Drag & Drop
        self.table = DropTableWidget()
        main_layout.addWidget(self.table, stretch=1)

        # 3. Opciones Rápidas en 3 Columnas
        options_group = QGroupBox("Opciones Rápidas de Optimización")
        cols_layout = QHBoxLayout(options_group)
        cols_layout.setSpacing(14)

        max_cpu = os.cpu_count() or 4
        max_vid = max(1, max_cpu // 2)

        # --- Columna 1: Imágenes ---
        img_box = QGroupBox("🖼️ Imágenes")
        img_layout = QVBoxLayout(img_box)
        img_layout.setSpacing(6)

        img_fmt_lbl = QLabel("Formato (solo archivos genéricos):")
        self.combo_img_fmt = QComboBox()
        self.combo_img_fmt.addItems(["WebP (Recomendado)", "PNG (Optimizado)", "JPEG (Compatibildiad)"])

        self.lbl_img_threads = QLabel(f"Hilos de CPU: {max_cpu}")
        self.slider_img_threads = QSlider(Qt.Orientation.Horizontal)
        self.slider_img_threads.setRange(1, max_cpu)
        self.slider_img_threads.setValue(max_cpu)
        self.slider_img_threads.valueChanged.connect(
            lambda v: self.lbl_img_threads.setText(f"Hilos de CPU: {v}")
        )

        img_layout.addWidget(img_fmt_lbl)
        img_layout.addWidget(self.combo_img_fmt)
        img_layout.addWidget(self.lbl_img_threads)
        img_layout.addWidget(self.slider_img_threads)
        img_layout.addStretch()
        cols_layout.addWidget(img_box)

        # --- Columna 2: Audio ---
        aud_box = QGroupBox("🎵 Audio")
        aud_layout = QVBoxLayout(aud_box)
        aud_layout.setSpacing(6)

        aud_fmt_lbl = QLabel("Formato (solo archivos genéricos):")
        self.combo_aud_fmt = QComboBox()
        self.combo_aud_fmt.addItems(["Vorbis / OGG", "Opus / OGG", "MP3"])

        self.lbl_aud_threads = QLabel(f"Hilos de CPU: {max_cpu}")
        self.slider_aud_threads = QSlider(Qt.Orientation.Horizontal)
        self.slider_aud_threads.setRange(1, max_cpu)
        self.slider_aud_threads.setValue(max_cpu)
        self.slider_aud_threads.valueChanged.connect(
            lambda v: self.lbl_aud_threads.setText(f"Hilos de CPU: {v}")
        )

        aud_layout.addWidget(aud_fmt_lbl)
        aud_layout.addWidget(self.combo_aud_fmt)
        aud_layout.addWidget(self.lbl_aud_threads)
        aud_layout.addWidget(self.slider_aud_threads)
        aud_layout.addStretch()
        cols_layout.addWidget(aud_box)

        # --- Columna 3: Video ---
        vid_box = QGroupBox("🎬 Video")
        vid_layout = QVBoxLayout(vid_box)
        vid_layout.setSpacing(6)

        vid_codec_lbl = QLabel("Códec:")
        self.combo_vid_codec = QComboBox()
        self.combo_vid_codec.addItems(["VP8 (Webm rápido)", "VP9 (webm lento)", "H.264 (mp4 muy rápido)"])

        vid_crf_lbl = QLabel("Compresión CRF:")
        self.combo_vid_crf = QComboBox()
        self.combo_vid_crf.addItems(["26 (Equilibrado)", "15 (Alta calidad)", "31 (Máx. ahorro)"])

        self.lbl_vid_threads = QLabel("Videos simultáneos: 1")
        self.slider_vid_threads = QSlider(Qt.Orientation.Horizontal)
        self.slider_vid_threads.setRange(1, max_vid)
        self.slider_vid_threads.setValue(1)
        self.slider_vid_threads.valueChanged.connect(
            lambda v: self.lbl_vid_threads.setText(f"Videos simultáneos: {v}")
        )

        vid_layout.addWidget(vid_codec_lbl)
        vid_layout.addWidget(self.combo_vid_codec)
        vid_layout.addWidget(vid_crf_lbl)
        vid_layout.addWidget(self.combo_vid_crf)
        vid_layout.addWidget(self.lbl_vid_threads)
        vid_layout.addWidget(self.slider_vid_threads)
        cols_layout.addWidget(vid_box)

        main_layout.addWidget(options_group)

        # Nota sutil sobre motores
        note_lbl = QLabel("ℹ️ Los juegos detectados (RPG Maker, Ren'Py, etc.) preservan automáticamente las extensiones de archivo originales requeridas por su motor.")
        note_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic; margin-left: 4px;")
        main_layout.addWidget(note_lbl)

        # 4. Destino y Modos
        dest_group = QGroupBox("Ubicación Temporal y Reglas de Sustitución")
        dest_layout = QVBoxLayout(dest_group)
        dest_layout.setSpacing(6)

        # Selector de ubicación temporal
        temp_radio_layout = QHBoxLayout()
        self.radio_temp_default = QRadioButton("Carpeta temporal predeterminada")
        self.radio_temp_default.setChecked(True)
        self.radio_temp_custom = QRadioButton("Carpeta temporal personalizada:")

        self.edit_custom_temp = QLineEdit()
        self.edit_custom_temp.setPlaceholderText("Seleccionar directorio para archivos temporales...")
        self.edit_custom_temp.setEnabled(False)
        self.btn_browse_temp = QPushButton("...")
        self.btn_browse_temp.setEnabled(False)
        self.btn_browse_temp.setMaximumWidth(40)

        self.radio_temp_custom.toggled.connect(self._toggle_custom_temp)
        self.btn_browse_temp.clicked.connect(self._browse_custom_temp)

        temp_radio_layout.addWidget(self.radio_temp_default)
        temp_radio_layout.addSpacing(20)
        temp_radio_layout.addWidget(self.radio_temp_custom)
        temp_radio_layout.addWidget(self.edit_custom_temp)
        temp_radio_layout.addWidget(self.btn_browse_temp)
        dest_layout.addLayout(temp_radio_layout)

        # Checkboxes de comportamiento
        chk_layout = QHBoxLayout()
        self.chk_overwrite_smaller = QCheckBox("Sobreescribir solo si el resultado final es más pequeño")
        self.chk_overwrite_smaller.setChecked(True)

        self.chk_nwjs_clean = QCheckBox("Aplicar parche y limpieza NW.js (juegos RPG Maker compatibles)")
        self.chk_nwjs_clean.setChecked(True)

        chk_layout.addWidget(self.chk_overwrite_smaller)
        chk_layout.addSpacing(25)
        chk_layout.addWidget(self.chk_nwjs_clean)
        chk_layout.addStretch()
        dest_layout.addLayout(chk_layout)

        main_layout.addWidget(dest_group)

        # 5. Barra Inferior de Ejecución
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Listo para optimizar")

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

        main_layout.addLayout(bottom_bar)

    def _connect_signals(self) -> None:
        self.btn_add_files.clicked.connect(self._on_add_files)
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        self.btn_remove.clicked.connect(self.table._remove_selected_rows)
        self.btn_clear.clicked.connect(self.table.setRowCount)
        self.table.items_dropped.connect(self.add_paths)

        # Worker detector
        self.detector_queue.signals.item_analysis_started.connect(self._on_analysis_started)
        self.detector_queue.signals.item_analysis_finished.connect(self._on_analysis_finished)

        # Botones de ejecución
        self.btn_start.clicked.connect(self._start_batch)
        self.btn_pause.clicked.connect(self._pause_batch)
        self.btn_cancel.clicked.connect(self._cancel_batch)

    def _toggle_custom_temp(self, checked: bool) -> None:
        self.edit_custom_temp.setEnabled(checked)
        self.btn_browse_temp.setEnabled(checked)

    def _browse_custom_temp(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para archivos temporales")
        if folder:
            self.edit_custom_temp.setText(folder)

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos multimedia", "",
            "Multimedia (*.png *.jpg *.jpeg *.webp *.ogg *.mp3 *.wav *.mp4 *.webm *.mkv);;Todos los archivos (*.*)"
        )
        if files:
            self.add_paths(files)

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de juego o assets")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths: list[str]) -> None:
        """Añade elementos a la tabla y los envía a la cola secuencial de detección."""
        for p_str in paths:
            path = Path(p_str)
            if not path.exists():
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Nombre
            item_name = QTableWidgetItem(f"📁 {path.name}" if path.is_dir() else f"📄 {path.name}")
            item_name.setData(Qt.ItemDataRole.UserRole, str(path))
            self.table.setItem(row, DropTableWidget.COL_NAME, item_name)

            # Motor / Tipo
            item_type = QTableWidgetItem("En espera...")
            self.table.setItem(row, DropTableWidget.COL_TYPE, item_type)

            # Tamaño Orig
            item_orig = QTableWidgetItem("Calculando...")
            self.table.setItem(row, DropTableWidget.COL_ORIG_SIZE, item_orig)

            # Tamaño Final
            item_final = QTableWidgetItem("--")
            self.table.setItem(row, DropTableWidget.COL_FINAL_SIZE, item_final)

            # Estado
            item_status = QTableWidgetItem("En cola de análisis")
            self.table.setItem(row, DropTableWidget.COL_STATUS, item_status)

            # Registrar en cola secuencial
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

    def _start_batch(self) -> None:
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

        # Mapear codec
        codec_map = {0: "vp8", 1: "vp9", 2: "h264"}
        selected_codec = codec_map.get(self.combo_vid_codec.currentIndex(), "vp8")

        crf_map = {0: 26, 1: 15, 2: 31}
        selected_crf = crf_map.get(self.combo_vid_crf.currentIndex(), 26)

        cfg = Config(
            target_category=TargetCategory.ALL,
            video_codec=selected_codec,
            crf=selected_crf,
            max_general_workers=self.slider_img_threads.value(),
            max_video_workers=self.slider_vid_threads.value(),
        )

        custom_temp = self.edit_custom_temp.text().strip() if self.radio_temp_custom.isChecked() else None

        self.batch_worker = BatchOptimizationWorker(
            jobs=jobs,
            base_config=cfg,
            custom_temp_dir=custom_temp,
            apply_nwjs_clean=self.chk_nwjs_clean.isChecked(),
            overwrite_smaller=self.chk_overwrite_smaller.isChecked(),
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
