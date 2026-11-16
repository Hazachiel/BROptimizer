"""Pruebas para el detector de motores de videojuegos."""

import tempfile
from pathlib import Path
import unittest

from broptimizer.engines.detector import EngineDetector
from broptimizer.engines.generic import GenericProfile
from broptimizer.engines.renpy import RenpyProfile
from broptimizer.engines.rpgmaker import RpgMakerLegacyProfile, RpgMakerMzProfile
from broptimizer.engines.wolfrpg import WolfRpgProfile


class TestEngineDetector(unittest.TestCase):

    def test_detect_generic_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = EngineDetector.detect(tmp)
            self.assertIsInstance(profile, GenericProfile)
            self.assertTrue(profile.supports_webp)

    def test_detect_renpy_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            game_dir = p / "game"
            game_dir.mkdir()
            (game_dir / "options.rpy").touch()
            (game_dir / "script.rpyc").touch()

            profile = EngineDetector.detect(p)
            self.assertIsInstance(profile, RenpyProfile)
            self.assertTrue(profile.supports_webp)
            self.assertTrue(profile.supports_opus)

    def test_detect_rpgmaker_mz(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            js_dir = p / "js"
            js_dir.mkdir()
            (js_dir / "rmmz_core.js").touch()

            profile = EngineDetector.detect(p)
            self.assertIsInstance(profile, RpgMakerMzProfile)
            self.assertTrue(profile.supports_webp)

    def test_detect_rpgmaker_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "Game.rxproj").touch()

            profile = EngineDetector.detect(p)
            self.assertIsInstance(profile, RpgMakerLegacyProfile)
            # Motores legados NO soportan WebP
            self.assertFalse(profile.supports_webp)

    def test_detect_wolfrpg(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            data_dir = p / "Data" / "BasicData"
            data_dir.mkdir(parents=True)
            (data_dir / "SysDatabase.project").touch()

            profile = EngineDetector.detect(p)
            self.assertIsInstance(profile, WolfRpgProfile)
            self.assertFalse(profile.supports_webp)


if __name__ == "__main__":
    unittest.main()
