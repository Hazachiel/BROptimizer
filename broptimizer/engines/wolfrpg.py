"""Perfil de compatibilidad para juegos desarrollados en Wolf RPG Editor."""

from broptimizer.engines.base import EngineProfile


class WolfRpgProfile(EngineProfile):
    """
    Wolf RPG Editor (DirectX 9 / GDI+).
    NO soporta WebP ni códecs Opus.
    Imágenes compatibles: PNG (con canal alfa o color transparente) y JPG (fondos opacos).
    Audios: OGG Vorbis, WAV, MP3, MIDI.
    """
    name: str = "wolfrpg"
    display_name: str = "Wolf RPG Editor"
    description: str = "Motor C++/DirectX 9. NO admite WebP. Imágenes en PNG/JPG y audio en OGG Vorbis."

    supports_webp: bool = False
    supports_opus: bool = False
    supports_vorbis: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".bmp"}
    supported_audio_exts: set[str] = {".ogg", ".wav", ".mp3", ".mid"}
    supported_video_exts: set[str] = {".avi", ".wmv", ".mp4"}

    def get_target_video_format(self, original_ext: str, preferred_webm_codec: str = "libx264") -> tuple[str, str]:
        return (original_ext.lower(), "libx264")
