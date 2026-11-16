"""Pruebas unitarias para la GUI modular por motor y preferencias divididas."""

import sys
import unittest
from PySide6.QtWidgets import QApplication

from broptimizer.gui.main_window import MainWindow
from broptimizer.gui.views.engines.rpgmaker_view import RPGMakerModernView
from broptimizer.gui.views.engines.renpy_view import RenPyView


class TestModularGUI(unittest.TestCase):
    """Verifica la jerarquía BaseEngineQueueView, sidebar colapsable y vistas de preferencias."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_main_window_views_count(self):
        win = MainWindow()
        # 5 vistas de motor + 1 logs + 4 sub-preferencias = 10 vistas
        self.assertEqual(win.stack.count(), 10)

    def test_sidebar_toggle_preferences(self):
        win = MainWindow()
        win.show()
        self.assertFalse(win.sidebar.prefs_frame.isVisible())
        
        # Al hacer toggle programático se expande
        win.sidebar._toggle_preferences()
        self.assertTrue(win.sidebar.prefs_frame.isVisible())

        # Al volver a hacer toggle se contrae
        win.sidebar._toggle_preferences()
        self.assertFalse(win.sidebar.prefs_frame.isVisible())
        win.close()

    def test_engine_specific_options(self):
        rpg_view = RPGMakerModernView()
        opts = rpg_view.get_engine_specific_options()
        self.assertIn("apply_nwjs_clean", opts)
        self.assertIn("decrypt", opts)
        self.assertIn("overwrite_smaller", opts)

        renpy_view = RenPyView()
        renpy_opts = renpy_view.get_engine_specific_options()
        self.assertNotIn("apply_nwjs_clean", renpy_opts)
        self.assertIn("decrypt", renpy_opts)

    def test_config_load_from_settings_defaults(self):
        from broptimizer.config import Config
        cfg = Config.load_from_settings({})
        self.assertEqual(cfg.video_codec, "h264")
        self.assertEqual(cfg.crf, 26)

    def test_config_load_from_settings_custom(self):
        from broptimizer.config import Config
        custom = {"video_codec": "vp9", "crf": 15, "desired_res": 720}
        cfg = Config.load_from_settings(custom)
        self.assertEqual(cfg.video_codec, "vp9")
        self.assertEqual(cfg.crf, 15)
        self.assertEqual(cfg.desired_res, 720)


    def test_activity_logger_format(self):
        import tempfile
        from pathlib import Path
        from broptimizer.logger import ActivityLogger

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_log = Path(tmp_dir) / "test_activity.log"
            ActivityLogger.set_log_file(test_log)
            ActivityLogger.log_item("actor1.png", 100000, 40000, "GUARDADO")
            ActivityLogger.log_item("bgm.ogg", 20000, 20000, "SALTADO")

            content = test_log.read_text(encoding="utf-8")
            self.assertIn("[actor1.png]", content)
            self.assertIn("GUARDADO", content)
            self.assertIn("SALTADO", content)


if __name__ == "__main__":
    unittest.main()
