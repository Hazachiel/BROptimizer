"""Workers Qt para mantener la interfaz responsiva durante operaciones pesadas."""

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from broptimizer.application import AnalysisResult, AnalysisService
from broptimizer.config import Config


class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, folder: str | Path) -> None:
        super().__init__()
        self.folder = folder

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(AnalysisService.analyze(self.folder))
        except Exception as exc:
            self.failed.emit(str(exc))


class OptimizationWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, analysis: AnalysisResult, config: Config) -> None:
        super().__init__()
        self.analysis = analysis
        self.config = config

    @Slot()
    def run(self) -> None:
        try:
            total = max(1, self.analysis.stats.total_media_count)
            completed = 0
            
            def on_progress(stage: str, _stage_completed: int, _stage_total: int, file_info, _result) -> None:
                nonlocal completed
                completed += 1
                self.progress.emit(min(100, int(completed * 100 / total)), f"{stage}: {file_info.path.name}")

            summary = AnalysisService.optimize(self.analysis, self.config, on_progress)
            self.finished.emit(summary)
        except Exception as exc:
            self.failed.emit(str(exc))
