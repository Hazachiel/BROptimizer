import subprocess, exiftool # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from bro_modules import config as bcfg
from bro_modules import system as bsys
from bro_modules import file_manager as bfm

def compress_image(project_folder:Path, cwebp_flags:list[str], source:Path) -> tuple[Path,Path]|None:
    # Output será un webp disfrazado de png (u otra extensión del archivo original)
    # para facilitar la aceptación del archivo por parte del motor de RPG Maker y sus scripts
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = bfm.get_compressed_folder(project_folder)/rel_source
        command:list[str] = cwebp_flags.copy()
        command.append(f"{source}")
        command.append("-o")
        command.append(f"{output}")
        try:
            subprocess.run(command)
        except Exception as e:
            # TODO
            print("ERROR en compress_image subprocess cwebp\n",f"source: {source}\n",f"output: {output}",e)
        return source, output
    return None
# END of function compress_image()

def process_images(project_folder:Path, cwebp_flags:list[str]):
    print("=== Preparando archivos de imágenes ===")
    max_threads = bsys.get_cpu_threads()
    source_list = bfm.get_source_list(project_folder, bcfg.get_image_extensions())
    result_list:list[tuple[Path,Path]] = []
    if len(source_list) > 0:
        bfm.create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de imágenes ===")
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(compress_image, project_folder, cwebp_flags, source)
                       for source in source_list}
            for future in tqdm(as_completed(futures), desc="Comprimiendo imágenes", total=len(futures)):
                result = future.result()
                if result:
                    result_list.append(result)
    if len(result_list) > 0:
        print("=== Iniciando comparación de imágenes ===")
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(bfm.compare_and_replace, original, compressed)
                       for original, compressed in result_list}
            for _ in tqdm(as_completed(futures), desc="Comparando resultados", total=len(futures)):
                pass
# END of function process_images()

def mark_as_optimized(file:Path) -> bool:
    """ Añade el tag BROPTIMIZED como metadata al archivo de imagen usando exiftool

    Retorna True si todo sale bien, de lo contrario retorna False
    """
    if file.exists():
        tag = "File:FileTypeExtension"
        with exiftool.ExifToolHelper() as et:
            metadata:dict[str,str] = dict(et.get_tags(str(file), tag)[0]) # type: ignore
        file_type = f".{str(metadata.get(tag)).lower()}" # File:FileTypeExtension
        file_original_ext = file.suffix.lower()
        if file_type != file_original_ext:
            file = file.rename(file.with_suffix(file_type))
        
        mark:str = bcfg.get_custom_mark()
        try:
            with exiftool.ExifToolHelper() as et:
                et.set_tags(file,  # type: ignore
                            tags={"XMP:UserComment": mark}, 
                            params=["-overwrite_original", "-q"])
            if file.suffix != file_original_ext:
                file.rename(file.with_suffix(file_original_ext))
            return True
        except Exception as e:
            print("ERROR, mark_as_optimized exiftool\n", e)
            return False
        # end try
    return False
# END of function mark_as_optimized()

def is_optimized(file:Path) -> bool:
    """ Verifica la existencia del string "BROPTIMIZED" dentro de la metadata del archivo de imagen

    Retorna True si lo encuentra, de lo contrario retorna False
    """
    if file.exists():
        mark:str = bcfg.get_custom_mark()   # returns the optimized mark
        """ # Notas de opciones para otros formatos de imagen
        keys = [
            "XMP:UserComment", "EXIF:UserComment", "PNG:Comment",
            "XMP:Description", "IPTC:Caption-Abstract", "GIF:Comment"
        ] """
        tags = ["XMP:UserComment", "GIF:Comment"]
        with exiftool.ExifToolHelper() as et:
            metadata:dict[str,str] = dict(et.get_tags(str(file), tags)[0]) # type: ignore
        
        for tag in tags:
            if tag in metadata and mark in str(metadata[tag]): # type: ignore
                return True
        return False
    else:
        return False
# END of function is_optimized()