"""Clase base y estructuras de resultado para optimizadores de medios."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from broptimizer.config import Config
from broptimizer.engines.base import EngineProfile


@dataclass
class OptimizationResult:
    """Resultado del proceso de optimización de un archivo."""
    input_path: Path
    temp_output_path: Path | None
    original_size: int
    optimized_size: int
    success: bool
    target_extension: str
    skipped: bool = False
    is_smaller: bool = False
    error_message: str | None = None

    @property
    def saved_bytes(self) -> int:
        if self.success and self.is_smaller:
            return max(0, self.original_size - self.optimized_size)
        return 0

    @property
    def saved_percent(self) -> float:
        if self.original_size > 0 and self.success and self.is_smaller:
            return ((self.original_size - self.optimized_size) / self.original_size) * 100.0
        return 0.0


class BaseMediaOptimizer(ABC):
    """Clase base abstracta para optimizadores de medios individuales."""

    @abstractmethod
    def optimize(
        self,
        input_path: Path,
        temp_dir: Path,
        config: Config,
        profile: EngineProfile,
    ) -> OptimizationResult:
        """Optimiza un archivo multimedia y devuelve el resultado."""
        raise NotImplementedError
