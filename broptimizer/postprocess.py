"""Manejo de post-procesamiento: Reemplazo in-place o clonación a carpeta nueva con archivos faltantes."""

from pathlib import Path
import shutil

from broptimizer.manager import OptimizationSummary
from broptimizer.rpgmaker_cleaner import RPGMMVCleaner
from broptimizer.scanner import MediaStats


class PostProcessor:
    """Aplica los cambios de optimización según la elección del usuario."""

    @classmethod
    def apply_in_place(cls, summary: OptimizationSummary, root_dir: Path) -> int:
        """
        Opción 1: Reemplaza los archivos en la carpeta original con las versiones optimizadas.
        Retorna la cantidad de archivos modificados/reemplazados.
        """
        replaced_count = 0
        root_dir = root_dir.resolve()

        for res in summary.results:
            if not res.success or not res.is_smaller or not res.temp_output_path or not res.temp_output_path.is_file():
                continue

            orig_file = res.input_path
            orig_ext = orig_file.suffix.lower()
            target_ext = res.target_extension.lower()

            try:
                if orig_ext != target_ext:
                    # Si cambió la extensión (ej. PNG -> WEBP), eliminar el archivo viejo
                    orig_file.unlink(missing_ok=True)
                    new_dest = orig_file.parent / f"{orig_file.stem}{res.target_extension}"
                    shutil.move(str(res.temp_output_path), str(new_dest))
                else:
                    # Sobrescribir en el mismo lugar
                    shutil.move(str(res.temp_output_path), str(orig_file))

                replaced_count += 1
            except Exception as e:
                print(f"[Error al reemplazar {orig_file.name}]: {e}")

        # Limpiar directorio temporal
        summary.cleanup()
        return replaced_count

    @classmethod
    def export_standalone(
        cls,
        summary: OptimizationSummary,
        stats: MediaStats,
        dest_dir: Path,
        clean_nwjs: bool = False,
    ) -> tuple[int, int]:
        """
        Opción 2: Genera una carpeta nueva e independiente.
        Coloca los archivos optimizados y copia TODOS los archivos faltantes
        (ejecutables .exe, .ini, .dll, scripts, datos y multimedia no modificada)
        para que el juego o carpeta funcione perfectamente.
        Retorna (archivos_optimizados_colocados, archivos_faltantes_copiados).
        """
        dest_dir = dest_dir.resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        root_dir = stats.root_path.resolve()

        # Mapa de resultados optimizados por path original
        optimized_map = {
            res.input_path.resolve(): res
            for res in summary.results
            if res.success and res.is_smaller and res.temp_output_path and res.temp_output_path.is_file()
        }

        optimized_placed = 0
        missing_copied = 0

        # Recorrer todos los archivos inventariados durante el escaneo
        for file_info in stats.files:
            orig_path = file_info.path.resolve()
            rel_path = file_info.rel_path

            if clean_nwjs and RPGMMVCleaner.is_redundant_path(orig_path, root_dir):
                continue

            if orig_path in optimized_map:
                res = optimized_map[orig_path]
                # Archivo optimizado: colocar en destino con su extensión final
                final_filename = f"{orig_path.stem}{res.target_extension}"
                target_file_path = dest_dir / rel_path.parent / final_filename
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(str(res.temp_output_path), str(target_file_path))
                optimized_placed += 1
            else:
                # Archivo no modificado (ejecutables, scripts, ini, o multimedia no comprimida)
                target_file_path = dest_dir / rel_path
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(str(orig_path), str(target_file_path))
                    missing_copied += 1
                except Exception as e:
                    print(f"[Error al copiar {rel_path}]: {e}")

        # Limpiar directorio temporal
        summary.cleanup()
        return (optimized_placed, missing_copied)
