"""Ventana principal de BROptimizer con navegación por Sidebar y vistas dedicadas."""

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QMessageBox
)

from broptimizer.gui.theme import DARK_THEME_QSS
from broptimizer.gui.widgets.banner import HeaderBanner
from broptimizer.gui.widgets.sidebar import Sidebar
from broptimizer.gui.views.logs_view import LogsView

# Vistas de motor
from broptimizer.gui.views.engines.rpgmaker_view import RPGMakerModernView
from broptimizer.gui.views.engines.legacy_rpg_view import RPGMakerLegacyView
from broptimizer.gui.views.engines.renpy_view import RenPyView
from broptimizer.gui.views.engines.wolfrpg_view import WolfRPGView
from broptimizer.gui.views.engines.generic_view import GenericView

# Sub-vistas de preferencias
from broptimizer.gui.views.preferences.pref_system import SystemPreferencesView
from broptimizer.gui.views.preferences.pref_image import ImagePreferencesView
from broptimizer.gui.views.preferences.pref_audio import AudioPreferencesView
from broptimizer.gui.views.preferences.pref_video import VideoPreferencesView


class MainWindow(QMainWindow):
    """Ventana principal modular de BROptimizer."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BROptimizer - Optimizador Multimedia para Juegos Indie")
        self.resize(1100, 740)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_THEME_QSS)

        self._views_by_id: dict[str, QWidget] = {}
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Header Banner superior
        self.banner = HeaderBanner()
        root_layout.addWidget(self.banner)

        # 2. Contenedor horizontal: Sidebar a la izquierda + Vistas apiladas a la derecha
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()

        # Instanciar y registrar vistas
        self.view_rpgmaker = RPGMakerModernView()
        self.view_legacy = RPGMakerLegacyView()
        self.view_renpy = RenPyView()
        self.view_wolfrpg = WolfRPGView()
        self.view_generic = GenericView()
        self.view_logs = LogsView()

        self.view_pref_sys = SystemPreferencesView()
        self.view_pref_img = ImagePreferencesView()
        self.view_pref_aud = AudioPreferencesView()
        self.view_pref_vid = VideoPreferencesView()

        views_list = [
            ("engine_rpgmaker", self.view_rpgmaker),
            ("engine_legacy_rpg", self.view_legacy),
            ("engine_renpy", self.view_renpy),
            ("engine_wolfrpg", self.view_wolfrpg),
            ("engine_generic", self.view_generic),
            ("logs", self.view_logs),
            ("pref_system", self.view_pref_sys),
            ("pref_image", self.view_pref_img),
            ("pref_audio", self.view_pref_aud),
            ("pref_video", self.view_pref_vid),
        ]

        for vid, widget in views_list:
            self._views_by_id[vid] = widget
            self.stack.addWidget(widget)

        body_layout.addWidget(self.stack, stretch=1)
        root_layout.addLayout(body_layout, stretch=1)

    def _connect_signals(self) -> None:
        self.sidebar.view_requested.connect(self.switch_to_view)

        # Redirección inteligente ante arrastre de carpeta discordante
        for engine_view in [self.view_rpgmaker, self.view_legacy, self.view_renpy, self.view_wolfrpg, self.view_generic]:
            engine_view.folder_dropped_mismatch.connect(self._on_folder_mismatch)

    def switch_to_view(self, view_id: str) -> None:
        """Cambia la vista visible en el QStackedWidget y sincroniza el Sidebar."""
        widget = self._views_by_id.get(view_id)
        if widget:
            self.stack.setCurrentWidget(widget)
            self.sidebar.select_view(view_id)
            if view_id == "logs":
                self.view_logs.reload_logs()
            elif view_id == "pref_system":
                self.view_pref_sys.check_binaries()

    def _on_folder_mismatch(self, folder_path: str, target_view_id: str) -> None:
        """Redirige automáticamente la carpeta a la pestaña correspondiente del motor detectado."""
        target_widget = self._views_by_id.get(target_view_id)
        if target_widget and hasattr(target_widget, "_insert_row"):
            self.switch_to_view(target_view_id)
            target_widget._insert_row(Path(folder_path))
            
            pname = Path(folder_path).name
            tname = getattr(target_widget, "view_title", target_view_id)
            self.statusBar().showMessage(f"Carpeta '{pname}' redirigida automáticamente a la vista {tname}", 5000)
