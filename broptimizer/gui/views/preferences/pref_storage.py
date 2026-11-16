"""Gestor compartido de preferencias y guardado en JSON."""

import json
import os
from pathlib import Path
from typing import Any

from broptimizer import PROJECT_ROOT

SETTINGS_FILE = PROJECT_ROOT / "broptimizer_settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    # Sistema
    "nw_path": "",
    "profile_path": r"%localappdata%\RPGM\User Data",
    "threads_image": 8,
    "threads_audio": 8,
    "threads_video": 1,
    "temp_folder_custom": "",
    "use_custom_temp": False,

    # Imágenes
    "webp_quality": 82,
    "webp_method": 6,
    "png_compression": 9,
    "jpeg_quality": 80,
    "tag_metadata": True,

    # Audio
    "max_opus_samplerate": 48000,
    "max_vorbis_samplerate": 44100,
    "max_mp3_samplerate": 44100,
    "max_audio_bitrate": 96,

    # Video
    "video_codec": "h264",
    "crf": 26,
    "desired_res": 600,
    "quality_mult_h264": 400,
    "quality_mult_vpx": 250,
    "force_yuv420p": True,
    "force_matroska_webm": True,
    "preserve_extension": True,
}


def load_all_settings() -> dict[str, Any]:
    """Carga la configuración combinada con valores por defecto."""
    settings = DEFAULT_SETTINGS.copy()
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            settings.update(saved)
        except Exception:
            pass
    return settings


def save_settings_dict(updates: dict[str, Any]) -> None:
    """Actualiza y persiste las configuraciones en el archivo JSON."""
    current = load_all_settings()
    current.update(updates)
    temp_file = SETTINGS_FILE.with_suffix(".tmp")
    try:
        temp_file.write_text(json.dumps(current, indent=2), encoding="utf-8")
        os.replace(temp_file, SETTINGS_FILE)
    except Exception as exc:
        print(f"[Error guardando settings en {SETTINGS_FILE}]: {exc}")
        if temp_file.exists():
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass

