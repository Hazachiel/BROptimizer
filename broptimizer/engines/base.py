"""Clase base y contratos para perfiles de motores de videojuegos."""

from abc import ABC


class EngineProfile(ABC):
    """Perfil que define reglas y formatos admitidos por un motor específico."""

    name: str = "generic"
    display_name: str = "Carpeta Genérica / Motor Desconocido"
    description: str = "Sin restricciones conocidas de motor. Admite formatos modernos."

    # Capacidades
    supports_webp: bool = True
    supports_opus: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    # Extensiones que el motor puede leer
    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".webp"}
    supported_audio_exts: set[str] = {".ogg", ".opus", ".mp3", ".wav"}
    supported_video_exts: set[str] = {".mp4", ".webm", ".mkv"}

    def get_target_image_format(self, original_ext: str, has_alpha: bool) -> str:
        """Determina el formato de imagen destino más eficiente y compatible."""
        ext = original_ext.lower()
        if self.supports_webp:
            return "webp"
        
        # Si no soporta WebP:
        if ext == ".png":
            if not has_alpha and self.allow_png_to_jpg_for_opaque:
                return "jpeg"
            return "png"
        if ext in (".jpg", ".jpeg"):
            return "jpeg"
        
        return "png"

    def get_target_audio_format(self, original_ext: str) -> str:
        """Determina el formato de audio óptimo compatible (Vorbis por defecto)."""
        ext = original_ext.lower()
        if ext in (".ogg", ".wav", ".flac"):
            return "ogg"
        if ext == ".opus":
            return "opus" if self.supports_opus else "ogg"
        if ext == ".mp3":
            return "mp3"
        return "ogg"

    def get_target_video_format(self, original_ext: str, preferred_video_codec: str = "vp8") -> tuple[str, str]:
        """
        Determina el contenedor y códec de video óptimos.
        Retorna (extensión_destino, codec_video).
        """
        ext = original_ext.lower()
        codec = preferred_video_codec.lower()

        if codec == "h264":
            return (".mp4", "h264")

        # Para VP8 o VP9
        if ext in (".webm", ".mkv"):
            return (".webm", codec)

        # Si el motor o formato original era MP4, mantener MP4
        if ext == ".mp4":
            return (".mp4", "h264")

        return (".webm", codec)
