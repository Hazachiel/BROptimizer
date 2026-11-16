"""Optimizador de imágenes con detección de transparencia y preservación de extensión."""

from pathlib import Path
import uuid
from PIL import Image

from broptimizer.config import Config
from broptimizer.engines.base import EngineProfile
from broptimizer.logger import ErrorLogger
from broptimizer.media.base import BaseMediaOptimizer, OptimizationResult
from broptimizer.tagger import MetadataTagger


class ImageOptimizer(BaseMediaOptimizer):
    """Optimiza imágenes (PNG, JPG, WebP) utilizando Pillow de alto rendimiento."""

    @classmethod
    def check_transparency(cls, img: Image.Image) -> bool:
        """Determina con precisión si una imagen contiene píxeles transparentes o semitransparentes."""
        if img.mode in ("RGBA", "LA"):
            alpha = img.getchannel("A")
            min_val, _ = alpha.getextrema()
            if type(min_val) == float:
                return min_val < 255

        if img.mode == "P":
            trans = img.info.get("transparency")
            if trans is not None:
                try:
                    rgba = img.convert("RGBA")
                    min_val, _ = rgba.getchannel("A").getextrema()
                    if type(min_val) == float:
                        return min_val < 255
                except Exception:
                    return True

        return False

    def optimize(
        self,
        input_path: Path,
        temp_dir: Path,
        config: Config,
        profile: EngineProfile,
    ) -> OptimizationResult:
        orig_size = input_path.stat().st_size
        orig_ext = input_path.suffix.lower()

        try:
            with Image.open(input_path) as img:
                img.load()

                has_alpha = self.check_transparency(img)
                target_format = profile.get_target_image_format(orig_ext, has_alpha)

                if config.preserve_extension:
                    final_ext = orig_ext
                else:
                    if target_format == "webp":
                        final_ext = ".webp"
                    elif target_format == "jpeg":
                        final_ext = ".jpg"
                    else:
                        final_ext = ".png"

                unique_id = uuid.uuid4().hex[:8]
                temp_filename = f"{input_path.stem}_{unique_id}{final_ext}"
                temp_output_path = temp_dir / temp_filename

                save_kwargs: dict[str, int | bool] = {}
                pillow_format = target_format.upper()
                if pillow_format == "JPG":
                    pillow_format = "JPEG"

                if pillow_format == "WEBP":
                    save_kwargs = {
                        "quality": config.settings.webp_quality,
                        "method": config.settings.webp_method,
                        "lossless": False,
                        "alpha_quality": 85 if config.preset == "lossy" else 100,
                    }
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA" if has_alpha else "RGB")

                elif pillow_format == "JPEG":
                    save_kwargs = {
                        "quality": config.settings.jpeg_quality,
                        "optimize": True,
                        "progressive": True,
                        "subsampling": 2,
                    }
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                elif pillow_format == "PNG":
                    save_kwargs = {
                        "optimize": True,
                        "compress_level": config.settings.png_compression_level,
                    }

                if config.tag_metadata:
                    # save_kwargs = MetadataTagger.attach_image_metadata(img, pillow_format, save_kwargs, temp_output_path) # type: ignore
                    MetadataTagger.attach_image_metadata(img, pillow_format, save_kwargs, temp_output_path)
                else:
                    img.save(temp_output_path, format=pillow_format, **save_kwargs)

            new_size = temp_output_path.stat().st_size
            is_smaller = new_size < orig_size

            if not is_smaller:
                temp_output_path.unlink(missing_ok=True)
                return OptimizationResult(
                    input_path=input_path,
                    temp_output_path=None,
                    original_size=orig_size,
                    optimized_size=orig_size,
                    success=True,
                    is_smaller=False,
                    target_extension=final_ext,
                )

            return OptimizationResult(
                input_path=input_path,
                temp_output_path=temp_output_path,
                original_size=orig_size,
                optimized_size=new_size,
                success=True,
                is_smaller=True,
                target_extension=final_ext,
            )

        except Exception as e:
            ErrorLogger.log_error(
                code_block="ImageOptimizer.optimize",
                file_path=input_path,
                exception=e,
            )
            return OptimizationResult(
                input_path=input_path,
                temp_output_path=None,
                original_size=orig_size,
                optimized_size=orig_size,
                success=False,
                is_smaller=False,
                target_extension=orig_ext,
                error_message=str(e),
            )
