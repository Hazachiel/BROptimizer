"""Configuración y Presets de Optimización para BROptimizer."""

from dataclasses import dataclass
from enum import Enum
import os


class Preset(str, Enum):
    """Presets de calidad de optimización."""
    LOSSY = "lossy"
    NEARLOSSLESS = "nearlossless"


class TargetCategory(str, Enum):
    """Categoría de archivos multimedia a optimizar."""
    ALL = "all"
    IMAGES = "images"
    AUDIO = "audio"
    VIDEO = "video"


VALID_VIDEO_CODECS = ("vp8", "vp9", "h264")
VALID_CRF_VALUES = (15, 26, 31)


@dataclass
class PresetSettings:
    """Parámetros de compresión para un preset específico."""
    name: str
    description: str

    # Imágenes
    webp_quality: int
    webp_method: int
    jpeg_quality: int
    png_compression_level: int

    # Audio
    max_audio_bitrate_kbps: int  # Tope máximo de bitrate de audio (96k)
    max_opus_samplerate: int     # 48000 Hz
    max_vorbis_samplerate: int   # 44100 Hz

    # Video
    default_video_codec: str     # 'h264' por defecto
    default_crf: int             # 26 para lossy, 15 para nearlossless
    quality_mult_h264: int       # 400
    quality_mult_vpx: int        # 250


PRESET_DEFINITIONS: dict[Preset, PresetSettings] = {
    Preset.LOSSY: PresetSettings(
        name="Lossy (Recomendado)",
        description="Máximo ahorro de espacio con calidad casi indistinguible para el ojo y oído humano.",
        webp_quality=80,
        webp_method=6,
        jpeg_quality=80,
        png_compression_level=9,
        max_audio_bitrate_kbps=96,
        max_opus_samplerate=48000,
        max_vorbis_samplerate=44100,
        default_video_codec="h264",
        default_crf=26,
        quality_mult_h264=400,
        quality_mult_vpx=250,
    ),
    Preset.NEARLOSSLESS: PresetSettings(
        name="Nearlossless",
        description="Fidelidad visual y auditiva de alta precisión con compresión superior al original.",
        webp_quality=92,
        webp_method=6,
        jpeg_quality=90,
        png_compression_level=9,
        max_audio_bitrate_kbps=96,
        max_opus_samplerate=48000,
        max_vorbis_samplerate=44100,
        default_video_codec="h264",
        default_crf=15,
        quality_mult_h264=400,
        quality_mult_vpx=250,
    ),
}


