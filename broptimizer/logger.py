"""Sistema de registro de errores y excepciones en archivo de texto, y log de actividad de optimización."""

from datetime import datetime
from pathlib import Path
import threading
import traceback

from broptimizer import PROJECT_ROOT


LOG_FILENAME = "broptimizer_errors.log"
ACTIVITY_LOG_FILENAME = "broptimizer_activity.log"

LOG_FILE_PATH = PROJECT_ROOT / LOG_FILENAME
ACTIVITY_LOG_FILE_PATH = PROJECT_ROOT / ACTIVITY_LOG_FILENAME


class ErrorLogger:
    """Registra errores detallados con timestamp, bloque de código y traza completa."""

    log_path: Path = LOG_FILE_PATH

    @classmethod
    def set_log_file(cls, path: str | Path) -> None:
        cls.log_path = Path(path).resolve()

    @classmethod
    def log_error(
        cls,
        code_block: str,
        file_path: str | Path | None = None,
        error_msg: str | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Escribe una entrada estructurada en el archivo de log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_file_str = str(file_path) if file_path else "N/A"
        exc_type = type(exception).__name__ if exception else "Error / Fallo de Transcodificación"

        details = []
        if error_msg:
            details.append(error_msg.strip())
        if exception:
            details.append("".join(traceback.format_exception(None, exception, exception.__traceback__)).strip())

        full_details = "\n".join(details) if details else "Sin información adicional del error."

        entry = (
            f"{'=' * 80}\n"
            f"[FECHA Y HORA]: {timestamp}\n"
            f"[BLOQUE / MÓDULO]: {code_block}\n"
            f"[ARCHIVO AFECTADO]: {target_file_str}\n"
            f"[TIPO DE ERROR]: {exc_type}\n"
            f"[DETALLE DEL ERROR]:\n{full_details}\n"
            f"{'=' * 80}\n\n"
        )

        try:
            with open(cls.log_path, "a", encoding="utf-8") as f:
                f.write(entry)
                f.flush()
        except Exception as e:
            print(f"[Error interno al escribir en {cls.log_path}]: {e}")


class ActivityLogger:
    """Registra en tiempo real cada archivo procesado de forma thread-safe."""

    log_path: Path = ACTIVITY_LOG_FILE_PATH
    _lock = threading.Lock()

    @classmethod
    def set_log_file(cls, path: str | Path) -> None:
        with cls._lock:
            cls.log_path = Path(path).resolve()

    @classmethod
    def format_size(cls, size_bytes: int | float) -> str:
        """Formatea bytes a KB o MB según corresponda."""
        if size_bytes <= 0:
            return "0.0 KB"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024.0:.1f} KB"
        return f"{size_bytes / (1024.0 * 1024.0):.2f} MB"

    @classmethod
    def log_item(
        cls,
        filename: str,
        orig_bytes: int,
        opt_bytes: int,
        status: str,
        extra: str = "",
    ) -> None:
        """
        Escribe una línea en broptimizer_activity.log con el formato:
        [archivo.ext] [peso original] -> [peso optimizado] (porcentaje) : [ESTADO]
        """
        orig_str = cls.format_size(orig_bytes)
        opt_str = cls.format_size(opt_bytes)

        if orig_bytes > 0 and opt_bytes < orig_bytes:
            saving_pct = ((orig_bytes - opt_bytes) / orig_bytes) * 100.0
            pct_str = f" (-{saving_pct:.1f}%)"
        else:
            pct_str = ""

        extra_str = f" ({extra})" if extra else ""
        line = f"[{filename}] {orig_str} -> {opt_str}{pct_str} : {status}{extra_str}\n"

        with cls._lock:
            try:
                with open(cls.log_path, "a", encoding="utf-8") as f:
                    f.write(line)
                    f.flush()
            except Exception as e:
                print(f"[Error interno al escribir en {cls.log_path}]: {e}")

    @classmethod
    def log_message(cls, message: str) -> None:
        """Escribe un mensaje de encabezado, separación o evento especial."""
        with cls._lock:
            try:
                with open(cls.log_path, "a", encoding="utf-8") as f:
                    f.write(f"{message}\n")
                    f.flush()
            except Exception as e:
                print(f"[Error interno al escribir en {cls.log_path}]: {e}")

    @classmethod
    def clear(cls) -> None:
        """Limpia el archivo de log de actividad."""
        with cls._lock:
            try:
                cls.log_path.write_text("", encoding="utf-8")
            except Exception:
                pass

