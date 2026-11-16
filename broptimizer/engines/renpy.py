"""Perfil de compatibilidad para novelas visuales y juegos Ren'Py."""

from broptimizer.engines.base import EngineProfile


class RenpyProfile(EngineProfile):
    """
    Ren'Py 6.18+ / 7+ / 8+ soporta WebP nativamente con decodificación veloz.
    Audios: OGG Vorbis, Opus (7.4+), MP3 y WAV.
    Videos: WebM (VP8/VP9) y MP4 (H.264).
    """
    name: str = "renpy"
    display_name: str = "Ren'Py Visual Novel Engine"
    description: str = "Soporta WebP, Ogg/Opus y WebM VP8/VP9."

    supports_webp: bool = True
    supports_opus: bool = True
    supports_vorbis: bool = True
    allow_png_to_jpg_for_opaque: bool = True

    supported_image_exts: set[str] = {".png", ".jpg", ".jpeg", ".webp"}
    supported_audio_exts: set[str] = {".ogg", ".opus", ".mp3", ".wav"}
    supported_video_exts: set[str] = {".webm", ".mp4", ".mkv", ".ogv"}

    def get_target_video_format(self, original_ext: str, preferred_webm_codec: str = "vp8") -> tuple[str, str]:
        preferred_webm_codec = "vp8" if preferred_webm_codec != "vp9" else "vp9"
        return (original_ext.lower(), preferred_webm_codec)