class Config:
    """Configuración global de ejecución de BROptimizer."""

    def __init__(
        self,
        preset: Preset = Preset.LOSSY,
        target_category: TargetCategory = TargetCategory.ALL,
        video_codec: str = "h264",
        preserve_extension: bool = True,
        max_video_workers: int = 1,
        max_general_workers: int | None = None,
        tag_metadata: bool = True,
        desired_res: int = 600,
        crf: int = 26,
        vpx_crf: int | None = None,
        h264_crf: int | None = None,
    ) -> None:
        self.preset = preset
        self.target_category = target_category
        
        # Códec de video: H264 por defecto
        codec_clean = str(video_codec).lower()
        self.video_codec = codec_clean if codec_clean in VALID_VIDEO_CODECS else "h264"

        self.preserve_extension = preserve_extension
        # Límite estricto de conversiones de video simultáneas (1 o 2)
        self.max_video_workers = max(1, min(2, max_video_workers))
        self.max_general_workers = max_general_workers or max(1, os.cpu_count() or 4)
        self.tag_metadata = tag_metadata
        self.desired_res = max(120, desired_res)

        # CRF unificado: permite 15, 26, 31 (por defecto 26)
        selected_crf = crf
        if vpx_crf in VALID_CRF_VALUES:
            selected_crf = vpx_crf
        elif h264_crf in VALID_CRF_VALUES:
            selected_crf = h264_crf

        if selected_crf not in VALID_CRF_VALUES:
            selected_crf = self.settings.default_crf
        self.crf = selected_crf

    @property
    def vpx_crf(self) -> int:
        return self.crf

    @vpx_crf.setter
    def vpx_crf(self, val: int) -> None:
        if val in VALID_CRF_VALUES:
            self.crf = val

    @property
    def h264_crf(self) -> int:
        return self.crf

    @h264_crf.setter
    def h264_crf(self, val: int) -> None:
        if val in VALID_CRF_VALUES:
            self.crf = val

    def cycle_video_codec(self) -> str:
        """Cicla entre VP8 -> VP9 -> H264 -> VP8."""
        order = ["vp8", "vp9", "h264"]
        try:
            curr_idx = order.index(self.video_codec)
            next_idx = (curr_idx + 1) % len(order)
            self.video_codec = order[next_idx]
        except ValueError:
            self.video_codec = "vp8"
        return self.video_codec

    def cycle_crf(self) -> int:
        """Cicla entre 15 -> 26 -> 31 -> 15."""
        order = [15, 26, 31]
        try:
            curr_idx = order.index(self.crf)
            next_idx = (curr_idx + 1) % len(order)
            self.crf = order[next_idx]
        except ValueError:
            self.crf = 26
        return self.crf

    @property
    def settings(self) -> PresetSettings:
        return PRESET_DEFINITIONS[self.preset]

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "preset": self.preset.value,
            "target_category": self.target_category.value,
            "video_codec": self.video_codec,
            "crf": self.crf,
            "preserve_extension": self.preserve_extension,
            "max_video_workers": self.max_video_workers,
            "max_general_workers": self.max_general_workers,
            "tag_metadata": self.tag_metadata,
            "desired_res": self.desired_res,
        }

    @classmethod
    def load_from_settings(cls, settings: dict | None = None, **overrides) -> "Config":
        """
        Carga la configuración combinando broptimizer_settings.json con valores por defecto tolerantes a fallos.
        Si el archivo no existe, está corrupto o falta alguna clave, aplica h264 y crf=26 por defecto.
        """
        if settings is None:
            try:
                from broptimizer.gui.views.preferences.pref_storage import load_all_settings
                settings = load_all_settings()
            except Exception:
                settings = {}

        # Preset
        preset_val = settings.get("preset", "lossy")
        try:
            preset = Preset(preset_val)
        except (ValueError, TypeError):
            preset = Preset.LOSSY

        # TargetCategory
        cat_val = settings.get("target_category", "all")
        try:
            target_category = TargetCategory(cat_val)
        except (ValueError, TypeError):
            target_category = TargetCategory.ALL

        # Video Codec
        v_codec = str(settings.get("video_codec", "h264")).lower()
        if v_codec not in VALID_VIDEO_CODECS:
            v_codec = "h264"

        # CRF
        crf_val = settings.get("crf", 26)
        try:
            crf_val = int(crf_val)
            if crf_val not in VALID_CRF_VALUES:
                crf_val = 26
        except (ValueError, TypeError):
            crf_val = 26

        # Workers / Hilos
        max_v_workers = settings.get("threads_video", 1)
        try:
            max_v_workers = max(1, min(2, int(max_v_workers)))
        except (ValueError, TypeError):
            max_v_workers = 1

        max_g_workers = settings.get("threads_image", None)
        try:
            if max_g_workers is not None:
                max_g_workers = max(1, int(max_g_workers))
        except (ValueError, TypeError):
            max_g_workers = None

        # Desired res
        desired_res = settings.get("desired_res", 600)
        try:
            desired_res = max(120, int(desired_res))
        except (ValueError, TypeError):
            desired_res = 600

        # Preserve ext & Tag metadata
        preserve_ext = bool(settings.get("preserve_extension", True))
        tag_meta = bool(settings.get("tag_metadata", True))

        cfg_kwargs = {
            "preset": preset,
            "target_category": target_category,
            "video_codec": v_codec,
            "crf": crf_val,
            "preserve_extension": preserve_ext,
            "max_video_workers": max_v_workers,
            "max_general_workers": max_g_workers,
            "tag_metadata": tag_meta,
            "desired_res": desired_res,
        }
        cfg_kwargs.update(overrides)

        instance = cls(**cfg_kwargs)

        # Ajustes de compresión avanzados si están presentes en settings
        try:
            if "webp_quality" in settings:
                instance.settings.webp_quality = int(settings["webp_quality"])
            if "webp_method" in settings:
                instance.settings.webp_method = int(settings["webp_method"])
            if "jpeg_quality" in settings:
                instance.settings.jpeg_quality = int(settings["jpeg_quality"])
            if "png_compression" in settings:
                instance.settings.png_compression_level = int(settings["png_compression"])
            if "max_audio_bitrate" in settings:
                instance.settings.max_audio_bitrate_kbps = int(settings["max_audio_bitrate"])
            if "max_opus_samplerate" in settings:
                instance.settings.max_opus_samplerate = int(settings["max_opus_samplerate"])
            if "max_vorbis_samplerate" in settings:
                instance.settings.max_vorbis_samplerate = int(settings["max_vorbis_samplerate"])
            if "quality_mult_h264" in settings:
                instance.settings.quality_mult_h264 = int(settings["quality_mult_h264"])
            if "quality_mult_vpx" in settings:
                instance.settings.quality_mult_vpx = int(settings["quality_mult_vpx"])
        except Exception:
            pass

        return instance
