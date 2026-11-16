"""Worker para análisis secuencial no bloqueante de carpetas y archivos agregados a la tabla."""

import os
from pathlib import Path
from queue import Queue
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool

from broptimizer.engines.detector import EngineDetector


class DetectorSignals(QObject):
    """Señales emitidas durante el análisis secuencial de elementos."""
    item_analysis_started = Signal(str)  # item_id o path
    item_analysis_finished = Signal(str, str, int)  # item_id, engine_name, total_size_bytes
    all_analysis_finished = Signal()


class DetectorTask(QRunnable):
    """Tarea secuencial que procesa elementos uno a uno para evitar saturación de I/O."""

    def __init__(self, task_queue: Queue, signals: DetectorSignals) -> None:
        super().__init__()
        self.task_queue = task_queue
        self.signals = signals

    def run(self) -> None:
        while not self.task_queue.empty():
            item_id, file_path_str = self.task_queue.get()
            self.signals.item_analysis_started.emit(item_id)

            path = Path(file_path_str)
            engine_name = "Desconocido"
            total_size = 0

            try:
                if path.is_file():
                    total_size = path.stat().st_size
                    engine_name = f"Archivo ({path.suffix.lower()})"
                elif path.is_dir():
                    # 1. Detectar motor
                    engine = EngineDetector.detect(path)
                    engine_name = engine.name if engine else "Multimedia Genérico"

                    # 2. Calcular peso total inicial de forma secuencial y segura
                    for root, _, files in os.walk(path):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                total_size += os.path.getsize(fp)
                            except OSError:
                                pass
            except Exception:
                engine_name = "Error al escanear"

            self.signals.item_analysis_finished.emit(item_id, engine_name, total_size)
            self.task_queue.task_done()

        self.signals.all_analysis_finished.emit()


class SequentialDetectorQueue(QObject):
    """Gestor de cola para encolar ítems y procesarlos uno tras otro en segundo plano."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.signals = DetectorSignals()
        self._queue: Queue = Queue()
        self._is_running = False
        self._pool = QThreadPool.globalInstance()

    def add_item(self, item_id: str, path_str: str) -> None:
        """Añade un ítem a la cola de análisis secuencial."""
        self._queue.put((item_id, path_str))
        self._check_start()

    def _check_start(self) -> None:
        if not self._is_running and not self._queue.empty():
            self._is_running = True
            task = DetectorTask(self._queue, self.signals)
            self.signals.all_analysis_finished.connect(self._on_finished)
            self._pool.start(task)

    def _on_finished(self) -> None:
        self._is_running = False
        try:
            self.signals.all_analysis_finished.disconnect(self._on_finished)
        except Exception:
            pass
        if not self._queue.empty():
            self._check_start()

