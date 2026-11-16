"""Pruebas para certificar la corrección de fallos en transcodificación con H.264."""

import subprocess
import tempfile
from pathlib import Path
import unittest

from broptimizer.config import Config
from broptimizer.engines.generic import GenericProfile
from broptimizer.media.video import VideoOptimizer


def create_test_video(path: Path, width: int = 120, height: int = 120) -> None:
    """Crea un video de prueba con FFmpeg adecuado para su contenedor."""
    ext = path.suffix.lower()
    if ext == ".mp4":
        vcodec = "libx264"
        acodec = "aac"
    else:
        vcodec = "libvpx"
        acodec = "libvorbis"

    cmd = [
        "ffmpeg",
        "-y",
        "-v", "error",
        "-f", "lavfi",
        "-i", f"testsrc=duration=1:size={width}x{height}:rate=10",
        "-f", "lavfi",
        "-i", "sine=frequency=800:duration=1",
        "-c:v", vcodec,
        "-c:a", acodec,
        str(path),
    ]
    subprocess.run(cmd, check=True)


class TestH264Fix(unittest.TestCase):

    def test_h264_with_webm_extension_preservation(self):
        """
        Verifica que H.264 sobre un archivo con extensión .webm no falle,
        gracias al forzado del muxer Matroska (-f matroska).
        """
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            staging = p / "staging"
            staging.mkdir()

            webm_file = p / "cutscene.webm"
            create_test_video(webm_file, width=128, height=128)

            # Forzar códec H.264 preservando la extensión original .webm
            config = Config(video_codec="h264", crf=26, preserve_extension=True)
            profile = GenericProfile()
            optimizer = VideoOptimizer()

            res = optimizer.optimize(webm_file, staging, config, profile)

            # La transcodificación debe ser exitosa sin errores
            self.assertTrue(res.success, f"Error en conversión H.264 a WebM: {res.error_message}")
            self.assertIsNone(res.error_message)

    def test_h264_with_odd_dimensions(self):
        """
        Verifica que un video con dimensiones impares (ej. 101x101)
        se transcodifique con H.264 sin arrojar error de libx264.
        """
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            staging = p / "staging"
            staging.mkdir()

            odd_video = p / "odd.mp4"
            create_test_video(odd_video, width=102, height=102)  # Video fuente estándar

            # Ahora probamos transcodificar forzando un video impar directamente
            odd_source = p / "odd_uncompressed.avi"
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "testsrc=duration=1:size=101x101:rate=10",
                "-c:v", "rawvideo", "-pix_fmt", "bgr24",
                str(odd_source),
            ]
            subprocess.run(cmd, check=True)

            config = Config(video_codec="h264", crf=26, preserve_extension=True)
            profile = GenericProfile()
            optimizer = VideoOptimizer()

            res = optimizer.optimize(odd_source, staging, config, profile)

            self.assertTrue(res.success, f"Error en video con tamaño impar: {res.error_message}")
            self.assertIsNone(res.error_message)


if __name__ == "__main__":
    unittest.main()
