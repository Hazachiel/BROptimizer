import subprocess, os, json
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bro_modules import system as bsys
from bro_modules import file_manager as bfm
from bro_modules import config as bcfg

def get_audio_hz(project_folder:Path, file: Path) -> int:
    """ Analiza un archivo de audio con ffprobe y devuelve sus hz o 0 si hay error """
    command_ffprobe = [
        "ffprobe", "-v", "-quiet", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        f"{file}"
    ]
    try:
        result = subprocess.run(command_ffprobe, capture_output=True, text=True)
        hz = int(result.stdout.strip())
    except Exception:
        hz = 0
    # end try
    return hz

def optimal_video_quality(source:Path, quality:int, plus:int|float) -> tuple[int, int, str]:
    """ Recibe un video y devuelve su resolución y bitrate optimos junto con su escala
    * source: Path que apunta a un archivo de video
    * quality: lado más pequeño de resolución deseada
    * plus: umbral de calidad
    """
    width, height = get_video_resolution(source)
    original_res:int = min(width, height)
    if original_res == 0:
        return 0,0,""
    
    target_res:int = min(original_res, quality)
    if width > height:
        vf_scale = f"-2:{target_res}"
    else:
        vf_scale = f"{target_res}:-2"

    original_kbps:int = get_video_kbps(source)
    target_optimal_kbps:int = optimal_kbps_for_resolution(target_res, plus)
    original_optimal_kbps:int = optimal_kbps_for_resolution(original_res, plus)

    if original_kbps == 0:
        return target_res, target_optimal_kbps, vf_scale

    if original_res <= target_res:
        if original_kbps <= original_optimal_kbps:
            return original_res, original_kbps, vf_scale
        else:
            return original_res, original_optimal_kbps, vf_scale
    else:
        ratio:float = original_kbps/original_optimal_kbps
        if ratio >= 1:
            return target_res, target_optimal_kbps, vf_scale
        else:
            return target_res, int(target_optimal_kbps*ratio), vf_scale
# END of function optimal_video_quality()

