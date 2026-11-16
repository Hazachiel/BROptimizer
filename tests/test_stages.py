"""Pruebas para el procesamiento en etapas secuenciales y filtrado de categorías."""

from pathlib import Path
import tempfile
import unittest
from PIL import Image

from broptimizer.config import Config, Preset, TargetCategory
from broptimizer.engines.generic import GenericProfile
from broptimizer.manager import OptimizationManager
from broptimizer.scanner import FileInfo, MediaType
from tests.test_optimizer import create_dummy_wav


class TestStagesAndCategoryFilters(unittest.TestCase):

    def test_staged_execution_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)

            # Crear una imagen
            img_path = p / "test.png"
            img = Image.new("RGB", (30, 30), (255, 0, 0))
            img.save(img_path, format="PNG")

            # Crear un audio
            aud_path = p / "test.wav"
            create_dummy_wav(aud_path, duration_sec=0.2)

            file_img = FileInfo(img_path, Path("test.png"), img_path.stat().st_size, MediaType.IMAGE, ".png")
            file_aud = FileInfo(aud_path, Path("test.wav"), aud_path.stat().st_size, MediaType.AUDIO, ".wav")

            config = Config(target_category=TargetCategory.ALL)
            manager = OptimizationManager(config, GenericProfile())

            stages_logged = []

            def on_progress(stage_label, completed, total, file_info, res):
                stages_logged.append(stage_label)

            summary = manager.process_files([file_img, file_aud], progress_callback=on_progress)

            # Debe haber registrado Etapa 1 para Imágenes y Etapa 2 para Audios
            self.assertTrue(any("Imágenes" in s for s in stages_logged))
            self.assertTrue(any("Audios" in s for s in stages_logged))
            # Verificar que la primera etapa registrada es Imágenes y luego Audios
            first_img_idx = next(i for i, s in enumerate(stages_logged) if "Imágenes" in s)
            first_aud_idx = next(i for i, s in enumerate(stages_logged) if "Audios" in s)
            self.assertLess(first_img_idx, first_aud_idx)

            summary.cleanup()

    def test_filter_only_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            img_path = p / "test.png"
            Image.new("RGB", (20, 20)).save(img_path)
            aud_path = p / "test.wav"
            create_dummy_wav(aud_path, duration_sec=0.2)

            file_img = FileInfo(img_path, Path("test.png"), img_path.stat().st_size, MediaType.IMAGE, ".png")
            file_aud = FileInfo(aud_path, Path("test.wav"), aud_path.stat().st_size, MediaType.AUDIO, ".wav")

            config = Config(target_category=TargetCategory.IMAGES)
            manager = OptimizationManager(config, GenericProfile())

            summary = manager.process_files([file_img, file_aud])

            # Solo debió procesar la imagen
            self.assertEqual(len(summary.results), 1)
            self.assertEqual(summary.results[0].input_path, img_path)
            summary.cleanup()

    def test_filter_only_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            img_path = p / "test.png"
            Image.new("RGB", (20, 20)).save(img_path)
            aud_path = p / "test.wav"
            create_dummy_wav(aud_path, duration_sec=0.2)

            file_img = FileInfo(img_path, Path("test.png"), img_path.stat().st_size, MediaType.IMAGE, ".png")
            file_aud = FileInfo(aud_path, Path("test.wav"), aud_path.stat().st_size, MediaType.AUDIO, ".wav")

            config = Config(target_category=TargetCategory.AUDIO)
            manager = OptimizationManager(config, GenericProfile())

            summary = manager.process_files([file_img, file_aud])

            # Solo debió procesar el audio
            self.assertEqual(len(summary.results), 1)
            self.assertEqual(summary.results[0].input_path, aud_path)
            summary.cleanup()


if __name__ == "__main__":
    unittest.main()
