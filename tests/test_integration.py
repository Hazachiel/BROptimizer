"""Prueba de integración integral de extremo a extremo (E2E)."""

import subprocess
import tempfile
from pathlib import Path
import unittest
from PIL import Image

from broptimizer.config import Config, Preset
from broptimizer.engines.detector import EngineDetector
from broptimizer.manager import OptimizationManager
from broptimizer.media.base import OptimizationResult
from broptimizer.postprocess import PostProcessor
from broptimizer.scanner import FolderScanner, MediaType
from broptimizer.tagger import MetadataTagger
from tests.test_optimizer import create_dummy_wav


def create_dummy_mp4(path: Path) -> None:
    """Genera un video MP4 de 1 segundo sintético usando FFmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-v", "error",
        "-f", "lavfi",
        "-i", "testsrc=duration=1:size=128x128:rate=10",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=1",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True)


class TestIntegrationE2E(unittest.TestCase):

    def test_full_workflow_and_second_pass_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            game_folder = Path(tmp) / "MyRenpyGame"
            game_folder.mkdir()

            # Estructura de Ren'Py
            (game_folder / "renpy").mkdir()
            game_sub = game_folder / "game"
            game_sub.mkdir()
            (game_sub / "options.rpy").write_text("define config.name = 'Test Game'")

            # 1. Imagen PNG grande (opaca)
            img_dir = game_sub / "images"
            img_dir.mkdir()
            img_opaque = img_dir / "bg_forest.png"
            im1 = Image.new("RGBA", (120, 120))
            for x in range(120):
                for y in range(120):
                    im1.putpixel((x, y), (x * 2, y * 2, (x * y) % 256, 255))
            im1.save(img_opaque, format="PNG", optimize=False)

            # 2. Imagen PNG con transparencia
            img_alpha = img_dir / "char_hero.png"
            im2 = Image.new("RGBA", (100, 100))
            for x in range(100):
                for y in range(100):
                    alpha = 0 if (x < 10 or y < 10) else 255
                    im2.putpixel((x, y), (200, 50, 50, alpha))
            im2.save(img_alpha, format="PNG", optimize=False)

            # 3. Audio WAV
            aud_dir = game_sub / "audio"
            aud_dir.mkdir()
            wav_sound = aud_dir / "effect.wav"
            create_dummy_wav(wav_sound, duration_sec=0.5)

            # 4. Video MP4
            vid_dir = game_sub / "video"
            vid_dir.mkdir()
            mp4_video = vid_dir / "cutscene.mp4"
            create_dummy_mp4(mp4_video)

            # 5. Archivos no multimedia
            (game_folder / "game.exe").write_bytes(b"MZExecutableStub")
            (game_folder / "settings.ini").write_text("[System]\nlang=es")

            # --- PASADA 1: DETECCIÓN Y ESCANEO ---
            profile = EngineDetector.detect(game_folder)
            self.assertEqual(profile.name, "renpy")

            stats = FolderScanner.scan(game_folder, check_tags=True)
            self.assertEqual(stats.images.file_count, 2)
            self.assertEqual(stats.audios.file_count, 1)
            self.assertEqual(stats.videos.file_count, 1)
            self.assertEqual(stats.others.file_count, 3)  # options.rpy, game.exe, settings.ini
            self.assertEqual(stats.total_tagged_count, 0)

            # --- PASADA 1: PROCESAMIENTO CON PRESET LOSSY ---
            config = Config(
                preset=Preset.LOSSY,
                video_codec="vp9",
                preserve_extension=True,
                max_video_workers=1,
                tag_metadata=True,
            )
            manager = OptimizationManager(config, profile)
            media_files = [f for f in stats.files if f.media_type != MediaType.OTHER]
            summary = manager.process_files(media_files)

            self.assertGreater(summary.optimized_count, 0)
            self.assertGreater(summary.total_saved_bytes, 0)

            # Aplicar in-place
            replaced = PostProcessor.apply_in_place(summary, game_folder)
            self.assertEqual(replaced, summary.optimized_count)

            # --- PASADA 2: VERIFICAR MARCA BROptimized ---
            stats_pass2 = FolderScanner.scan(game_folder, check_tags=True)
            # Todos los archivos optimizados deben estar etiquetados
            self.assertGreater(stats_pass2.total_tagged_count, 0)

            # Procesar nuevamente con el manager
            media_files_p2 = [f for f in stats_pass2.files if f.media_type != MediaType.OTHER]
            summary_pass2 = manager.process_files(media_files_p2)

            # En la segunda pasada, los ya marcados deben omitirse
            self.assertGreater(summary_pass2.skipped_count, 0)
            summary_pass2.cleanup()


if __name__ == "__main__":
    unittest.main()