def get_video_kbps(video_path:Path) -> int:
    cmd = [
        "ffprobe", "-v", "-quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "csv=s=x:p=0", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        result = int(result.stdout.strip())
        return int(result/1000)
        
    except subprocess.CalledProcessError as e:
        print("Error al obtener el bit rate", e)
    except Exception as e:
        print("Ocurrió un error inesperado - get_video_bitrate()", e)
    return 0

def optimal_kbps_for_resolution(quality:int, plus:float|int = 1.15) -> int:
    return int(((quality ** 2 / 180)  - (15/4) * quality + 1020)*plus)

def get_video_resolution(video_path:Path) -> tuple[int, int]:
    """
    Obtiene la resolución de un video usando ffprobe.
    Retorna ancho y alto si se completó con éxito, None si algo falló.
    """
    cmd = [
        "ffprobe", "-v", "-quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = result.stdout.strip().split("x")
        return int(width), int(height)
    except subprocess.CalledProcessError as e:
        print("Error al obtener resolución", e.stdout)
        return 0,0
    except Exception as e:
        print("Ocurrió un error inesperado - get_video_resolution()", e)
        return 0,0
# END of function get_video_resolution()

def mark_as_optimized_ffmpeg(file:Path) -> bool:
    """ Copia el flujo de datos (sin recodificar) y añade el tag BROPTIMIZADO.
    """
    output = file.with_stem(f"{file.stem}_broptimized")
    command:list[str] = [
        "ffmpeg", "-hide_banner", "-loglevel", "quiet",
        "-y",                                   # Sobreescribe archivos de salida
        "-i", str(file),
        "-c", "copy",                           # Copia exacta de audio/video/imagen
        "-map_metadata", "0",                   # Mantiene metadatos originales
        "-metadata", "comment=BROPTIMIZADO",    # Añade la marca
        str(output)
    ]
    try:
        subprocess.run(command)
        file.unlink()
        output.rename(file)
        return True
    except Exception as e:
        # TODO
        print("ERROR in mark_as_optimized subprocess, unlink, rename", e)
    # end try
    return False
# END of function mark_as_optimized()

def compress_audio(project_folder:Path, source:Path):
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = bfm.get_compressed_folder(project_folder)/rel_source
        output = output.with_suffix(".ogg")
        hz = get_audio_hz(project_folder, source)
        if 22050 <= hz < 32000:
            hz = 22050
        else:
            hz = 32000
        command:list[str] = [
                "ffmpeg", "-hide_banner", "-loglevel", "quiet",
                "-i", f"{source}",
                "-c:a", "libvorbis", 
                "-ar", f"{hz}", 
                "-q:a", "0", 
                "-y",                                   # Sobreescribe archivos de salida
                "-map_metadata", "0",                   # Mantiene metadatos originales
                "-metadata", "comment=BROPTIMIZADO",    # Añade una marca
                f"{output}"
            ]
        if len(command) > 0:
            try:
                subprocess.run(command)
            except Exception as e:
                # TODO
                print("ERROR",e)

            bfm.compare_and_replace(source, output)
# END of function compress_audio()

def compress_video(project_folder:Path, quality:int, plus:int|float, source:Path):
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = bfm.get_compressed_folder(project_folder)/rel_source.with_suffix(".mp4")
        target_res, video_bitrate, vf_scale = optimal_video_quality(source, quality, plus)

        if min(target_res, video_bitrate) == 0 or vf_scale == "":
            return False
        
        audio_bitrate = "48"
        audio_codec = "libopus"
        extra = ["-pix_fmt", "yuv420p", "-ar", "48000", "-tune", "animation"]
        video_codec = "libx264"

        passlog = "ffmpeg_pass_temp"
        null = "NUL" if os.name == "nt" else "/dev/null"

        cmd1:list[str] = [
            "ffmpeg", "-hide_banner", "-loglevel", "quiet",
            "-i", str(source),
            "-vf", f"scale={vf_scale}",
            "-c:v", video_codec,
            "-preset", "medium",
            *extra,
            "-b:v", f"{video_bitrate}k",
            "-pass", "1",
            "-passlogfile", passlog,
            "-an", "-f", "null", null
        ]
        try:
            subprocess.run(cmd1, check=True)
        except subprocess.CalledProcessError as e:
            print("Falló Pass 1", e)
            return False
        # end try

        # Pass 2
        cmd2:list[str] = [
            "ffmpeg", "-hide_banner", "-loglevel", "quiet",
            "-i", str(source),
            "-vf", f"scale={vf_scale}",
            "-c:v", video_codec,
            "-preset", "medium",
            *extra,
            "-b:v", f"{video_bitrate}k",
            "-pass", "2",
            "-passlogfile", passlog,
            "-c:a", audio_codec,
            "-b:a", f"{audio_bitrate}k",
            "-y",                                   # Sobreescribe archivos de salida
            "-map_metadata", "0",                   # Mantiene metadatos originales
            "-metadata", "comment=BROPTIMIZADO",    # Añade la marca
            str(output)
        ]
        try:
            subprocess.run(cmd2, check=True)
        except subprocess.CalledProcessError as e:
            print("Falló Pass 2", e)
            return False
        # end try

        bfm.compare_and_replace(source, output)

        # Limpieza
        for passlog_file in [f"{passlog}-0.log", f"{passlog}-0.log.mbtree"]:
            passlog_file = Path(passlog_file)
            if passlog_file.is_file():
                passlog_file.unlink()
        return True
# END of function compress_video()

def process_audios(project_folder:Path):
    print("=== Preparando archivos de audio ===")
    max_threads = bsys.get_cpu_threads()
    source_list = bfm.get_source_list(project_folder, bcfg.get_audio_extensions())
    if len(source_list) > 0:
        bfm.create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de audios ===")
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(compress_audio, project_folder, source) for source in source_list}
            for _ in tqdm(as_completed(futures), desc="Comprimiendo audios", total=len(futures)):
                pass
# END of function process_audios()

def process_videos(project_folder:Path, quality:int = 600, plus:int|float = 1.15):
    print("=== Preparando archivos de videos ===")
    # Limitación a 1 hilo debido a que el procesamiento de videos es más pesado
    # Se mantiene el formato del código para actualizarlo en el futuro
    max_threads = 1 
    source_list = bfm.get_source_list(project_folder, bcfg.get_video_extensions())
    if len(source_list) > 0:
        bfm.create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de videos ===")
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(compress_video, project_folder, quality, plus, source) for source in source_list}
            for _ in tqdm(as_completed(futures), desc="Comprimiendo videos", total=len(futures)):
                pass
# END of function process_videos()

def is_optimized(file:Path) -> bool:
    """ Verifica la existencia del string "BROPTIMIZADO" dentro del tag comment en un archivo de video o audio
    """
    """ TODO Optimizar velocidad de verificación """
    if file.exists():
        command:list[str] = [
            "ffprobe", 
            "-v", "-quiet",
            "-print_format", "json",
            "-show_entries", "format_tags=comment",
            "-of", "json",
            str(file)
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print("ERROR running ffprobe", result.stderr)
                return False
            data = json.loads(result.stdout)
            comment = data.get("format", {}).get("tags", {}).get("comment")
            return comment == bcfg.get_custom_mark()
        except Exception as e:
            # TODO
            print("ERROR is_optimized video or audio", e)
    return False
# END of function is_optimized()