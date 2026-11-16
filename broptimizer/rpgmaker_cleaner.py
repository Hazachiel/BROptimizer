"""Limpieza segura de componentes redundantes de NW.js en RPG Maker MV/MZ."""

import json
from pathlib import Path
import shutil


class RPGMMVCleaner:
    """Detecta y elimina componentes embebidos de NW.js sin tocar los datos del juego."""

    ROOT_FILES = {
        "credits.html",
        "d3dcompiler_47.dll",
        "ffmpeg.dll",
        "icudtl.dat",
        "libegl.dll",
        "libglesv2.dll",
        "node.dll",
        "nw.dll",
        "nw_100_percent.pak",
        "nw_200_percent.pak",
        "nw_elf.dll",
        "resources.pak",
        "debug.log",
        "natives_blob.bin",
        "snapshot_blob.bin",
        "v8_context_snapshot.bin",
        "notification_helper.exe",
        "vulkan-1.dll",
        "vk_swiftshader_icd.json",
        "vk_swiftshader.dll",
    }
    DIRECTORY_NAMES = {"swiftshader", "dictionaries"}

    @classmethod
    def _nwjs_paths(cls, root: Path) -> list[Path]:
        """Devuelve los elementos redundantes presentes, respetando el caso del sistema."""
        paths: list[Path] = []
        if root / "www" in root.iterdir() if root.is_dir() else []:
            paths.extend(cls._nwjs_paths(root / "www"))  # Escanear subdirectorio www si existe
        for item in root.iterdir() if root.is_dir() else []:
            if item.name.lower() in cls.ROOT_FILES:
                paths.append(item)
            elif item.is_dir() and item.name.lower() in cls.DIRECTORY_NAMES:
                paths.append(item)

        locales = next((item for item in root.iterdir() if item.is_dir() and item.name.lower() == "locales"), None) if root.is_dir() else None
        if locales:
            paths.extend(item for item in locales.iterdir() if item.is_file() and item.suffix.lower() in {".info", ".pak"})
        return paths

    @classmethod
    def scan_nwjs_files(cls, root: Path) -> dict[str, int | list[Path]]:
        """Resume los componentes NW.js eliminables encontrados en ``root``."""
        root = Path(root).resolve()
        paths = cls._nwjs_paths(root)
        return {
            "files": paths,
            "count": len(paths),
            "size": sum(path.stat().st_size for path in paths if path.is_file()),
        }

    @classmethod
    def is_redundant_path(cls, path: Path, root: Path) -> bool:
        """Indica si ``path`` es uno de los componentes eliminables del juego."""
        try:
            return Path(path).resolve() in {item.resolve() for item in cls._nwjs_paths(Path(root).resolve())}
        except OSError:
            return False

    @classmethod
    def clean_nwjs(cls, root: Path) -> tuple[int, int]:
        """Elimina componentes redundantes y devuelve ``(elementos, bytes)`` eliminados."""
        removed_count = 0
        removed_size = 0
        for path in cls._nwjs_paths(Path(root).resolve()):
            try:
                if path.is_dir():
                    size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
                    shutil.rmtree(path)
                else:
                    size = path.stat().st_size
                    path.unlink()
                removed_count += 1
                removed_size += size
            except (OSError, PermissionError):
                continue
        return removed_count, removed_size

    @classmethod
    def _package_path(cls, root: Path) -> Path | None:
        for candidate in (root / "package.json", root / "www" / "package.json"):
            if candidate.is_file():
                return candidate
        return None

    @classmethod
    def patch_package_json(cls, root: Path) -> bool:
        """Unifica el perfil NW.js y centra la ventana del juego."""
        package_path = cls._package_path(Path(root).resolve())
        if package_path is None:
            return False
        try:
            data = json.loads(package_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return False
            data["name"] = "RPGM"
            window = dict(data.get("window", {}))
            window["position"] = "center"
            data["window"] = window
            package_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return True
        except (OSError, json.JSONDecodeError, UnicodeError):
            return False

    @classmethod
    def copy_launcher(cls, dest: Path, src_launcher: Path) -> bool:
        """Copia el lanzador global al directorio final del juego."""
        try:
            dest = Path(dest)
            src_launcher = Path(src_launcher)
            if not src_launcher.is_file():
                return False
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_launcher, dest / src_launcher.name)
            return True
        except (OSError, PermissionError):
            return False
