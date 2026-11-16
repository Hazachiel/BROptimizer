"""Orquestador de optimización con procesamiento secuencial por etapas (Imágenes -> Audios -> Videos)."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
import shutil
import tempfile
import threading

from broptimizer.config import Config, TargetCategory
from broptimizer.engines.base import EngineProfile
from broptimizer.logger import ErrorLogger
from broptimizer.media.audio import AudioOptimizer
from broptimizer.media.base import OptimizationResult
from broptimizer.media.image import ImageOptimizer
from broptimizer.media.video import VideoOptimizer
from broptimizer.scanner import FileInfo, MediaType, format_bytes


@dataclass
class OptimizationSummary:
    """Resumen integral de los resultados tras procesar una carpeta."""
    results: list[OptimizationResult] = field(default_factory=list)
    temp_dir: Path | None = None
    total_original_bytes: int = 0
    total_optimized_bytes: int = 0
    optimized_count: int = 0
    kept_original_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0

    @property
    def total_files_processed(self) -> int:
        return len(self.results)

    @property
    def total_saved_bytes(self) -> int:
        return max(0, self.total_original_bytes - self.total_optimized_bytes)

    @property
    def total_saved_percent(self) -> float:
        if self.total_original_bytes > 0:
            return (self.total_saved_bytes / self.total_original_bytes) * 100.0
        return 0.0

    @property
    def formatted_original_size(self) -> str:
        return format_bytes(self.total_original_bytes)

    @property
    def formatted_optimized_size(self) -> str:
        return format_bytes(self.total_optimized_bytes)

    @property
    def formatted_saved_size(self) -> str:
        return format_bytes(self.total_saved_bytes)

    def cleanup(self) -> None:
        """Elimina el directorio temporal aislado y todos los archivos intermedios."""
        if self.temp_dir and self.temp_dir.is_dir():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None


class OptimizationManager:
    """Gestiona el procesamiento por etapas secuenciales con semáforo de video."""

    def __init__(self, config: Config, profile: EngineProfile) -> None:
        self.config = config
        self.profile = profile
        self.image_optimizer = ImageOptimizer()
        self.audio_optimizer = AudioOptimizer()
        self.video_optimizer = VideoOptimizer()
        
        # Semáforo estricto para limitar conversiones de video simultáneas (1 o 2)
        self.video_semaphore = threading.Semaphore(self.config.max_video_workers)

    def _process_single_file(self, file_info: FileInfo, temp_dir: Path) -> OptimizationResult:
        """Procesa un archivo individual según su categoría."""
        if file_info.is_tagged:
            return OptimizationResult(
                input_path=file_info.path,
                temp_output_path=None,
                original_size=file_info.size,
                optimized_size=file_info.size,
                success=True,
                skipped=True,
                is_smaller=False,
                target_extension=file_info.extension,
            )

        if file_info.media_type == MediaType.IMAGE:
            return self.image_optimizer.optimize(file_info.path, temp_dir, self.config, self.profile)

        elif file_info.media_type == MediaType.AUDIO:
            return self.audio_optimizer.optimize(file_info.path, temp_dir, self.config, self.profile)

        elif file_info.media_type == MediaType.VIDEO:
            with self.video_semaphore:
                return self.video_optimizer.optimize(file_info.path, temp_dir, self.config, self.profile)

        return OptimizationResult(
            input_path=file_info.path,
            temp_output_path=None,
            original_size=file_info.size,
            optimized_size=file_info.size,
            success=True,
            skipped=True,
            is_smaller=False,
            target_extension=file_info.extension,
        )

    def process_files(
        self,
        files_to_process: list[FileInfo],
        progress_callback: Callable[[str, int, int, FileInfo, OptimizationResult], None] | None = None,
    ) -> OptimizationSummary:
        """
        Ejecuta la optimización en tres etapas estrictamente secuenciales:
        1. Imágenes
        2. Audios
        3. Videos
        Filtrando según config.target_category.
        """
        temp_dir_path = Path(tempfile.mkdtemp(prefix="bropt_staging_"))
        summary = OptimizationSummary(temp_dir=temp_dir_path)

        images = [f for f in files_to_process if f.media_type == MediaType.IMAGE]
        audios = [f for f in files_to_process if f.media_type == MediaType.AUDIO]
        videos = [f for f in files_to_process if f.media_type == MediaType.VIDEO]

        stages: list[tuple[str, list[FileInfo]]] = []

        target = self.config.target_category
        if target in (TargetCategory.ALL, TargetCategory.IMAGES) and images:
            stages.append(("Imágenes", images))
        if target in (TargetCategory.ALL, TargetCategory.AUDIO) and audios:
            stages.append(("Audios", audios))
        if target in (TargetCategory.ALL, TargetCategory.VIDEO) and videos:
            stages.append(("Videos", videos))

        for stage_idx, (stage_name, stage_files) in enumerate(stages, start=1):
            stage_total = len(stage_files)
            stage_completed = 0
            stage_label = f"Etapa {stage_idx}/{len(stages)}: {stage_name}"

            with ThreadPoolExecutor(max_workers=self.config.max_general_workers) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, file_info, temp_dir_path): file_info
                    for file_info in stage_files
                }

                for future in as_completed(future_to_file):
                    file_info = future_to_file[future]
                    stage_completed += 1
                    try:
                        res: OptimizationResult = future.result()
                    except Exception as ex:
                        ErrorLogger.log_error(
                            code_block="OptimizationManager.process_files",
                            file_path=file_info.path,
                            exception=ex,
                        )
                        res = OptimizationResult(
                            input_path=file_info.path,
                            temp_output_path=None,
                            original_size=file_info.size,
                            optimized_size=file_info.size,
                            success=False,
                            target_extension=file_info.extension,
                            error_message=str(ex),
                        )

                    summary.results.append(res)
                    summary.total_original_bytes += res.original_size

                    if res.skipped:
                        summary.skipped_count += 1
                        summary.total_optimized_bytes += res.original_size
                    elif not res.success:
                        summary.failed_count += 1
                        summary.total_optimized_bytes += res.original_size
                    elif res.is_smaller and res.temp_output_path:
                        summary.optimized_count += 1
                        summary.total_optimized_bytes += res.optimized_size
                    else:
                        summary.kept_original_count += 1
                        summary.total_optimized_bytes += res.original_size

                    if progress_callback:
                        progress_callback(stage_label, stage_completed, stage_total, file_info, res)

        return summary
