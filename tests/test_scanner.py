"""Pruebas para el escáner de archivos, cálculo de estadísticas y detección de encriptados."""

import tempfile
from pathlib import Path
import unittest

from broptimizer.scanner import FolderScanner, MediaType


class TestFolderScanner(unittest.TestCase):

    def test_scan_and_categorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)

            # Crear imágenes
            img1 = p / "bg.png"
            img1.write_bytes(b"a" * 100)
            img2 = p / "character.jpg"
            img2.write_bytes(b"b" * 200)

            # Crear audio
            aud1 = p / "bgm.ogg"
            aud1.write_bytes(b"c" * 300)

            # Crear video
            vid1 = p / "op.mp4"
            vid1.write_bytes(b"d" * 500)

            # Crear otros (ejecutable, script, ini)
            exe1 = p / "Game.exe"
            exe1.write_bytes(b"e" * 1000)
            ini1 = p / "config.ini"
            ini1.write_bytes(b"f" * 50)

            stats = FolderScanner.scan(p, check_tags=False)

            self.assertEqual(stats.total_files, 6)
            self.assertEqual(stats.total_size, 2150)
            self.assertEqual(stats.images.file_count, 2)
            self.assertEqual(stats.images.total_size, 300)
            self.assertEqual(stats.audios.file_count, 1)
            self.assertEqual(stats.audios.total_size, 300)
            self.assertEqual(stats.videos.file_count, 1)
            self.assertEqual(stats.videos.total_size, 500)
            self.assertEqual(stats.others.file_count, 2)
            self.assertEqual(stats.others.total_size, 1050)
            self.assertEqual(stats.total_media_count, 4)
            self.assertEqual(stats.total_media_size, 1100)
            self.assertEqual(stats.encrypted_packed_count, 0)

    def test_detect_encrypted_and_packed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)

            # RPG Maker encrypted
            (p / "picture.rpgmvp").write_bytes(b"enc_png")
            (p / "audio.rpgmvo").write_bytes(b"enc_ogg")
            (p / "movie.rpgmvm").write_bytes(b"enc_mp4")

            # Ren'Py archive
            (p / "scripts.rpa").write_bytes(b"RPA-3.0")

            # Wolf RPG archive
            (p / "Data.wolf").write_bytes(b"WOLF")

            # RPG Maker RGSS archive
            (p / "Game.rgss3a").write_bytes(b"RGSSAD")

            stats = FolderScanner.scan(p, check_tags=False)

            self.assertEqual(stats.encrypted_packed_count, 6)
            self.assertEqual(len(stats.encrypted_packed_files), 6)
            exts = {f.extension.lower() for f in stats.encrypted_packed_files}
            self.assertIn(".rpgmvp", exts)
            self.assertIn(".rpgmvo", exts)
            self.assertIn(".rpgmvm", exts)
            self.assertIn(".rpa", exts)
            self.assertIn(".wolf", exts)
            self.assertIn(".rgss3a", exts)


if __name__ == "__main__":
    unittest.main()
