"""Pruebas para el marcado y lectura de metadatos 'BROptimized'."""

import tempfile
from pathlib import Path
import unittest
from PIL import Image

from broptimizer.tagger import MetadataTagger, TAG_KEY, TAG_VALUE


class TestMetadataTagger(unittest.TestCase):

    def test_image_tagging_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "test.png"
            img = Image.new("RGBA", (32, 32), (255, 0, 0, 255))

            save_kwargs = MetadataTagger.attach_image_metadata(img, "PNG", {})
            img.save(img_path, format="PNG", **save_kwargs)

            # Verificar que el tagger detecte que ya está marcado
            self.assertTrue(MetadataTagger.is_tagged(img_path))

    def test_image_tagging_webp(self):
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "test.webp"
            img = Image.new("RGB", (32, 32), (0, 255, 0))

            save_kwargs = MetadataTagger.attach_image_metadata(img, "WEBP", {})
            img.save(img_path, format="WEBP", **save_kwargs)

            self.assertTrue(MetadataTagger.is_tagged(img_path))

    def test_untagged_file_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "clean.bin"
            file_path.write_bytes(b"Clean file without any metadata markers")
            self.assertFalse(MetadataTagger.is_tagged(file_path))

    def test_ffmpeg_metadata_args(self):
        args = MetadataTagger.get_ffmpeg_metadata_args()
        self.assertIn("-metadata", args)
        self.assertIn(f"{TAG_KEY}={TAG_VALUE}", args)


if __name__ == "__main__":
    unittest.main()
