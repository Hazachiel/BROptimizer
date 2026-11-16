"""Pruebas de limpieza de componentes NW.js de RPG Maker MV/MZ."""

import json
from pathlib import Path
import tempfile
import unittest

from broptimizer.rpgmaker_cleaner import RPGMMVCleaner


class TestRPGMMVCleaner(unittest.TestCase):
    def test_scan_and_clean_preserves_locales_translations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "swiftshader").mkdir()
            (root / "swiftshader" / "shader.bin").write_bytes(b"shader")
            (root / "Dictionaries").mkdir()
            (root / "nw.dll").write_bytes(b"nw")
            locales = root / "locales"
            locales.mkdir()
            (locales / "en-US.pak").write_bytes(b"pak")
            (locales / "en-US.info").write_bytes(b"info")
            (locales / "es.json").write_text("{}", encoding="utf-8")

            found = RPGMMVCleaner.scan_nwjs_files(root)
            self.assertEqual(found["count"], 5)
            removed_count, removed_size = RPGMMVCleaner.clean_nwjs(root)

            self.assertEqual(removed_count, 5)
            self.assertGreater(removed_size, 0)
            self.assertFalse((root / "swiftshader").exists())
            self.assertFalse((root / "Dictionaries").exists())
            self.assertFalse((root / "nw.dll").exists())
            self.assertFalse((locales / "en-US.pak").exists())
            self.assertFalse((locales / "en-US.info").exists())
            self.assertTrue((locales / "es.json").exists())

    def test_patch_package_json_at_root_and_www(self):
        for package_location in ("root", "www"):
            with self.subTest(package_location=package_location), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                package_dir = root if package_location == "root" else root / "www"
                package_dir.mkdir(exist_ok=True)
                package_path = package_dir / "package.json"
                package_path.write_text(json.dumps({"name": "Old", "main": "index.html", "window": {"width": 816}}), encoding="utf-8")

                self.assertTrue(RPGMMVCleaner.patch_package_json(root))
                data = json.loads(package_path.read_text(encoding="utf-8"))
                self.assertEqual(data["name"], "RPGM")
                self.assertEqual(data["window"]["position"], "center")
                self.assertEqual(data["window"]["width"], 816)
                self.assertEqual(data["main"], "index.html")

    def test_copy_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "nwjs_game_launch.bat"
            source.write_text("launch", encoding="utf-8")
            destination = root / "game"

            self.assertTrue(RPGMMVCleaner.copy_launcher(destination, source))
            self.assertEqual((destination / source.name).read_text(encoding="utf-8"), "launch")


if __name__ == "__main__":
    unittest.main()
