"""Pruebas para ciclos de configuración y lógica de memoria de última ruta."""

from pathlib import Path
import unittest

from broptimizer.cli import BROptimizerCLI
from broptimizer.config import Config


class TestNavigationAndCycles(unittest.TestCase):

    def test_cycle_video_codec(self):
        config = Config(video_codec="vp8")
        self.assertEqual(config.video_codec, "vp8")

        self.assertEqual(config.cycle_video_codec(), "vp9")
        self.assertEqual(config.cycle_video_codec(), "h264")
        self.assertEqual(config.cycle_video_codec(), "vp8")

    def test_cycle_crf(self):
        config = Config(crf=26)
        self.assertEqual(config.crf, 26)

        self.assertEqual(config.cycle_crf(), 15)
        self.assertEqual(config.cycle_crf(), 26)
        self.assertEqual(config.cycle_crf(), 31)

    def test_cli_last_folder_memory(self):
        cli = BROptimizerCLI()
        self.assertIsNone(cli.last_folder)

        fake_folder = Path("C:/Dummy/Game")
        cli.last_folder = fake_folder
        self.assertEqual(cli.last_folder, fake_folder)


if __name__ == "__main__":
    unittest.main()
