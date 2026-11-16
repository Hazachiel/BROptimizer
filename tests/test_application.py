"""Pruebas de los servicios compartidos por CLI y GUI."""

from pathlib import Path
import tempfile
import unittest

from broptimizer.application import AnalysisService


class TestApplicationServices(unittest.TestCase):
    def test_analyze_detects_rpgmaker_and_nwjs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "js").mkdir()
            (root / "js" / "rmmz_core.js").touch()
            (root / "nw.dll").write_bytes(b"nw")
            (root / "locales").mkdir()
            (root / "locales" / "en-US.pak").write_bytes(b"pak")

            result = AnalysisService.analyze(root)

            self.assertEqual(result.profile.name, "rpgmaker_modern")
            self.assertEqual(result.nwjs["count"], 2)
            self.assertGreater(result.nwjs["size"], 0)

    def test_clean_rpgmaker_updates_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text('{"name":"Game"}', encoding="utf-8")
            (root / "nw.dll").write_bytes(b"nw")

            result = AnalysisService.clean_rpgmaker(root)

            self.assertEqual(result.removed_count, 1)
            self.assertTrue(result.package_updated)
            self.assertFalse((root / "nw.dll").exists())


if __name__ == "__main__":
    unittest.main()
