"""Perfil genérico para carpetas generales y motores modernos sin restricciones."""

from broptimizer.engines.base import EngineProfile


class GenericProfile(EngineProfile):
    """
    Carpeta estándar de archivos o motor no detectado.
    Permite el uso de todos los formatos modernos de compresión:
    WebP para imágenes, Opus/OGG para audio, WebM VP9/VP8 y MP4 H.264 para video.
    """
    name: str = "generic"
    display_name: str = "Carpeta Estándar / Genérica"
    description: str = "Sin restricciones de motor. Permite compresión máxima con WebP, Opus, Vorbis y WebM."

    supports_webp: bool = True
    supports_opus: bool = True
    supports_vorbis: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    supported_audio_exts: set[str] = {".ogg", ".opus", ".mp3", ".wav", ".flac", ".m4a"}
    supported_video_exts: set[str] = {".webm", ".mp4", ".mkv", ".avi", ".mov"}

    def get_target_video_format(self, original_ext: str, preferred_webm_codec: str) -> tuple[str, str]:
        return (original_ext.lower(), preferred_webm_codec)