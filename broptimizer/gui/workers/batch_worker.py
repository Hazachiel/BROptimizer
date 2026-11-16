"""Worker secuencial para ejecutar las optimizaciones por lote."""

import os
from pathlib import Path
import shutil
from typing import Any
from PySide6.QtCore import QThread, Signal

from broptimizer import PROJECT_ROOT
from broptimizer.config import Config, TargetCategory
from broptimizer.engines.detector import EngineDetector
from broptimizer.engines.generic import GenericProfile
from broptimizer.engines.rpgmaker import RpgMakerMzProfile
from broptimizer.logger import ActivityLogger
from broptimizer.manager import OptimizationManager
from broptimizer.postprocess import PostProcessor
from broptimizer.rpgmaker_cleaner import RPGMMVCleaner
from broptimizer.scanner import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    FileInfo,
    FolderScanner,
    MediaType,
)


class BatchOptimizationWorker(QThread):
    """Procesa secuencialmente cada trabajo de la cola en segundo plano."""

    item_started = Signal(int, str)             # row_index, item_name
    item_status_update = Signal(int, str)       # row_index, status_text
    item_progress = Signal(int, int)            # row_index, percent
    item_finished = Signal(int, int, float)     # row_index, final_size, savings_percent
    item_error = Signal(int, str)               # row_index, error_msg
    batch_finished = Signal()

    def __init__(
        self,
        jobs: list[dict[str, Any]],
        base_config: Config,
        custom_temp_dir: str | None,
        apply_nwjs_clean: bool,
        overwrite_smaller: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.jobs = jobs
        self.base_config = base_config
        self.custom_temp_dir = custom_temp_dir
        self.apply_nwjs_clean = apply_nwjs_clean
        self.overwrite_smaller = overwrite_smaller
        self._is_paused = False
        self._is_cancelled = False

    def pause(self) -> None:
        self._is_paused = True

    def resume(self) -> None:
        self._is_paused = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def _determine_media_type(self, ext: str) -> MediaType:
        ext = ext.lower()
        if ext in IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        if ext in AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        if ext in VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        return MediaType.OTHER

    def run(self) -> None:
        for job in self.jobs:
            if self._is_cancelled:
                break

            while self._is_paused and not self._is_cancelled:
                self.msleep(200)

            if self._is_cancelled:
                break

            row = job["row"]
            path = Path(job["path"]).resolve()
            orig_size = job.get("orig_size", 0)

            self.item_started.emit(row, path.name)
            self.item_status_update.emit(row, "Escaneando archivos...")
            ActivityLogger.log_message(f"\n{'=' * 60}\n[LOTE INICIADO]: {path.name}\n{'=' * 60}")

            try:
                if path.is_dir():
                    # 1. Detectar perfil de motor directamente
                    profile = EngineDetector.detect(path) or GenericProfile()
                    is_modern_rpg = isinstance(profile, RpgMakerMzProfile) or getattr(profile, "name", "") == "rpgmaker_modern"
                    should_clean_nwjs = self.apply_nwjs_clean and is_modern_rpg

                    # 2. Escanear archivos multimedia
                    stats = FolderScanner.scan(
                        path,
                        check_tags=self.base_config.tag_metadata,
                        detect_nwjs=is_modern_rpg,
                    )
                    processable_files = [
                        f for f in stats.files
                        if f.media_type in (MediaType.IMAGE, MediaType.AUDIO, MediaType.VIDEO)
                    ]

                    # Si no hay multimedia pero se pidió limpieza NW.js en RPG Maker MV/MZ
                    if not processable_files:
                        if should_clean_nwjs:
                            self.item_status_update.emit(row, "Limpiando NW.js...")
                            rem_count, rem_bytes = RPGMMVCleaner.clean_nwjs(path)
                            RPGMMVCleaner.patch_package_json(path)
                            bat_source = PROJECT_ROOT / "nwjs_game_launch.bat"
                            if bat_source.is_file():
                                RPGMMVCleaner.copy_launcher(path, bat_source)
                            ActivityLogger.log_message(
                                f"[NW.js Limpieza] {rem_count} componentes redundantes eliminados "
                                f"({ActivityLogger.format_size(rem_bytes)}) : ELIMINADO"
                            )

                        final_size = sum(
                            os.path.getsize(os.path.join(root, f))
                            for root, _, files in os.walk(path)
                            for f in files
                        )
                        savings = 0.0
                        if orig_size > 0:
                            savings = max(0.0, ((orig_size - final_size) / orig_size) * 100.0)
                        self.item_status_update.emit(row, "Limpieza NW.js completada")
                        self.item_finished.emit(row, final_size, savings)
                        continue

                    # 3. Optimizar multimedia
                    manager = OptimizationManager(self.base_config, profile)
                    total_files = len(processable_files)
                    completed_files = 0

                    def on_progress(
                        stage_label: str,
                        stage_completed: int,
                        stage_total: int,
                        file_info: FileInfo | None = None,
                        res: Any = None,
                        *args,
                    ) -> None:
                        nonlocal completed_files
                        completed_files += 1

                        if total_files > 0:
                            pct = int((completed_files / total_files) * 100)
                            self.item_progress.emit(row, pct)

                        self.item_status_update.emit(
                            row, f"[{stage_label}] {stage_completed}/{stage_total}"
                        )

                        # Registrar en ActivityLogger de forma thread-safe
                        if file_info and res:
                            fname = file_info.path.name
                            orig_b = getattr(res, "original_size", file_info.size)
                            opt_b = getattr(res, "optimized_size", file_info.size)

                            if not getattr(res, "success", True):
                                status_str = "ERROR!"
                                extra = getattr(res, "error_message", "") or "Fallo en conversión"
                            elif getattr(res, "skipped", False):
                                status_str = "SALTADO"
                                extra = "Ya optimizado (BROptimized)"
                            elif getattr(res, "is_smaller", False):
                                status_str = "GUARDADO"
                                extra = ""
                            else:
                                status_str = "DESCARTADO"
                                extra = "Sin reducción de peso"

                            ActivityLogger.log_item(fname, orig_b, opt_b, status_str, extra)

                    summary = manager.process_files(processable_files, progress_callback=on_progress)

                    # 4. Post-procesamiento
                    if self.overwrite_smaller:
                        self.item_status_update.emit(row, "Aplicando cambios...")
                        PostProcessor.apply_in_place(summary, path)
                        dest_folder = path
                        for res in summary.results:
                            if getattr(res, "success", False) and getattr(res, "is_smaller", False):
                                ActivityLogger.log_item(
                                    res.input_path.name,
                                    res.original_size,
                                    res.optimized_size,
                                    "SOBREESCRITO",
                                )

                        if should_clean_nwjs:
                            self.item_status_update.emit(row, "Limpiando NW.js...")
                            rem_count, rem_bytes = RPGMMVCleaner.clean_nwjs(dest_folder)
                            RPGMMVCleaner.patch_package_json(dest_folder)
                            bat_source = PROJECT_ROOT / "nwjs_game_launch.bat"
                            if bat_source.is_file():
                                RPGMMVCleaner.copy_launcher(dest_folder, bat_source)
                            ActivityLogger.log_message(
                                f"[NW.js Limpieza] {rem_count} componentes redundantes eliminados "
                                f"({ActivityLogger.format_size(rem_bytes)}) : ELIMINADO"
                            )
                    else:
                        dest_folder = (
                            Path(self.custom_temp_dir)
                            if self.custom_temp_dir
                            else path.parent / f"{path.name}_optimized"
                        )
                        self.item_status_update.emit(row, f"Exportando a {dest_folder.name}...")
                        PostProcessor.export_standalone(
                            summary, stats, dest_folder, clean_nwjs=should_clean_nwjs
                        )
                        if should_clean_nwjs:
                            self.item_status_update.emit(row, "Parcheando NW.js...")
                            RPGMMVCleaner.patch_package_json(dest_folder)
                            bat_source = PROJECT_ROOT / "nwjs_game_launch.bat"
                            if bat_source.is_file():
                                RPGMMVCleaner.copy_launcher(dest_folder, bat_source)
                            ActivityLogger.log_message(
                                f"[NW.js Limpieza] Launcher y package.json configurados en {dest_folder.name}"
                            )

                    # 5. Calcular tamaño final
                    final_size = sum(
                        os.path.getsize(os.path.join(root, f))
                        for root, _, files in os.walk(dest_folder)
                        for f in files
                    )

                else:
                    # Caso: Archivo individual
                    profile = GenericProfile()
                    mtype = self._determine_media_type(path.suffix)
                    if mtype in (MediaType.IMAGE, MediaType.AUDIO, MediaType.VIDEO):
                        file_info = FileInfo(
                            path=path,
                            rel_path=Path(path.name),
                            size=path.stat().st_size,
                            media_type=mtype,
                            extension=path.suffix.lower(),
                        )
                        manager = OptimizationManager(self.base_config, profile)

                        def on_file_progress(
                            stage_label: str,
                            stage_completed: int,
                            stage_total: int,
                            file_info: FileInfo | None = None,
                            res: Any = None,
                            *args,
                        ) -> None:
                            self.item_progress.emit(row, 100)
                            self.item_status_update.emit(row, f"[{stage_label}] Completado")
                            if file_info and res:
                                fname = file_info.path.name
                                orig_b = getattr(res, "original_size", file_info.size)
                                opt_b = getattr(res, "optimized_size", file_info.size)
                                if not getattr(res, "success", True):
                                    status_str = "ERROR!"
                                    extra = getattr(res, "error_message", "") or "Fallo en conversión"
                                elif getattr(res, "skipped", False):
                                    status_str = "SALTADO"
                                    extra = "Ya optimizado"
                                elif getattr(res, "is_smaller", False):
                                    status_str = "GUARDADO"
                                    extra = ""
                                else:
                                    status_str = "DESCARTADO"
                                    extra = "No redujo tamaño"
                                ActivityLogger.log_item(fname, orig_b, opt_b, status_str, extra)

                        summary = manager.process_files([file_info], progress_callback=on_file_progress)

                        if self.overwrite_smaller:
                            self.item_status_update.emit(row, "Aplicando cambios...")
                            PostProcessor.apply_in_place(summary, path.parent)
                            final_size = path.stat().st_size if path.exists() else orig_size
                            res = summary.results[0] if summary.results else None
                            if res and getattr(res, "success", False) and getattr(res, "is_smaller", False):
                                ActivityLogger.log_item(
                                    res.input_path.name,
                                    res.original_size,
                                    res.optimized_size,
                                    "SOBREESCRITO",
                                )
                        else:
                            dest_folder = (
                                Path(self.custom_temp_dir)
                                if self.custom_temp_dir
                                else path.parent / f"{path.stem}_optimized"
                            )
                            dest_folder.mkdir(parents=True, exist_ok=True)
                            res = summary.results[0] if summary.results else None
                            if res and res.success and res.is_smaller and res.temp_output_path:
                                dest_file = dest_folder / f"{path.stem}{res.target_extension}"
                                shutil.copy2(str(res.temp_output_path), str(dest_file))
                                final_size = dest_file.stat().st_size
                            else:
                                dest_file = dest_folder / path.name
                                shutil.copy2(str(path), str(dest_file))
                                final_size = dest_file.stat().st_size
                            summary.cleanup()
                    else:
                        final_size = path.stat().st_size

                savings = 0.0
                if orig_size > 0:
                    savings = max(0.0, ((orig_size - final_size) / orig_size) * 100.0)

                self.item_finished.emit(row, final_size, savings)
                self.item_status_update.emit(row, "✔ Completado")

            except Exception as exc:
                self.item_error.emit(row, str(exc))
                self.item_status_update.emit(row, "❌ Error")

        self.batch_finished.emit()
