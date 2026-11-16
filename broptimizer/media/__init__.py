"""Módulo de optimizadores multimedia especializados."""

from broptimizer.media.audio import AudioOptimizer
from broptimizer.media.base import BaseMediaOptimizer, OptimizationResult
from broptimizer.media.image import ImageOptimizer
from broptimizer.media.video import VideoOptimizer

__all__ = [
    "BaseMediaOptimizer",
    "OptimizationResult",
    "ImageOptimizer",
    "AudioOptimizer",
    "VideoOptimizer",
]
