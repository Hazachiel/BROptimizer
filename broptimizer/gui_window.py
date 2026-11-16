"""Ventana principal PySide6 para BROptimizer."""

from pathlib import Path

from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from broptimizer.application import AnalysisResult, AnalysisService
from broptimizer.config import Config, Preset, TargetCategory
from broptimizer.gui_workers import AnalysisWorker, OptimizationWorker
from broptimizer.manager import OptimizationSummary
from broptimizer.postprocess import PostProcessor
from broptimizer.scanner import format_bytes

VERSION = "1.3.0"

# e903eb
STYLE = """
QMainWindow, QWidget { background: #222222; color: white; font-size: 13px; }
QFrame#sidebar { background: #1e1e1e; color: white; }
QLabel#brand { background: #1e1e1e; color: white; font-size: 24px; font-weight: 700; }
QLabel#subtitle { background: #1e1e1e; color: #9eabc0; }
QListWidget { background: transparent; border: 0; color: white; padding: 12px 8px; }
QListWidget::item { padding: 13px 14px; border-radius: 7px; }
QListWidget::item:selected { background: #454545; color: white; }
QLabel#pageTitle { font-size: 26px; font-weight: 700; color: #d7d7d7; }
QLabel#muted { color: #c1cbdb; }
QLabel#selectFolder { background: #4e4e4e; color: white; border-radius: 6px; padding: 6px; }
QFrame#card { background: transparent; border: 1px solid #dbe3ef; border-radius: 10px; }
QLabel#metricValue { font-size: 22px; font-weight: 700; color: white; }
QPushButton { background: #1fa6a8; color: white; border: 0; border-radius: 7px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #168d90; }
QPushButton:disabled { background: #a9b5c8; }
QPushButton#danger { background: #c64b54; }
QLineEdit, QComboBox, QTextEdit, QTableWidget { background: #4e4e4e; border: 1px solid #cbd6e5; border-radius: 6px; padding: 6px; }
QSpinBox { background: #4e4e4e; color: white; border: 1px solid #cbd6e5; border-radius: 6px;}
QHeaderView::section { background: #3e3e3e; padding: 8px; border: 0; font-weight: 600; }
QProgressBar { background: #e4ebf4; border: 0; border-radius: 5px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #1fa6a8; border-radius: 5px; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BROptimizer")
        self.resize(1240, 780)
        self.setMinimumSize(980, 640)
        self.setStyleSheet(STYLE)
        self.config = Config()
        self.analysis: AnalysisResult | None = None
        self.summary: OptimizationSummary | None = None
        self.full_optimization = False
        self._thread: QThread | None = None
        self._worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 26, 18, 18)
        brand = QLabel("BROptimizer", objectName="brand")
        side_layout.addWidget(brand)
        side_layout.addWidget(QLabel("Optimización multimedia", objectName="subtitle"))
        side_layout.addSpacing(28)
        self.navigation = QListWidget()
        self.navigation.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for label in ("Inicio", "Análisis", "Optimización", "Resultados", "Configuración"):
            self.navigation.addItem(QListWidgetItem(label))
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex if hasattr(self, "pages") else lambda _: None)
        side_layout.addWidget(self.navigation)
        side_layout.addStretch()
        side_layout.addWidget(QLabel(f"v{VERSION}", objectName="subtitle"))
        layout.addWidget(sidebar)

        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_analysis_page())
        self.pages.addWidget(self._build_optimization_page())
        self.pages.addWidget(self._build_results_page())
        self.pages.addWidget(self._build_settings_page())
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.setCentralWidget(root)

    def _page(self, title: str, description: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)
        layout.addWidget(QLabel(title, objectName="pageTitle"))
        layout.addWidget(QLabel(description, objectName="muted"))
        return page, layout

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        return card, layout

    def _build_home_page(self) -> QWidget:
        page, layout = self._page("Optimiza tus juegos", "Selecciona una carpeta para analizar sus recursos y detectar el motor automáticamente.")
        card, card_layout = self._card()
        card_layout.addWidget(QLabel("Carpeta a optimizar", objectName="muted"))
        row = QHBoxLayout()
        self.folder_label = QLabel("Ninguna carpeta seleccionada", objectName="selectFolder")
        self.folder_label.setWordWrap(True)
        row.addWidget(self.folder_label, 1)
        browse = QPushButton("Elegir carpeta")
        browse.clicked.connect(self.choose_folder)
        row.addWidget(browse)
        card_layout.addLayout(row)
        self.analyze_button = QPushButton("Analizar carpeta")
        self.analyze_button.clicked.connect(self.analyze_folder)
        self.analyze_button.setEnabled(False)
        card_layout.addWidget(self.analyze_button)
        layout.addWidget(card)

        metrics = QHBoxLayout()
        self.home_engine: QFrame = self._metric("Motor", "Pendiente")
        self.home_media: QFrame = self._metric("Multimedia", "0 archivos")
        self.home_size: QFrame = self._metric("Tamaño total", "0 B")
        self.home_nwjs: QFrame = self._metric("NW.js redundante", "No analizado")
        for card in (self.home_engine, self.home_media, self.home_size, self.home_nwjs):
            metrics.addWidget(card)
        layout.addLayout(metrics)
        layout.addStretch()
        return page

    def _metric(self, title: str, value: str) -> QFrame:
        card, layout = self._card()
        layout.addWidget(QLabel(title, objectName="muted"))
        label = QLabel(value, objectName="metricValue")
        label.setWordWrap(True)
        layout.addWidget(label)
        card.metric_value = label
        return card

    def _build_analysis_page(self) -> QWidget:
        page, layout = self._page("Análisis", "Revisa el contenido detectado antes de iniciar una operación.")
        self.analysis_summary = QLabel("Selecciona una carpeta en Inicio.", objectName="muted")
        self.analysis_summary.setWordWrap(True)
        layout.addWidget(self.analysis_summary)
        self.stats_table = QTableWidget(0, 4)
        self.stats_table.setHorizontalHeaderLabels(("Categoría", "Archivos", "Tamaño", "Marcados"))
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table, 1)
        actions = QHBoxLayout()
        self.clean_button = QPushButton("Limpiar NW.js")
        self.clean_button.clicked.connect(self.clean_nwjs)
        self.full_button = QPushButton("Optimización completa")
        self.full_button.clicked.connect(lambda: self.start_optimization(full=True))
        self.media_button = QPushButton("Optimizar multimedia")
        self.media_button.clicked.connect(lambda: self.start_optimization(full=False))
        actions.addWidget(self.clean_button)
        actions.addWidget(self.media_button)
        actions.addWidget(self.full_button)
        layout.addLayout(actions)
        return page

    def _build_optimization_page(self) -> QWidget:
        page, layout = self._page("Optimización", "Ajusta la calidad y sigue el progreso de la operación en tiempo real.")
        card = QFrame(objectName="card")
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setVerticalSpacing(12)
        
        # Configuración básica
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Lossy (recomendado)", Preset.LOSSY)
        
        self.target_combo = QComboBox()
        for label, value in (("Todo", TargetCategory.ALL), ("Imágenes", TargetCategory.IMAGES), 
                            ("Audio", TargetCategory.AUDIO), ("Vídeo", TargetCategory.VIDEO)):
            self.target_combo.addItem(label, value)
            
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(("VP8", "VP9", "H264"))
        
        # --- Configuración CRF ---
        self.crf_line_edit = QLineEdit("26")
        self.crf_line_edit.setFixedWidth(60) # Ancho fijo para que se alinee bien
        self.crf_line_edit.setValidator(QIntValidator(15, 31))  # Validar que el valor esté entre 15 y 31
        self.crf_slider = QSlider(Qt.Orientation.Horizontal)
        self.crf_slider.setRange(15, 31)
        self.crf_slider.setSingleStep(1)
        self.crf_slider.setValue(26)
        self.crf_slider.valueChanged.connect(lambda value: self.crf_line_edit.setText(str(value)))
        self.crf_line_edit.editingFinished.connect(lambda: self._on_crf_editing_finished())
        self.crf_line_edit.focusOutEvent = lambda event: (self._on_crf_editing_finished(), QLineEdit.focusOutEvent(self.crf_line_edit, event))
        
        # Crear contenedor horizontal para CRF
        crf_layout = QHBoxLayout()
        crf_layout.addWidget(self.crf_line_edit, alignment=Qt.AlignmentFlag.AlignRight)
        crf_layout.addWidget(self.crf_slider)
        crf_layout.setSpacing(10)
        
        # --- Configuración Resolución ---
        self.res_line_edit = QLineEdit("600")
        self.res_line_edit.setFixedWidth(60)
        self.res_line_edit.setValidator(QIntValidator(120, 4096))  # Validar que el valor esté entre 120 y 4096
        self.res_slider = QSlider(Qt.Orientation.Horizontal)
        self.res_slider.setRange(120, 4096)
        self.res_slider.setSingleStep(40)
        self.res_slider.setValue(600)
        self.res_slider.valueChanged.connect(lambda value: self.res_line_edit.setText(str(value)))
        self.res_line_edit.editingFinished.connect(lambda: self._on_res_editing_finished())
        self.res_line_edit.focusOutEvent = lambda event: (self._on_res_editing_finished(), QLineEdit.focusOutEvent(self.res_line_edit, event))

        # Crear contenedor horizontal para Resolución
        res_layout = QHBoxLayout()
        res_layout.addWidget(self.res_line_edit, alignment=Qt.AlignmentFlag.AlignRight)
        res_layout.addWidget(self.res_slider)
        res_layout.setSpacing(10)
        
        # --- Añadir filas al formulario ---
        form.addRow("Preset", self.preset_combo)
        form.addRow("Categoría", self.target_combo)
        form.addRow("Códec de vídeo", self.codec_combo)
        
        # Aquí agregamos el layout horizontal como una sola fila
        form.addRow("CRF", crf_layout)
        form.addRow("Resolución deseada", res_layout)
        
        self.extension_check = self._check("Preservar extensión original", True)
        self.metadata_check = self._check("Marcar metadata BROptimized", True)
        
        form.addRow("Opciones", self.extension_check)
        form.addRow("", self.metadata_check)
        
        layout.addWidget(card)
        
        self.progress_label = QLabel("Listo para optimizar", objectName="muted")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        
        self.start_button = QPushButton("Iniciar optimización")
        self.start_button.clicked.connect(self.start_optimization)
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        
        return page

    def _on_res_editing_finished(self):
        value = int(self.res_line_edit.text())
        if self.res_slider.minimum() <= value <= self.res_slider.maximum():
            self.res_slider.setValue(value)
        else:
            self.res_line_edit.setText(str(self.res_slider.value()))

    def _on_crf_editing_finished(self):
        value = int(self.crf_line_edit.text())
        if self.crf_slider.minimum() <= value <= self.crf_slider.maximum():
            self.crf_slider.setValue(value)
        else:
            self.crf_line_edit.setText(str(self.crf_slider.value()))

    def _check(self, text: str, checked: bool):
        from PySide6.QtWidgets import QCheckBox
        control = QCheckBox(text)
        control.setChecked(checked)
        return control

    def _build_results_page(self) -> QWidget:
        page, layout = self._page("Resultados", "Aplica los archivos optimizados o exporta una copia independiente del juego.")
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text, 1)
        actions = QHBoxLayout()
        self.in_place_button = QPushButton("Aplicar in-place")
        self.in_place_button.clicked.connect(self.apply_in_place)
        self.export_button = QPushButton("Exportar copia")
        self.export_button.clicked.connect(self.export_copy)
        actions.addWidget(self.in_place_button)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        return page

    def _build_settings_page(self) -> QWidget:
        page, layout = self._page("Configuración", "Los valores se aplican a la siguiente operación de optimización.")
        card = QFrame(objectName="card")
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setVerticalSpacing(12)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 64)
        self.threads_spin.setValue(self.config.max_general_workers)
        self.video_workers_spin = QSpinBox()
        self.video_workers_spin.setRange(1, 2)
        self.video_workers_spin.setValue(self.config.max_video_workers)
        form.addRow("Hilos generales", self.threads_spin)
        form.addRow("Conversiones de vídeo simultáneas", self.video_workers_spin)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta del juego")
        if folder:
            self.folder_label.setText(folder)
            self.analyze_button.setEnabled(True)
            self._selected_folder = Path(folder)

    def analyze_folder(self) -> None:
        if not getattr(self, "_selected_folder", None):
            return
        self._set_busy(True)
        self.progress_label.setText("Analizando carpeta...")
        self._run_worker(AnalysisWorker(self._selected_folder), self._analysis_finished)

    def _run_worker(self, worker, finished_handler) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(finished_handler)
        worker.failed.connect(self._worker_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _analysis_finished(self, result: AnalysisResult) -> None:
        self.analysis = result
        self._set_busy(False)
        self._update_analysis(result)
        self.navigation.setCurrentRow(1)
        self.progress_label.setText("Análisis completado")

    def _update_analysis(self, result: AnalysisResult) -> None:
        self.home_engine.metric_value.setText(result.profile.display_name)
        self.home_media.metric_value.setText(f"{result.stats.total_media_count} archivos")
        self.home_size.metric_value.setText(result.stats.formatted_total_size)
        self.home_nwjs.metric_value.setText(f"{result.nwjs['count']} / {format_bytes(result.nwjs['size'])}")
        self.analysis_summary.setText(
            f"{result.root}\nMotor: {result.profile.display_name}\n"
            f"NW.js redundante: {result.nwjs['count']} archivos ({format_bytes(result.nwjs['size'])})"
        )
        rows = (("Imágenes", result.stats.images), ("Audio", result.stats.audios), ("Vídeo", result.stats.videos), ("Otros", result.stats.others))
        self.stats_table.setRowCount(len(rows))
        for row, (name, stats) in enumerate(rows):
            values = (name, str(stats.file_count), stats.formatted_size, str(stats.tagged_count))
            for column, value in enumerate(values):
                self.stats_table.setItem(row, column, QTableWidgetItem(value))
        is_rpgmaker = result.profile.name == "rpgmaker_modern"
        self.clean_button.setEnabled(is_rpgmaker and bool(result.nwjs["count"]))
        self.full_button.setEnabled(result.stats.total_media_count > 0)
        self.media_button.setEnabled(result.stats.total_media_count > 0)

    def _config_from_controls(self) -> Config:
        return Config(
            preset=self.preset_combo.currentData(),
            target_category=self.target_combo.currentData(),
            video_codec=self.codec_combo.currentText().lower(),
            crf=self.crf_spin.value(),
            desired_res=self.res_spin.value(),
            preserve_extension=self.extension_check.isChecked(),
            tag_metadata=self.metadata_check.isChecked(),
            max_general_workers=self.threads_spin.value(),
            max_video_workers=self.video_workers_spin.value(),
        )

    def start_optimization(self, full: bool = False) -> None:
        if not self.analysis:
            self.navigation.setCurrentRow(0)
            return
        config = self._config_from_controls()
        self.config = config
        self.full_optimization = full
        self._set_busy(True)
        self.navigation.setCurrentRow(2)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando...")
        self._run_worker(OptimizationWorker(self.analysis, config), self._optimization_finished)

    def _optimization_finished(self, summary: OptimizationSummary) -> None:
        self.summary = summary
        self._set_busy(False)
        self.progress_bar.setValue(100)
        self.results_text.setPlainText(
            f"Original: {summary.formatted_original_size}\n"
            f"Optimizado: {summary.formatted_optimized_size}\n"
            f"Ahorro: {summary.formatted_saved_size} ({summary.total_saved_percent:.2f}%)\n"
            f"Reducidos: {summary.optimized_count}\n"
            f"Sin cambios: {summary.kept_original_count}\n"
            f"Omitidos: {summary.skipped_count}\n"
            f"Errores: {summary.failed_count}"
        )
        self.navigation.setCurrentRow(3)

    def clean_nwjs(self) -> None:
        if not self.analysis:
            return
        answer = QMessageBox.question(self, "Confirmar limpieza", "Se eliminarán únicamente componentes redundantes de NW.js y se actualizará package.json.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = AnalysisService.clean_rpgmaker(self.analysis.root)
        self.progress_label.setText(f"Limpieza: {result.removed_count} elementos, {format_bytes(result.removed_size)} liberados")
        self.analyze_folder()

    def apply_in_place(self) -> None:
        if not self.summary or not self.analysis:
            return
        count = PostProcessor.apply_in_place(self.summary, self.analysis.root)
        self.results_text.append(f"\nAplicados in-place: {count} archivos.")
        if self.full_optimization and self.analysis.profile.name == "rpgmaker_modern":
            launcher = Path(__file__).resolve().parent.parent / "nwjs_game_launch.bat"
            cleanup = AnalysisService.clean_rpgmaker(self.analysis.root, copy_launcher=True, launcher_source=launcher)
            self.results_text.append(f"Limpieza NW.js: {cleanup.removed_count} elementos; lanzador copiado: {cleanup.launcher_copied}.")
        self.summary = None

    def export_copy(self) -> None:
        if not self.summary or not self.analysis:
            return
        destination = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino")
        if not destination:
            return
        destination_path = Path(destination)
        placed, copied = PostProcessor.export_standalone(
            self.summary,
            self.analysis.stats,
            destination_path,
            clean_nwjs=self.full_optimization,
        )
        self.results_text.append(f"\nExportados: {placed} optimizados, {copied} archivos copiados.")
        if self.full_optimization and self.analysis.profile.name == "rpgmaker_modern":
            launcher = Path(__file__).resolve().parent.parent / "nwjs_game_launch.bat"
            cleanup = AnalysisService.clean_rpgmaker(destination_path, copy_launcher=True, launcher_source=launcher)
            self.results_text.append(f"Limpieza NW.js: {cleanup.removed_count} elementos; lanzador copiado: {cleanup.launcher_copied}.")
        self.summary = None

    def _worker_failed(self, message: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, "Operación fallida", message)

    def _set_busy(self, busy: bool) -> None:
        self.analyze_button.setEnabled(not busy and bool(getattr(self, "_selected_folder", None)))
        self.start_button.setEnabled(not busy and self.analysis is not None)
        can_clean = bool(self.analysis and self.analysis.profile.name == "rpgmaker_modern" and self.analysis.nwjs["count"])
        self.clean_button.setEnabled(not busy and can_clean)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
