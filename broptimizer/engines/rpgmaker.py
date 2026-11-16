"""Perfiles de compatibilidad para juegos de RPG Maker (MZ, MV, XP, VX, VX Ace)."""

from broptimizer.engines.base import EngineProfile


class RpgMakerMzProfile(EngineProfile):
    """
    RPG Maker MZ y MV (basados en Chromium / Web).
    Soportan WebP de forma nativa/moderna.
    Imágenes opacas pueden convertirse a JPG si se desea, con WebP para transparencias.
    Audios principales: OGG Vorbis, M4A, MP3.
    Videos: WebM, MP4.
    """
    name: str = "rpgmaker_modern"
    display_name: str = "RPG Maker MZ / MV (Chromium/Web)"
    description: str = "Soporta WebP nativo, JPG para imágenes opacas, OGG Vorbis y WebM/MP4."

    supports_webp: bool = True
    supports_opus: bool = False  # OGG Vorbis es el estándar universal en RPG Maker MV/MZ
    supports_vorbis: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".webp"}
    supported_audio_exts: set[str] = {".ogg", ".m4a", ".mp3", ".wav"}
    supported_video_exts: set[str] = {".webm", ".mp4"}

    def get_target_video_format(self, original_ext: str, preferred_webm_codec: str = "vp8") -> tuple[str, str]:
        preferred_webm_codec = "vp8" if preferred_webm_codec != "vp9" else "vp9"
        return (original_ext.lower(), preferred_webm_codec)

class RpgMakerLegacyProfile(EngineProfile):
    """
    RPG Maker XP, VX, VX Ace (basados en RGSS / DirectDraw).
    NO soportan WebP. Las imágenes DEBEN permanecer como PNG o JPG.
    Audios: OGG Vorbis, MP3, WAV.
    Videos: OGG Theora, WMV, AVI.
    """
    name: str = "rpgmaker_legacy"
    display_name: str = "RPG Maker XP / VX / VX Ace (RGSS)"
    description: str = "Motor heredado. NO admite WebP. Imágenes en PNG/JPG y audio en OGG Vorbis/MP3."

    supports_webp: bool = False
    supports_opus: bool = False
    supports_vorbis: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".bmp"}
    supported_audio_exts: set[str] = {".ogg", ".mp3", ".wav", ".mid"}
    supported_video_exts: set[str] = {".ogv", ".avi", ".wmv", ".mp4"}

    def get_target_video_format(self, original_ext: str, preferred_webm_codec: str = "libx264") -> tuple[str, str]:
        # Para motores legados, mantener contenedor original con H.264 o stream óptimo
        return (original_ext.lower(), "libx264")
