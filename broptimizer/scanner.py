"""Escaneo recursivo, categorización y estadísticas de archivos multimedia en directorios."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from broptimizer.tagger import MetadataTagger
from broptimizer.rpgmaker_cleaner import RPGMMVCleaner


class MediaType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tga"}
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".opus", ".wav", ".flac", ".m4a", ".aac", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".ogv"}

# Extensiones de archivos encriptados o empaquetados de motores de videojuegos
ENCRYPTED_PACKED_EXTENSIONS = {
    # RPG Maker MV/MZ encriptados
    ".rpgmvp", ".rpgmvm", ".rpgmvo",
    ".png_", ".ogg_", ".m4a_",
    # RPG Maker RGSS empaquetados
    ".rgssad", ".rgss2a", ".rgss3a",
    # Ren'Py empaquetados
    ".rpa",
    # Wolf RPG empaquetados
    ".wolf",
}


def format_bytes(size: int | float) -> str:
    """Convierte un tamaño en bytes a formato legible (B, KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


@dataclass
class FileInfo:
    """Información de un archivo individual escaneado."""
    path: Path
    rel_path: Path
    size: int
    media_type: MediaType
    extension: str
    is_tagged: bool = False
    is_encrypted_or_packed: bool = False


@dataclass
class CategoryStats:
    """Estadísticas acumuladas de una categoría de archivos."""
    media_type: MediaType
    file_count: int = 0
    total_size: int = 0
    tagged_count: int = 0
    extensions_count: dict[str, int] = field(default_factory=dict)
    extensions_size: dict[str, int] = field(default_factory=dict)

    def add(self, info: FileInfo) -> None:
        self.file_count += 1
        self.total_size += info.size
        if info.is_tagged:
            self.tagged_count += 1
        ext = info.extension.lower()
        self.extensions_count[ext] = self.extensions_count.get(ext, 0) + 1
        self.extensions_size[ext] = self.extensions_size.get(ext, 0) + info.size

    @property
    def formatted_size(self) -> str:
        return format_bytes(self.total_size)


@dataclass
class MediaStats:
    """Resumen completo de estadísticas de una carpeta."""
    root_path: Path
    total_files: int = 0
    total_size: int = 0
    images: CategoryStats = field(default_factory=lambda: CategoryStats(MediaType.IMAGE))
    audios: CategoryStats = field(default_factory=lambda: CategoryStats(MediaType.AUDIO))
    videos: CategoryStats = field(default_factory=lambda: CategoryStats(MediaType.VIDEO))
    others: CategoryStats = field(default_factory=lambda: CategoryStats(MediaType.OTHER))
    files: list[FileInfo] = field(default_factory=list)
    
    # Detección de paquetes y assets encriptados
    encrypted_packed_files: list[FileInfo] = field(default_factory=list)
    encrypted_packed_count: int = 0
    encrypted_packed_size: int = 0
    nwjs_files: list[Path] = field(default_factory=list)
    nwjs_count: int = 0
    nwjs_size: int = 0

    @property
    def total_media_count(self) -> int:
        return self.images.file_count + self.audios.file_count + self.videos.file_count

    @property
    def total_media_size(self) -> int:
        return self.images.total_size + self.audios.total_size + self.videos.total_size

    @property
    def total_tagged_count(self) -> int:
        return self.images.tagged_count + self.audios.tagged_count + self.videos.tagged_count

    @property
    def formatted_total_size(self) -> str:
        return format_bytes(self.total_size)

    @property
    def formatted_media_size(self) -> str:
        return format_bytes(self.total_media_size)

    @property
    def formatted_encrypted_packed_size(self) -> str:
        return format_bytes(self.encrypted_packed_size)

    @property
    def formatted_nwjs_size(self) -> str:
        return format_bytes(self.nwjs_size)


class FolderScanner:
    """Escanea y clasifica todos los archivos de un directorio recursivamente."""

    @classmethod
    def classify_extension(cls, ext: str) -> MediaType:
        ext = ext.lower()
        if ext in IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        if ext in AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        if ext in VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        return MediaType.OTHER

    @classmethod
    def scan(cls, folder_path: str | Path, check_tags: bool = True, detect_nwjs: bool = False) -> MediaStats:
        root = Path(folder_path).resolve()
        stats = MediaStats(root_path=root)

        if not root.is_dir():
            return stats

        for item in root.rglob("*"):
            if not item.is_file():
                continue

            try:
                size = item.stat().st_size
            except (OSError, PermissionError):
                continue

            stats.total_files += 1
            stats.total_size += size

            ext = item.suffix.lower()
            media_type = cls.classify_extension(ext)
            rel_path = item.relative_to(root)

            is_tagged = False
            if check_tags and media_type != MediaType.OTHER:
                is_tagged = MetadataTagger.is_tagged(item)

            # Verificar si es un asset empaquetado o encriptado
            is_enc_packed = (ext in ENCRYPTED_PACKED_EXTENSIONS) or (item.name.lower() == "data.wolf")

            info = FileInfo(
                path=item,
                rel_path=rel_path,
                size=size,
                media_type=media_type,
                extension=ext,
                is_tagged=is_tagged,
                is_encrypted_or_packed=is_enc_packed,
            )
            stats.files.append(info)

            if is_enc_packed:
                stats.encrypted_packed_files.append(info)
                stats.encrypted_packed_count += 1
                stats.encrypted_packed_size += size

            if media_type == MediaType.IMAGE:
                stats.images.add(info)
            elif media_type == MediaType.AUDIO:
                stats.audios.add(info)
            elif media_type == MediaType.VIDEO:
                stats.videos.add(info)
            else:
                stats.others.add(info)

        if detect_nwjs:
            nwjs_summary = RPGMMVCleaner.scan_nwjs_files(root)
            stats.nwjs_files = nwjs_summary["files"]
            stats.nwjs_count = nwjs_summary["count"]
            stats.nwjs_size = nwjs_summary["size"]

        return stats
