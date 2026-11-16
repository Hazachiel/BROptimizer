"""Pruebas para el módulo ErrorLogger y registro de fallos en archivo de texto."""

from pathlib import Path
import tempfile
import unittest

from broptimizer.logger import ErrorLogger


class TestErrorLogger(unittest.TestCase):

    def test_log_error_creates_file_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom_log = Path(tmp) / "test_errors.log"
            ErrorLogger.set_log_file(custom_log)

            test_file = Path(tmp) / "corrupt_video.mp4"

            try:
                raise ValueError("Error simulado de decodificación")
            except Exception as e:
                ErrorLogger.log_error(
                    code_block="TestModule.run_test",
                    file_path=test_file,
                    error_msg="Mensaje adicional explicativo del fallo",
                    exception=e,
                )

            self.assertTrue(custom_log.is_file())
            content = custom_log.read_text(encoding="utf-8")

            self.assertIn("[BLOQUE / MÓDULO]: TestModule.run_test", content)
            self.assertIn("corrupt_video.mp4", content)
            self.assertIn("ValueError", content)
            self.assertIn("Error simulado de decodificación", content)
            self.assertIn("Mensaje adicional explicativo del fallo", content)

    def tearDown(self):
        # Restaurar nombre de archivo estándar
        ErrorLogger.set_log_file("broptimizer_errors.log")


if __name__ == "__main__":
    unittest.main()
