"""Servicios de aplicación compartidos por la CLI y la interfaz gráfica."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from broptimizer.config import Config
from broptimizer.engines.detector import EngineDetector
from broptimizer.engines.base import EngineProfile
from broptimizer.manager import OptimizationManager, OptimizationSummary
from broptimizer.rpgmaker_cleaner import RPGMMVCleaner
from broptimizer.scanner import FolderScanner, MediaStats


@dataclass
class AnalysisResult:
    root: Path
    profile: EngineProfile
    stats: MediaStats
    nwjs: dict


@dataclass
class CleanupResult:
    removed_count: int
    removed_size: int
    package_updated: bool
    launcher_copied: bool


class AnalysisService:
    """Coordina detección, escaneo y operaciones específicas de RPG Maker."""

    @staticmethod
    def analyze(folder: str | Path) -> AnalysisResult:
        root = Path(folder).expanduser().resolve()
        profile = EngineDetector.detect(root)
        stats = FolderScanner.scan(root, check_tags=True, detect_nwjs=profile.name == "rpgmaker_modern")
        nwjs = {
            "files": stats.nwjs_files,
            "count": stats.nwjs_count,
            "size": stats.nwjs_size,
        }
        return AnalysisResult(root=root, profile=profile, stats=stats, nwjs=nwjs)

    @staticmethod
    def optimize(
        analysis: AnalysisResult,
        config: Config,
        progress_callback: Callable | None = None,
    ) -> OptimizationSummary:
        files = [file_info for file_info in analysis.stats.files if file_info.media_type.value != "other"]
        manager = OptimizationManager(config, analysis.profile)
        return manager.process_files(files, progress_callback=progress_callback)

    @staticmethod
    def clean_rpgmaker(
        root: str | Path,
        copy_launcher: bool = False,
        launcher_source: Path | None = None,
    ) -> CleanupResult:
        destination = Path(root).expanduser().resolve()
        removed_count, removed_size = RPGMMVCleaner.clean_nwjs(destination)
        package_updated = RPGMMVCleaner.patch_package_json(destination)
        launcher_copied = False
        if copy_launcher and launcher_source:
            launcher_copied = RPGMMVCleaner.copy_launcher(destination, launcher_source)
        return CleanupResult(removed_count, removed_size, package_updated, launcher_copied)
