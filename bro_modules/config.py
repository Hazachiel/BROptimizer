
def get_custom_mark() -> str:
    return "BROPTIMIZED"

def get_default_image_profile_name() -> str:
    """ Devuelve el nombre de perfil de compresión de imágenes por defecto a usar el el programa"""
    return "PERFORMANCE"

def get_default_cwebp_flags() -> list[str]:
    """ Devuelve los flags de cwebp que corresponden al perfil por defecto para la compresión de imágenes """
    return ["cwebp", "-q", "80", "-alpha_q", "100", "-exact", "-f", "30", "-af", "-quiet"]

def get_video_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de video que el propgrama procesasará """
    return (".mp4", ".webm", ".avi", ".mkv", ".mov")

def get_audio_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de audio que el propgrama procesasará """
    return (".ogg", ".mp3", ".wav", ".m4a", ".flac")

def get_image_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de imagenes que el propgrama procesasará """
    return (".jpg", ".jpeg", ".webp", ".png")

def get_useless_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos consideradas sin utilidad que el propgrama podría eliminar """
    # TODO
    return (".psd",)

def get_encrypted_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos encriptados """
    # TODO
    return (".rpgmvp", ".rpgmvm", ".rpgmvo",   # RPGM MV
            ".rpgmzp", ".rpgmzm", ".rpgmzo",   # RPGM MZ
            "ogg_", "m4a_", "wav_", "mp3_",    # Otros posibles archivos de audio cifrados
            "jpg_", "jpeg_", "png_", "webp_")  # Otros posibles archivos de imagen cifrados

def get_nwjs_files() -> tuple[str,...]:
    """ Devuelve una tupla que contiene los archivos de NW.js a buscar en la carpeta del juego seleccionado """
    return ("credits.html", "d3dcompiler_47.dll",
            "ffmpeg.dll", "icudtl.dat", 
            "libEGL.dll", "libGLESv2.dll", 
            "node.dll", "nw.dll",
            "nw_100_percent.pak", "nw_200_percent.pak", 
            "nw_elf.dll", "resources.pak", 
            "debug.log", "natives_blob.bin", 
            "snapshot_blob.bin", "v8_context_snapshot.bin",
            "notification_helper.exe", "vulkan-1.dll",
            "vk_swiftshader_icd.json", "vk_swiftshader.dll")

def get_nwjs_folders() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las carpetas de NW.js a buscar en la carpeta del juego seleccionado """
    return ("locales", "swiftshader")
