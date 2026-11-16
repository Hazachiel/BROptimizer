"""Optimizador de video con probing por FFprobe, cálculo dinámico de bitrate y soporte robusto para H.264, VP8 y VP9."""

import json
from pathlib import Path
import subprocess
import uuid

from broptimizer.config import Config
from broptimizer.engines.base import EngineProfile
from broptimizer.logger import ErrorLogger
from broptimizer.media.audio import calculate_target_bitrate_kbps, get_opus_samplerate, get_vorbis_samplerate
from broptimizer.media.base import BaseMediaOptimizer, OptimizationResult
from broptimizer.tagger import MetadataTagger


def probe_video(file_path: Path) -> dict[str, int | float | bool]:
    """
    Usa ffprobe para extraer parámetros detallados del stream de video y audio.
    Retorna diccionario con width, height, frame_rate, video_bitrate, audio_bitrate, audio_samplerate.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(file_path),
    ]
    meta: dict[str, int | float | bool] = {
        "width": 800,
        "height": 600,
        "frame_rate": 30.0,
        "video_bitrate": 0,
        "has_audio": False,
        "audio_bitrate": 0,
        "audio_samplerate": 32000,
    }
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            format_info = data.get("format", {})
            format_bitrate = int(format_info.get("bit_rate") or 0)

            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type")
                if codec_type == "video" and meta["video_bitrate"] == 0:
                    meta["width"] = int(stream.get("width") or 800)
                    meta["height"] = int(stream.get("height") or 600)
                    r_fps = stream.get("r_frame_rate", "30/1")
                    try:
                        if "/" in r_fps:
                            num, den = r_fps.split("/")
                            meta["frame_rate"] = float(num) / float(den) if float(den) > 0 else 30.0
                        else:
                            meta["frame_rate"] = float(r_fps)
                    except Exception:
                        meta["frame_rate"] = 30.0

                    v_br = int(stream.get("bit_rate") or 0)
                    meta["video_bitrate"] = v_br if v_br > 0 else format_bitrate

                elif codec_type == "audio" and not meta["has_audio"]:
                    meta["has_audio"] = True
                    meta["audio_samplerate"] = int(stream.get("sample_rate") or 32000)
                    meta["audio_bitrate"] = int(stream.get("bit_rate") or 0)
    except Exception as ex:
        ErrorLogger.log_error("VideoOptimizer.probe_video", file_path, exception=ex)

    return meta


def calculate_video_bitrate(
    width: int,
    height: int,
    frame_rate: float,
    desired_res: int,
    quality_multiplier: int,
    orig_video_bitrate: int = 0,
) -> int:
    """
    Aplica la fórmula matemática para obtener un bitrate de video óptimo y ajustado:
        aspect_ratio = max(width, height) / min(width, height)
        smaller_res = min(desired_res, width, height)
        kbps = ((smaller_res ** 2) * aspect_ratio * frame_rate) / 1000
        target_vbit_rate = int(quality_multiplier * (kbps ** 0.85))
    """
    w = max(1, width)
    h = max(1, height)
    aspect_ratio: float = max(w, h) / min(w, h)
    smaller_res: int = min(desired_res, w, h)
    fps = max(1.0, frame_rate)

    kbps: float = ((smaller_res ** 2) * aspect_ratio * fps) / 1000.0
    target_vbit_rate = int(quality_multiplier * (kbps ** 0.85))

    # Si el bitrate original es menor que el calculado, no aumentarlo
    if orig_video_bitrate > 0 and orig_video_bitrate < target_vbit_rate:
        return orig_video_bitrate
    return target_vbit_rate


class VideoOptimizer(BaseMediaOptimizer):
    """Optimiza archivos de video (MP4, WebM, MKV) aplicando compresión perceptual eficiente."""

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
        v_meta = probe_video(input_path)

        target_ext, _ = profile.get_target_video_format(orig_ext, config.video_codec)

        if config.preserve_extension:
            final_ext = orig_ext
        else:
            final_ext = target_ext

        unique_id = uuid.uuid4().hex[:8]
        temp_filename = f"{input_path.stem}_{unique_id}{final_ext}"
        temp_output_path = temp_dir / temp_filename

        # 2. Configuración de códec y formato
        active_codec = config.video_codec.lower()
        format_override_args = []
        target_res = round(min(config.desired_res, v_meta["width"], v_meta["height"]) / 2) * 2  # Asegurar resolución par

        if active_codec == "h264":
            quality_mult = config.settings.quality_mult_h264  # 400
            v_bitrate = calculate_video_bitrate(
                int(v_meta["width"]),
                int(v_meta["height"]),
                float(v_meta["frame_rate"]),
                int(target_res),
                int(quality_mult),
                int(v_meta["video_bitrate"]),
            )

            # Para H.264:
            # - pix_fmt yuv420p universal
            # - escala a dimensiones pares para evitar fallos de libx264
            # - si la extensión es .webm, forzar muxer matroska (-f matroska) para no ser rechazado por FFmpeg
            v_codec_args = [
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-b:v", str(v_bitrate),
                "-maxrate", f"{v_bitrate * 4}",     # permite picos hasta x
                "-bufsize", f"{v_bitrate * 4}",     # buffer para estabilizar
                "-crf", str(config.crf),
                "-preset", "fast",
            ]

            if final_ext in (".webm", ".mkv"):
                format_override_args = ["-f", "matroska"]
            else:
                v_codec_args.extend(["-movflags", "+faststart"])

            # Audio para H.264
            if v_meta["has_audio"]:
                target_a_kbps = calculate_target_bitrate_kbps(
                    int(v_meta["audio_bitrate"]),
                    int(config.settings.max_audio_bitrate_kbps),
                )
                a_codec_args = [
                    "-c:a", "aac",
                    "-b:a", f"{target_a_kbps}k",
                    "-ar", str(min(32000, int(v_meta["audio_samplerate"]))),
                ]
            else:
                a_codec_args = ["-an"]

        elif active_codec == "vp8":
            quality_mult = config.settings.quality_mult_vpx  # 250
            v_bitrate = calculate_video_bitrate(
                int(v_meta["width"]),
                int(v_meta["height"]),
                float(v_meta["frame_rate"]),
                int(target_res),
                int(quality_mult),
                int(v_meta["video_bitrate"]),
            )

            v_codec_args = [
                "-c:v", "libvpx",
                "-b:v", str(v_bitrate),
                "-maxrate", f"{v_bitrate * 4}",     # permite picos hasta x
                "-bufsize", f"{v_bitrate * 4}",     # buffer para estabilizar
                "-crf", str(config.crf),
                "-cpu-used", "2",
            ]

            # Audio con Vorbis por defecto
            if v_meta["has_audio"]:
                target_a_kbps = calculate_target_bitrate_kbps(
                    int(v_meta["audio_bitrate"]),
                    int(config.settings.max_audio_bitrate_kbps),
                )
                a_sr = get_vorbis_samplerate(int(v_meta["audio_samplerate"]))
                a_codec_args = [
                    "-c:a", "libvorbis",
                    "-b:a", f"{target_a_kbps}k",
                    "-ar", str(a_sr),
                ]
            else:
                a_codec_args = ["-an"]

        else:  # VP9 por defecto
            quality_mult = config.settings.quality_mult_vpx  # 250
            v_bitrate = calculate_video_bitrate(
                int(v_meta["width"]),
                int(v_meta["height"]),
                float(v_meta["frame_rate"]),
                int(target_res),
                int(quality_mult),
                int(v_meta["video_bitrate"]),
            )

            v_codec_args = [
                "-c:v", "libvpx-vp9",
                "-b:v", str(v_bitrate),
                "-maxrate", f"{v_bitrate * 4}",     # permite picos hasta x
                "-bufsize", f"{v_bitrate * 4}",     # buffer para estabilizar
                "-crf", str(config.crf),
                "-cpu-used", "2",
            ]

            if v_meta["has_audio"]:
                target_a_kbps = calculate_target_bitrate_kbps(
                    int(v_meta["audio_bitrate"]),
                    int(config.settings.max_audio_bitrate_kbps),
                )
                a_sr = get_opus_samplerate(int(v_meta["audio_samplerate"]))
                a_codec_args = [
                    "-c:a", "libopus",
                    "-b:a", f"{target_a_kbps}k",
                    "-ar", str(a_sr),
                ]
            else:
                a_codec_args = ["-an"]

        meta_args = MetadataTagger.get_ffmpeg_metadata_args() if config.tag_metadata else []
        if v_meta["width"] < v_meta["height"]:
            # Si el video es vertical, forzar escala a altura deseada y ancho proporcional
            scale_filter = f"scale=-2:{target_res}:flags=lanczos,smartblur=1.5:-0.5:1"
        else:
            # Si el video es horizontal, forzar escala a ancho deseado y altura proporcional
            scale_filter = f"scale={target_res}:-2:flags=lanczos,smartblur=1.5:-0.5:1"
        cmd = [
            "ffmpeg",
            "-y",
            "-v", "error",
            "-i", str(input_path),
            "-vf", scale_filter,
            *v_codec_args,
            *a_codec_args,
            *meta_args,
            *format_override_args,
            str(temp_output_path),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if res.returncode != 0 or not temp_output_path.is_file():
                error_msg = res.stderr.strip() or "Error en transcodificación de video con FFmpeg"
                ErrorLogger.log_error(
                    code_block="VideoOptimizer.optimize",
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
                code_block="VideoOptimizer.optimize (Excepción)",
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
