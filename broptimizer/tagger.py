"""Sistema de marcado y lectura de metadata ('BROptimized') para imágenes, audios y videos."""

from pathlib import Path
from PIL import Image, PngImagePlugin


TAG_KEY = "BROptimized"
TAG_VALUE = "1"
TAG_BYTES = b"BROptimized"


class MetadataTagger:
    """Gestiona la lectura y escritura de la marca de optimización en los archivos multimedia."""

    @classmethod
    def is_tagged(cls, file_path: str | Path) -> bool:
        """
        Comprueba si un archivo ya contiene la marca 'BROptimized'.
        Combina un escaneo ultra-rápido de cabecera/cola en binario con validación profunda.
        """
        path = Path(file_path)
        if not path.is_file():
            return False

        try:
            file_size = path.stat().st_size
            if file_size == 0:
                return False

            # Lectura rápida de cabecera (primeros 64 KB) y cola (últimos 64 KB)
            read_len = min(65536, file_size)
            with open(path, "rb") as f:
                header = f.read(read_len)
                if TAG_BYTES in header or b"BROPTIMIZED" in header:
                    return True

                if file_size > read_len:
                    f.seek(-read_len, 2)
                    footer = f.read(read_len)
                    if TAG_BYTES in footer or b"BROPTIMIZED" in footer:
                        return True
        except Exception:
            pass

        return False

    @classmethod
    def get_ffmpeg_metadata_args(cls) -> list[str]:
        """Retorna los argumentos de línea de comandos para incrustar metadata con FFmpeg."""
        return [
            "-metadata", f"{TAG_KEY}={TAG_VALUE}",
            "-metadata", f"comment={TAG_KEY}",
            "-metadata", f"description={TAG_KEY}",
        ]

    @classmethod
    def attach_image_metadata(cls, img: Image.Image, output_format: str, save_kwargs: dict[str, int | bool], temp_output_path: Path) -> None:
        """
        Incrusta la metadata 'BROptimized' en los argumentos de guardado de Pillow.
        Retorna el diccionario save_kwargs actualizado.
        """
        fmt = output_format.upper()
        # save_kwargs = dict(save_kwargs)
        new_save_kwargs: dict[str, int | bool | PngImagePlugin.PngInfo | Image.Exif | bytes] = {**save_kwargs}

        if fmt == "PNG":
            # png_info = save_kwargs.get("pnginfo") or PngImagePlugin.PngInfo()
            png_info = PngImagePlugin.PngInfo()
            png_info.add_text(TAG_KEY, TAG_VALUE)
            png_info.add_text("Comment", TAG_KEY)
            new_save_kwargs["pnginfo"] = png_info

        elif fmt in ("JPEG", "JPG"):
            # En JPEG usamos EXIF UserComment y descripción
            try:
                exif = img.getexif()
                exif[0x9286] = TAG_KEY  # UserComment
                exif[0x010E] = TAG_KEY  # ImageDescription
                new_save_kwargs["exif"] = exif
            except Exception:
                new_save_kwargs["comment"] = TAG_BYTES

        elif fmt == "WEBP":
            try:
                exif = img.getexif()
                exif[0x9286] = TAG_KEY
                exif[0x010E] = TAG_KEY
                new_save_kwargs["exif"] = exif
            except Exception:
                pass
        img.save(temp_output_path, format=fmt, **new_save_kwargs)
        # return save_kwargs
