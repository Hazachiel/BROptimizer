import shutil, os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from bro_modules import system as bsys
from bro_modules import logger as blog
from bro_modules import config as bcfg
from bro_modules import image_core
from bro_modules import av_core

def get_localappdata() -> Path|None:
    """ Devuelve un Path con la dirección de la carpeta ~/AppData/Local, y si no la encuentra devuelve un Path vacio """
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        return None
    return Path(local_appdata)

def get_script_folder() -> Path:
    """ Devuelve la ruta actual del programa principal """
    return Path(__file__).parent.parent

def get_logs_folder() -> Path:
    """ Devuelve la ruta hacia la carpeta logs del programa """
    logs_folder = get_script_folder()/"logs"
    if not logs_folder.exists():
        logs_folder.mkdir(parents=True, exist_ok=True)
    return logs_folder

def get_game_launch_file() -> Path:
    """ Devuelve la ruta hacia el lanzador del juego junto al programa """
    return get_script_folder()/"nwjs_game_launch.bat"
    
def get_folder_size(folder:Path) -> float:
    """ Recorre una carpeta y devuelve el peso en MB de todo su contenido """
    size = sum(file.stat().st_size for file in folder.rglob('*') if file.is_file())
    size = round(size/1000000, ndigits=2)
    return size

def subfolder_of(folder:Path, parent:Path) -> bool:
    if str(parent) in str(folder):
        return True
    return False

def get_compressed_folder(project_folder:Path) -> Path:
    """ Devuelve la ruta de la carpeta compressed del programa, y la crea si no existe """
    compressed_folder = project_folder.parent/"broptimized_temp"
    if not compressed_folder.exists():
        compressed_folder.mkdir(parents=True, exist_ok=True)
    return compressed_folder

def create_output_path(project_folder:Path, source_file_list:list[Path]):
    for source_file in source_file_list:
        rel_source_file = source_file.relative_to(project_folder)
        output_file = get_compressed_folder(project_folder)/rel_source_file
        if not output_file.parent.exists():
            output_file.parent.mkdir(parents=True, exist_ok=True)

def select_folder(folder_type: str) -> Path|None:
    """ Abre la ventana de dialogo de selección de directorios """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder = filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir")
    tk_root.destroy()
    if len(selected_folder) == 0:
        return None
    return Path(selected_folder)

def select_file(project_folder:Path, file_name:str, extension:str) -> Path|None:
    """ Abre la ventana de dialogo de selección de archivos """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_file = filedialog.askopenfilename(title=f"Selecciona el archivo {file_name} correspondiente", filetypes=[(f"{extension}",f"{extension}")], initialdir=str(project_folder))
    tk_root.destroy()
    if len(selected_file) == 0:
        return None
    return Path(selected_file)

def delete_folder(folder:Path):
    """ Toma un directorio elimina todo su contenido """
    if folder.exists():
        try:
            shutil.rmtree(folder, ignore_errors=True)
            print(f"Eliminado directorio: {folder}")
        except Exception as e:
            blog.log_exception(e, "delete_folder", "rmtree in delete_folder", folder)

def delete_files_in_list(folder: Path, files_to_remove: tuple[str,...]) -> float:
    """ Toma un directorio y una lista, busca en el directorio los archivos que se encuentren en la lista y los elimina """
    files_size:float = 0.0
    for root, _, files in folder.walk():
        for file in files:
            if file in files_to_remove:
                file_path = Path(root/file)
                if file_path.exists():
                    try:
                        files_size += file_path.stat().st_size
                        file_path.unlink()
                        print(f"Eliminado: {file_path.relative_to(folder.parent)}")
                    except Exception as e:
                        blog.log_exception(e, "delete_files_in_list", "file unlink", file_path)
    return files_size

def delete_folders_in_list(folder: Path, folders_to_remove: tuple[str,...]) -> float:
    """ Toma un directorio y una lista, busca en el directorio los nombres de directorios que se encuentren en la lista y los elimina """
    folder_size:float = 0.0
    for root, dirs, _ in folder.walk():
        for dir in dirs:
            if dir in folders_to_remove:
                current_folder = (root/dir)
                if current_folder.exists():
                    folder_size += get_folder_size(current_folder)
                    try:
                        shutil.rmtree(current_folder, ignore_errors=True)
                        print( f"Eliminado directorio: {current_folder}")
                    except Exception as e:
                        blog.log_exception(e, "delete_folders_in_list", "rmtree in delete_folder", current_folder)
    return folder_size

def compare_project_size(original_size:float, new_size:float):
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño del proyecto originalmente:.....{original_size}MB")
    print(f"Espacio Ahorrado tras la compresión:...{round(original_size-new_size, ndigits=2)}MB")
    print(f"Tamaño actual del proyecto:............{new_size}MB")

def get_source_list(project_folder:Path, extensions:tuple[str,...]) -> list[Path]:
    source_file_list:list[Path] = []
    if extensions == bcfg.get_image_extensions():
        is_optimized = image_core.is_optimized
    else:
        is_optimized = av_core.is_optimized
    with ThreadPoolExecutor(max_workers=bsys.get_cpu_threads()) as executor:
        # La función is_optimized toma mucho tiempo en procesar. 
        # Hasta que una versión más rapida de verificación sea encontrada...
        # permanecerá sin uso real y retornando False por defecto de forma automática
        futures = {executor.submit(is_optimized, root/file):root/file
                   for root,_,files in project_folder.walk() 
                   for file in files
                   if file.endswith(extensions)}
        for future in tqdm(as_completed(futures), desc="Filtrando archivos...", total=len(futures)):
            if not future.result():
                source_file_list.append(futures[future])
    return source_file_list

def compare_and_replace(original:Path, compressed:Path) -> bool:
    """ Compara dos archivos en directorios diferentes:
    * Si original es más pesado, lo reemplaza por compressed y marca compressed
    * Si original es más ligero, elimina compressed y marca original
    """
    if compressed.exists() and original.exists():
        if compressed.stat().st_size < original.stat().st_size:
            try:
                # Compressed ya está marcado como Optimizado
                original.unlink()
            except Exception as e:
                # TODO
                print("ERROR compare_and_replace compressed is smaller")
                print("----- original.unlink", e)
            try:
                compressed.replace(original.with_suffix(compressed.suffix))
            except Exception as e:
                print("ERROR compare_and_replace compressed is smaller")
                print("----- compressed.replace", e)
            # end try
        else:
            if original.suffix.lower() in (bcfg.get_image_extensions()):
                result = image_core.mark_as_optimized(original)
            else:
                result = av_core.mark_as_optimized(original)
            if result:
                try:
                    compressed.unlink()
                except Exception as e:
                    # TODO
                    print("ERROR compare_and_replace original is smaller",e)
                    print("----- compressed.unlink", e)
    return True
# END of function compare_and_replace()
    