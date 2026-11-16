"""Detector automático de motores de videojuegos a partir de la estructura de archivos."""

from pathlib import Path

from broptimizer.engines.base import EngineProfile
from broptimizer.engines.generic import GenericProfile
from broptimizer.engines.renpy import RenpyProfile
from broptimizer.engines.rpgmaker import RpgMakerLegacyProfile, RpgMakerMzProfile
from broptimizer.engines.wolfrpg import WolfRpgProfile


class EngineDetector:
    """Inspecciona una carpeta y determina si pertenece a un motor de juego conocido."""

    @classmethod
    def detect(cls, root_dir: str | Path) -> EngineProfile:
        path = Path(root_dir)
        if not path.is_dir():
            return GenericProfile()

        # 1. Detectar Ren'Py
        if cls._is_renpy(path):
            return RenpyProfile()

        # 2. Detectar RPG Maker Moderno (MZ / MV)
        if cls._is_rpgmaker_modern(path):
            return RpgMakerMzProfile()

        # 3. Detectar RPG Maker Heredado (XP / VX / VX Ace)
        if cls._is_rpgmaker_legacy(path):
            return RpgMakerLegacyProfile()

        # 4. Detectar Wolf RPG Editor
        if cls._is_wolfrpg(path):
            return WolfRpgProfile()

        # Motor genérico por defecto
        return GenericProfile()

    @classmethod
    def _is_renpy(cls, path: Path) -> bool:
        """Verifica marcadores característicos de Ren'Py."""
        # Carpeta renpy/ o archivo renpy.py
        if (path / "renpy").is_dir() or (path / "renpy.py").is_file():
            return True

        # Carpeta game/ con archivos de script o paquetes
        game_dir = path / "game"
        if game_dir.is_dir():
            indicators = ["options.rpy", "options.rpyc", "script.rpy", "script.rpyc", "gui.rpy"]
            for ind in indicators:
                if (game_dir / ind).is_file():
                    return True
            # Búsqueda superficial de .rpyc o .rpa en game/
            if any(game_dir.glob("*.rpa")) or any(game_dir.glob("*.rpyc")) or any(game_dir.glob("*.rpy")):
                return True

        return False

    @classmethod
    def _is_rpgmaker_modern(cls, path: Path) -> bool:
        """Verifica marcadores de RPG Maker MZ o MV (HTML5 / NW.js)."""
        # A veces los archivos están en la raíz o en una subcarpeta www/
        check_roots = [path, path / "www"]

        for r in check_roots:
            if not r.is_dir():
                continue

            # Scripts principales
            if (r / "js" / "rmmz_core.js").is_file() or (r / "js" / "rpg_core.js").is_file():
                return True

            # Archivo de datos de sistema característico
            if (r / "data" / "System.json").is_file() and (r / "img").is_dir():
                return True

            # package.json con referencias a rpg maker
            pkg_file = r / "package.json"
            if pkg_file.is_file():
                try:
                    content = pkg_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if "rpgmakermv" in content or "rmmz" in content or "rpg maker" in content:
                        return True
                except Exception:
                    pass

        return False

    @classmethod
    def _is_rpgmaker_legacy(cls, path: Path) -> bool:
        """Verifica marcadores de RPG Maker XP, VX o VX Ace."""
        # Archivos de proyecto
        legacy_projects = ["Game.rxproj", "Game.rvproj", "Game.rvproj2"]
        for lp in legacy_projects:
            if (path / lp).is_file():
                return True

        # DLLs de motor RGSS
        rgss_dlls = ["rgss100j.dll", "rgss102e.dll", "rgss103j.dll", "rgss200j.dll", "rgss202e.dll", "rgss301.dll"]
        for item in path.glob("*.dll"):
            if item.name.lower() in rgss_dlls:
                return True

        # Carpeta Data/ con archivos .rxdata o .rvdata
        data_dir = path / "Data"
        if data_dir.is_dir():
            if (data_dir / "System.rxdata").is_file() or (data_dir / "System.rvdata").is_file() or (data_dir / "System.rvdata2").is_file():
                return True

        return False

    @classmethod
    def _is_wolfrpg(cls, path: Path) -> bool:
        """Verifica marcadores de Wolf RPG Editor."""
        # Archivo de datos básico
        if (path / "Data" / "BasicData" / "SysDatabase.project").is_file():
            return True
        if (path / "Data.wolf").is_file():
            return True

        # Carpeta Data con carpetas típicas de Wolf RPG (BasicData, Graphic, Sound, MapData)
        data_dir = path / "Data"
        if data_dir.is_dir():
            if (data_dir / "BasicData").is_dir() and ((data_dir / "Graphic").is_dir() or (data_dir / "Sound").is_dir()):
                return True

        return False
