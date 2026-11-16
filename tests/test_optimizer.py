"""Pruebas para los optimizadores de imágenes y audio, detección de transparencia y fórmulas matemáticas."""

import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from PIL import Image

from broptimizer.config import Config, Preset
from broptimizer.engines.generic import GenericProfile
from broptimizer.engines.renpy import RenpyProfile
from broptimizer.engines.rpgmaker import RpgMakerLegacyProfile
from broptimizer.media.audio import (
    AudioOptimizer,
    calculate_target_bitrate_kbps,
    get_opus_samplerate,
    get_vorbis_samplerate,
)
from broptimizer.media.image import ImageOptimizer
from broptimizer.media.video import VideoOptimizer, calculate_video_bitrate


def create_dummy_wav(path: Path, duration_sec: float = 1.0, sample_rate: int = 44100) -> None:
    """Genera un archivo WAV de prueba con una onda senoidal de 440 Hz."""
    num_samples = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            value = int(16000 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            frames.extend(struct.pack("<h", value))
        wav.writeframes(frames)


class TestOptimizers(unittest.TestCase):

    def test_transparency_detection(self):
        # 1. Imagen RGBA con píxel transparente
        img_trans = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img_trans.putpixel((5, 5), (0, 0, 0, 0))
        self.assertTrue(ImageOptimizer.check_transparency(img_trans))

        # 2. Imagen RGBA totalmente opaca
        img_opaque = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        self.assertFalse(ImageOptimizer.check_transparency(img_opaque))

        # 3. Imagen RGB sin canal alfa
        img_rgb = Image.new("RGB", (10, 10), (255, 0, 0))
        self.assertFalse(ImageOptimizer.check_transparency(img_rgb))

    def test_image_optimization_and_extension_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            temp_staging = tmp_path / "staging"
            temp_staging.mkdir()

            img_path = tmp_path / "sprite.png"
            img = Image.new("RGBA", (128, 128))
            for x in range(128):
                for y in range(128):
                    img.putpixel((x, y), (x * 2, y * 2, (x + y) % 256, 255 if x > 10 else 100))
            img.save(img_path, format="PNG", optimize=False)
            orig_size = img_path.stat().st_size

            config = Config(preset=Preset.LOSSY, preserve_extension=True)
            profile = RenpyProfile()
            optimizer = ImageOptimizer()

            res = optimizer.optimize(img_path, temp_staging, config, profile)

            self.assertTrue(res.success)
            self.assertTrue(res.is_smaller)
            self.assertIsNotNone(res.temp_output_path)
            self.assertLess(res.optimized_size, orig_size)
            self.assertEqual(res.target_extension, ".png")
            self.assertTrue(res.temp_output_path.name.endswith(".png"))

            with Image.open(res.temp_output_path) as opt_img:
                self.assertEqual(opt_img.size, (128, 128))

    def test_audio_rules_samplerate_and_bitrate(self):
        # 1. Bitrate cap at 96k
        self.assertEqual(calculate_target_bitrate_kbps(320000, 96), 96)
        self.assertEqual(calculate_target_bitrate_kbps(128000, 96), 96)
        self.assertEqual(calculate_target_bitrate_kbps(64000, 96), 64)
        self.assertEqual(calculate_target_bitrate_kbps(32000, 96), 32)
        # Sin bitrate conocido o 0 -> 96k
        self.assertEqual(calculate_target_bitrate_kbps(0, 96), 96)

        # 2. Opus sample rate rounding (<= 48k)
        self.assertEqual(get_opus_samplerate(44100), 48000)
        self.assertEqual(get_opus_samplerate(48000), 48000)
        self.assertEqual(get_opus_samplerate(96000), 48000)
        self.assertEqual(get_opus_samplerate(22050), 24000)
        self.assertEqual(get_opus_samplerate(16000), 16000)
        self.assertEqual(get_opus_samplerate(11025), 12000)
        self.assertEqual(get_opus_samplerate(8000), 8000)

        # 3. Vorbis sample rate cap (<= 44.1k)
        self.assertEqual(get_vorbis_samplerate(48000), 44100)
        self.assertEqual(get_vorbis_samplerate(96000), 44100)
        self.assertEqual(get_vorbis_samplerate(44100), 44100)
        self.assertEqual(get_vorbis_samplerate(22050), 22050)

    def test_video_dynamic_bitrate_formula(self):
        # 1280x720 @ 30fps con desired_res = 600
        # aspect_ratio = 1280 / 720 ≈ 1.7777777778
        # smaller_res = min(600, 720) = 600
        # kbps = (600^2 * 1.7777777778 * 30) / 1000 = 19200.0
        # kbps^0.85 = 19200^0.85 ≈ 4272.0396
        # target_vbit_rate con H.264 (400) = int(400 * 4272.0396) = 1708815 bps
        # target_vbit_rate con VP8/VP9 (250) = int(250 * 4272.0396) = 1068009 bps
        h264_br = calculate_video_bitrate(1280, 720, 30.0, desired_res=600, quality_multiplier=400)
        vpx_br = calculate_video_bitrate(1280, 720, 30.0, desired_res=600, quality_multiplier=250)

        self.assertAlmostEqual(h264_br, 1749307, delta=50)
        self.assertAlmostEqual(vpx_br, 1093316, delta=50)

        # Comprobar que no infla un video con bitrate original inferior
        capped_br = calculate_video_bitrate(1280, 720, 30.0, desired_res=600, quality_multiplier=400, orig_video_bitrate=500000)
        self.assertEqual(capped_br, 500000)

    def test_audio_optimization_wav_to_ogg(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wav_path = tmp_path / "sound.wav"
            create_dummy_wav(wav_path, duration_sec=1.0)
            orig_size = wav_path.stat().st_size

            temp_staging = tmp_path / "staging"
            temp_staging.mkdir()

            config = Config(preset=Preset.LOSSY, preserve_extension=False)
            profile = GenericProfile()
            optimizer = AudioOptimizer()

            res = optimizer.optimize(wav_path, temp_staging, config, profile)

            self.assertTrue(res.success)
            self.assertTrue(res.is_smaller)
            self.assertIsNotNone(res.temp_output_path)
            self.assertLess(res.optimized_size, orig_size / 2)


if __name__ == "__main__":
    unittest.main()
