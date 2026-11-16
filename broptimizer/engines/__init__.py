"""Módulo de perfiles y detección de motores de videojuegos."""

from broptimizer.engines.base import EngineProfile
from broptimizer.engines.detector import EngineDetector
from broptimizer.engines.generic import GenericProfile
from broptimizer.engines.renpy import RenpyProfile
from broptimizer.engines.rpgmaker import RpgMakerLegacyProfile, RpgMakerMzProfile
from broptimizer.engines.wolfrpg import WolfRpgProfile

__all__ = [
    "EngineProfile",
    "EngineDetector",
    "GenericProfile",
    "RenpyProfile",
    "RpgMakerMzProfile",
    "RpgMakerLegacyProfile",
    "WolfRpgProfile",
]
