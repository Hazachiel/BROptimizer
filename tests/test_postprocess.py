"""Pruebas para los flujos de post-procesamiento (In-Place y Exportación Independiente)."""

from pathlib import Path
import tempfile
import unittest

from broptimizer.manager import OptimizationSummary
from broptimizer.media.base import OptimizationResult
from broptimizer.postprocess import PostProcessor
from broptimizer.scanner import FileInfo, MediaStats, MediaType


class TestPostProcessor(unittest.TestCase):

    def test_apply_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            orig_file = tmp_path / "image.png"
            orig_file.write_bytes(b"Original Uncompressed Content")

            # Archivo optimizado temporal
            staging = tmp_path / "staging"
            staging.mkdir()
            opt_file = staging / "image_opt.png"
            opt_file.write_bytes(b"Optimized")

            res = OptimizationResult(
                input_path=orig_file,
                temp_output_path=opt_file,
                original_size=len(b"Original Uncompressed Content"),
                optimized_size=len(b"Optimized"),
                success=True,
                is_smaller=True,
                target_extension=".png",
            )

            summary = OptimizationSummary(results=[res], temp_dir=staging)
            count = PostProcessor.apply_in_place(summary, tmp_path)

            self.assertEqual(count, 1)
            # El archivo original ahora debe contener el contenido optimizado
            self.assertEqual(orig_file.read_bytes(), b"Optimized")

    def test_export_standalone(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            orig_dir = tmp_path / "GameFolder"
            orig_dir.mkdir()

            # Archivo no multimedia (ejecutable del juego)
            exe_file = orig_dir / "Game.exe"
            exe_file.write_bytes(b"BinaryExecutableCode")

            # Archivo de configuración .ini
            ini_file = orig_dir / "settings.ini"
            ini_file.write_bytes(b"[Settings]\nfullscreen=1")

            nw_file = orig_dir / "nw.dll"
            nw_file.write_bytes(b"NW.js")
            locales_dir = orig_dir / "locales"
            locales_dir.mkdir()
            locale_file = locales_dir / "en-US.pak"
            locale_file.write_bytes(b"locale")

            # Archivo multimedia en subdirectorio
            sub_dir = orig_dir / "img" / "pictures"
            sub_dir.mkdir(parents=True)
            media_file = sub_dir / "bg.png"
            media_file.write_bytes(b"BigOriginalImage")

            # Staging con imagen optimizada
            staging = tmp_path / "staging"
            staging.mkdir()
            opt_media = staging / "bg_opt.png"
            opt_media.write_bytes(b"SmallImage")

            res = OptimizationResult(
                input_path=media_file,
                temp_output_path=opt_media,
                original_size=len(b"BigOriginalImage"),
                optimized_size=len(b"SmallImage"),
                success=True,
                is_smaller=True,
                target_extension=".png",
            )

            summary = OptimizationSummary(results=[res], temp_dir=staging)

            # Construir stats
            stats = MediaStats(root_path=orig_dir)
            stats.files = [
                FileInfo(exe_file, Path("Game.exe"), len(b"BinaryExecutableCode"), MediaType.OTHER, ".exe"),
                FileInfo(ini_file, Path("settings.ini"), len(b"[Settings]\nfullscreen=1"), MediaType.OTHER, ".ini"),
                FileInfo(nw_file, Path("nw.dll"), len(b"NW.js"), MediaType.OTHER, ".dll"),
                FileInfo(locale_file, Path("locales/en-US.pak"), len(b"locale"), MediaType.OTHER, ".pak"),
                FileInfo(media_file, Path("img/pictures/bg.png"), len(b"BigOriginalImage"), MediaType.IMAGE, ".png"),
            ]

            dest_dir = tmp_path / "GameFolder_Optimized"
            placed, copied = PostProcessor.export_standalone(summary, stats, dest_dir, clean_nwjs=True)

            self.assertEqual(placed, 1)
            self.assertEqual(copied, 2)

            # Verificar que todos los archivos existen en la carpeta destino
            self.assertTrue((dest_dir / "Game.exe").is_file())
            self.assertEqual((dest_dir / "Game.exe").read_bytes(), b"BinaryExecutableCode")

            self.assertTrue((dest_dir / "settings.ini").is_file())
            self.assertEqual((dest_dir / "settings.ini").read_bytes(), b"[Settings]\nfullscreen=1")
            self.assertFalse((dest_dir / "nw.dll").exists())
            self.assertFalse((dest_dir / "locales" / "en-US.pak").exists())

            dest_media = dest_dir / "img" / "pictures" / "bg.png"
            self.assertTrue(dest_media.is_file())
            self.assertEqual(dest_media.read_bytes(), b"SmallImage")


if __name__ == "__main__":
    unittest.main()
