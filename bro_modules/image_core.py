import piexif, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from PIL import Image
from bro_modules import config as bcfg
from bro_modules import system as bsys
from bro_modules import file_manager as bfm

def mark_as_optimized_image(file:Path) -> bool:
    """  Añade el tag BROPTIMIZADO con el método apropiado según el tipo de archivo
    """
    im = Image.open(file)
    mark = bcfg.get_custom_mark()
    if im.format in ("PNG", "WEBP"):
        pnginfo = im.info.copy()
        pnginfo[mark] = mark
        im.save(file, pnginfo=pnginfo)    # Sobreescribe el mismo archivo
        return True
    elif im.format == "JPEG":
        exif_bytes = im.info.get("exif", b"")
        exif_dict = piexif.load(exif_bytes) if exif_bytes else {"Exif": {}} # type: ignore
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = f"{mark}:{mark}".encode()
        exif_bytes = piexif.dump(exif_dict) # type: ignore
        im.save(file, exif=exif_bytes)
        return True
    elif im.format == "GIF":
        im.info["comment"] = f"{mark}:{mark}".encode()
        im.save(file, save_all=True, comment=im.info["comment"])
        return True
    return False

def compress_image(project_folder:Path, cwebp_flags:list[str], source:Path):
    # Output será un webp disfrazado de png (u otra extensión del archivo original)
    # para facilitar la aceptación del archivo por parte del motor de RPG Maker y sus scripts
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = bfm.get_compressed_folder(project_folder)/rel_source
        command:list[str] = cwebp_flags.copy()
        command.append(f"{source}")
        command.append("-o")
        command.append(f"{output}")
        if len(command) > 0:
            try:
                subprocess.run(command)
            except Exception as e:
                # TODO
                print("ERROR en compress_image subprocess cwebp\n",f"source: {source}\n",f"output: {output}",e)

            bfm.compare_and_replace(source, output)
# END of function compress_image()

def process_images(project_folder:Path, cwebp_flags:list[str]):
    print("=== Preparando archivos de imágenes ===")
    max_threads = bsys.get_cpu_threads()
    source_list = bfm.get_source_list(project_folder, bcfg.get_image_extensions())
    if len(source_list) > 0:
        bfm.create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de imágenes ===")
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(compress_image, project_folder, cwebp_flags, source) for source in source_list}
            for _ in tqdm(as_completed(futures), desc="Comprimiendo imágenes", total=len(futures)):
                pass
# END of function process_images()

def is_optimized(file:Path) -> bool:
    """ Verifica la existencia del string "BROPTIMIZADO" dentro del tag comment en un archivo de video o audio
    """
    """ TODO Optimizar velocidad de verificación """
    if file.exists():
        mark = bcfg.get_custom_mark()
        try:
            im = Image.open(file)
            # 1. PNG, WEBP, GIF (info dict)
            if mark in im.info:
                return True
            # 2. JPEG (EXIF)
            if "exif" in im.info:
                exif_dict:dict = piexif.load(im.info["exif"]) # type: ignore
                user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, b"") # type: ignore
                if mark.encode() in user_comment:
                    return True
            # 3. GIF (comment)
            if im.format == "GIF" and "comment" in im.info:
                if mark.encode() in im.info["comment"]:
                    return True
        except Exception as e:
            # TODO
            print("ERROR is_optimized image", e)
        return False
        # end try
    return False
# END of function is_optimized()