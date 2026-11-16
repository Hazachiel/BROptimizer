"""Optimizador de audio utilizando FFprobe para inspección y FFmpeg para compresión perceptualmente transparente."""

import json
from pathlib import Path
import subprocess
import uuid

from broptimizer.config import Config
from broptimizer.engines.base import EngineProfile
from broptimizer.logger import ErrorLogger
from broptimizer.media.base import BaseMediaOptimizer, OptimizationResult
from broptimizer.tagger import MetadataTagger


def probe_audio(file_path: Path) -> tuple[int, int]:
    """
    Usa ffprobe para obtener (samplerate_hz, bitrate_bps).
    Retorna una tupla (sample_rate, bit_rate).
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(file_path),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    sr = int(stream.get("sample_rate") or 44100)
                    br = int(stream.get("bit_rate") or data.get("format", {}).get("bit_rate") or 0)
                    if br == 0:
                        duration = float(data.get("format", {}).get("duration") or 0)
                        if duration > 0:
                            file_size = file_path.stat().st_size
                            br = int((file_size * 8) / duration)
                    return sr, br
    except Exception as ex:
        ErrorLogger.log_error("AudioOptimizer.probe_audio", file_path, exception=ex)

    return 44100, 128000


def get_opus_samplerate(orig_sr: int) -> int:
    """
    libopus no debe superar los 48k (48000 Hz).
    Usa el menor posible redondeando hacia un valor aceptable para opus:
    8000, 12000, 16000, 24000, 48000 Hz.
    """
    for r in [8000, 12000, 16000, 24000, 48000]:
        if orig_sr <= r:
            return r
    return 48000


def get_vorbis_samplerate(orig_sr: int) -> int:
    """
    En vorbis el sample rate nunca debe superar los 32k (32000 Hz).
    """
    return min(32000, orig_sr)


def calculate_target_bitrate_kbps(orig_br: int, max_limit_kbps: int = 96) -> int:
    """
    El bitrate del audio no debe ser superior a 96k.
    Si el audio original tiene menos de 96k, se usa el bitrate original.
    """
    if orig_br > 0:
        orig_kbps = int(orig_br / 1000)
        if orig_kbps < max_limit_kbps:
            return max(16, orig_kbps)
    return max_limit_kbps


class AudioOptimizer(BaseMediaOptimizer):
    """Optimiza archivos de audio (OGG, MP3, WAV, Opus) con Vorbis como default y registro de errores."""

    def optimize(
        self,
        input_path: Path,
        temp_dir: Path,
        config: Config,
        profile: EngineProfile,
    ) -> OptimizationResult:
        orig_size = input_path.stat().st_size
        orig_ext = input_path.suffix.lower()

        # 1. Probing con ffprobe
        orig_sr, orig_br = probe_audio(input_path)

        # 2. Calcular bitrate objetivo (tope 96k, o bitrate original si < 96k)
        target_kbps = calculate_target_bitrate_kbps(orig_br, config.settings.max_audio_bitrate_kbps)

        # 3. Determinar formato destino (Vorbis por defecto para ogg/wav)
        target_audio_type = profile.get_target_audio_format(orig_ext)

        if config.preserve_extension:
            final_ext = orig_ext
        else:
            final_ext = f".{target_audio_type}"

        unique_id = uuid.uuid4().hex[:8]
        temp_filename = f"{input_path.stem}_{unique_id}{final_ext}"
        temp_output_path = temp_dir / temp_filename

        # 4. Configurar argumentos de códec y sample rate
        codec_args = []
        if target_audio_type == "opus" or final_ext == ".opus":
            opus_sr = get_opus_samplerate(orig_sr)
            codec_args = [
                "-c:a", "libopus",
                "-b:a", f"{target_kbps}k",
                "-ar", str(opus_sr),
            ]
        elif target_audio_type == "mp3" or final_ext == ".mp3":
            mp3_sr = min(32000, orig_sr)
            codec_args = [
                "-c:a", "libmp3lame",
                "-b:a", f"{target_kbps}k",
                "-ar", str(mp3_sr),
            ]
        else:
            # Vorbis por defecto para OGG, WAV u otros
            vorbis_sr = get_vorbis_samplerate(orig_sr)
            codec_args = [
                "-c:a", "libvorbis",
                "-b:a", f"{target_kbps}k",
                "-ar", str(vorbis_sr),
                "-q:a", "0",  # Calidad mínima para Vorbis
            ]

        meta_args = MetadataTagger.get_ffmpeg_metadata_args() if config.tag_metadata else []

        cmd = [
            "ffmpeg",
            "-y",
            "-v", "error",
            "-i", str(input_path),
            "-vn",
            *codec_args,
            *meta_args,
            str(temp_output_path),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if res.returncode != 0 or not temp_output_path.is_file():
                error_msg = res.stderr.strip() or "Error en transcodificación de audio con FFmpeg"
                ErrorLogger.log_error(
                    code_block="AudioOptimizer.optimize",
                    file_path=input_path,
                    error_msg=f"Comando: {' '.join(cmd)}\nStderr: {error_msg}",
                )
                return OptimizationResult(
                    input_path=input_path,
                    temp_output_path=None,
                    original_size=orig_size,
                    optimized_size=orig_size,
                    success=False,
                    is_smaller=False,
                    target_extension=orig_ext,
                    error_message=error_msg,
                )

            new_size = temp_output_path.stat().st_size
            is_smaller = new_size < orig_size

            if not is_smaller:
                temp_output_path.unlink(missing_ok=True)
                return OptimizationResult(
                    input_path=input_path,
                    temp_output_path=None,
                    original_size=orig_size,
                    optimized_size=orig_size,
                    success=True,
                    is_smaller=False,
                    target_extension=final_ext,
                )

            return OptimizationResult(
                input_path=input_path,
                temp_output_path=temp_output_path,
                original_size=orig_size,
                optimized_size=new_size,
                success=True,
                is_smaller=True,
                target_extension=final_ext,
            )

        except Exception as e:
            ErrorLogger.log_error(
                code_block="AudioOptimizer.optimize (Excepción)",
                file_path=input_path,
                exception=e,
            )
            return OptimizationResult(
                input_path=input_path,
                temp_output_path=None,
                original_size=orig_size,
                optimized_size=orig_size,
                success=False,
                is_smaller=False,
                target_extension=orig_ext,
                error_message=str(e),
            )
