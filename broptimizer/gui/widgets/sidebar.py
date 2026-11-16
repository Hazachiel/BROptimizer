"""Barra lateral (Sidebar) con secciones y submenú colapsable para Preferencias."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QButtonGroup
)


class Sidebar(QWidget):
    """Barra lateral estructurada por categorías con menú de preferencias colapsable."""

    view_requested = Signal(str)  # Emite el ID de la vista deseada

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._buttons_by_id: dict[str, QPushButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(4)

        # 1. Sección Motores de Juegos
        lbl_engines = QLabel("Motores de Juegos")
        lbl_engines.setProperty("class", "SidebarSectionLabel")
        layout.addWidget(lbl_engines)

        engines = [
            ("⚡ RPG Maker (MV / MZ)", "engine_rpgmaker"),
            ("🗡️ RPG Maker (Legacy)", "engine_legacy_rpg"),
            ("📖 Ren'Py", "engine_renpy"),
            ("🐺 Wolf RPG", "engine_wolfrpg"),
        ]
        for text, vid in engines:
            self._add_nav_button(layout, text, vid)

        # 2. Sección General
        lbl_general = QLabel("General")
        lbl_general.setProperty("class", "SidebarSectionLabel")
        layout.addWidget(lbl_general)

        self._add_nav_button(layout, "📂 Multimedia Genérico", "engine_generic")

        # 3. Sección Herramientas
        lbl_tools = QLabel("Herramientas")
        lbl_tools.setProperty("class", "SidebarSectionLabel")
        layout.addWidget(lbl_tools)

        self._add_nav_button(layout, "📋 Historial y Logs", "logs")

        # 4. Sección Preferencias (Colapsable con QFrame anidado)
        lbl_prefs = QLabel("Configuración")
        lbl_prefs.setProperty("class", "SidebarSectionLabel")
        layout.addWidget(lbl_prefs)

        self.btn_prefs_toggle = QPushButton("⚙️ Preferencias  ▼")
        self.btn_prefs_toggle.setCheckable(False)
        self.btn_prefs_toggle.clicked.connect(self._toggle_preferences)
        layout.addWidget(self.btn_prefs_toggle)

        # QFrame colapsable para sub-opciones
        self.prefs_frame = QFrame()
        self.prefs_frame.setObjectName("PrefsSubmenu")
        prefs_layout = QVBoxLayout(self.prefs_frame)
        prefs_layout.setContentsMargins(4, 4, 4, 4)
        prefs_layout.setSpacing(2)

        pref_subitems = [
            ("💻 Sistema", "pref_system"),
            ("🖼️ Imágenes", "pref_image"),
            ("🎵 Audio", "pref_audio"),
            ("🎬 Video", "pref_video"),
        ]
        for text, vid in pref_subitems:
            btn = QPushButton(text)
            btn.setCheckable(True)
            self._button_group.addButton(btn)
            self._buttons_by_id[vid] = btn
            btn.clicked.connect(lambda _, target=vid: self.view_requested.emit(target))
            prefs_layout.addWidget(btn)

        layout.addWidget(self.prefs_frame)
        self.prefs_frame.setVisible(False)  # Inicia contraído

        layout.addStretch()

        # Seleccionar por defecto la primera vista
        if "engine_rpgmaker" in self._buttons_by_id:
            self._buttons_by_id["engine_rpgmaker"].setChecked(True)

    def _add_nav_button(self, layout: QVBoxLayout, text: str, view_id: str) -> None:
        btn = QPushButton(text)
        btn.setCheckable(True)
        self._button_group.addButton(btn)
        self._buttons_by_id[view_id] = btn
        btn.clicked.connect(lambda: self.view_requested.emit(view_id))
        layout.addWidget(btn)

    def _toggle_preferences(self) -> None:
        """Expande o contrae el contenedor de sub-preferencias."""
        is_visible = not self.prefs_frame.isVisible()
        self.prefs_frame.setVisible(is_visible)
        if is_visible:
            self.btn_prefs_toggle.setText("⚙️ Preferencias  ▲")
            # Si no hay ninguna sub-opción seleccionada, seleccionar sistema por defecto
            if "pref_system" in self._buttons_by_id and not any(
                self._buttons_by_id[vid].isChecked() for vid in ["pref_system", "pref_image", "pref_audio", "pref_video"]
            ):
                self.select_view("pref_system")
                self.view_requested.emit("pref_system")
        else:
            self.btn_prefs_toggle.setText("⚙️ Preferencias  ▼")

    def select_view(self, view_id: str) -> None:
        """Activa visualmente el botón correspondiente a view_id en el Sidebar."""
        btn = self._buttons_by_id.get(view_id)
        if btn:
            btn.setChecked(True)
            # Si es un sub-ítem de preferencias, asegurar que el frame esté visible
            if view_id.startswith("pref_") and not self.prefs_frame.isVisible():
                self.prefs_frame.setVisible(True)
                self.btn_prefs_toggle.setText("⚙️ Preferencias  ▲")
