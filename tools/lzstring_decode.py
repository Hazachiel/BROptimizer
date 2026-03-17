import lzstring
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def select_input_folder() -> Path | None:
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Selecciona la carpeta con los archivos comprimidos")
    root.destroy()
    return Path(folder) if folder else None

def main():
    input_folder = select_input_folder()
    if not input_folder:
        print("No se seleccionó carpeta.")
        return

    # Buscamos todos los .txt (o cambia la extensión si usas otra)
    files = list(input_folder.glob("*.jsono"))  # o "*.lz", "*.compressed", etc.

    if not files:
        print("No se encontraron archivos .txt en la carpeta.")
        return

    print(f"Encontrados {len(files)} archivos para procesar.\n")

    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                compressed = f.read().strip()

            decoded = lzstring.LZString().decompressFromBase64(compressed)

            # Guardamos con el mismo nombre pero cambiando _decoded o extensión
            output_path = file_path.with_suffix(".json")  # o .txt
            if decoded != None:
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(decoded)

                print(f"OK → {file_path.name} → {output_path.name}")
            else:
                print(f"ERROR en decompresión de {compressed}\n")
        except Exception as e:
            print(f"ERROR en {file_path.name}: {type(e).__name__} - {str(e)}")

    print("\n¡Proceso terminado!")

if __name__ == "__main__":
    main()