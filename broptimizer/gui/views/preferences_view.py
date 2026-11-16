"""Vista de Preferencias y Configuración Avanzada."""

import json
import os
from pathlib import Path
import shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QFileDialog, QCheckBox, QSpinBox, QMessageBox, QScrollArea
)


class PreferencesView(QWidget):
    """Panel de configuración avanzada, diagnóstico de binarios y persistencia."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.config_file = Path("broptimizer_settings.json")
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Diagnóstico del Sistema y Binarios
        diag_group = QGroupBox("🛠️ Diagnóstico del Sistema y Binarios")
        diag_layout = QVBoxLayout(diag_group)
        diag_layout.setSpacing(8)

        self.lbl_ffmpeg = QLabel("FFmpeg: Verificando...")
        self.lbl_ffprobe = QLabel("FFprobe: Verificando...")
        self.lbl_nwjs = QLabel("NW.js Portable: Verificando...")

        diag_layout.addWidget(self.lbl_ffmpeg)
        diag_layout.addWidget(self.lbl_ffprobe)
        diag_layout.addWidget(self.lbl_nwjs)

        btn_recheck = QPushButton("🔄 Volver a verificar binarios")
        btn_recheck.clicked.connect(self.check_binaries)
        diag_layout.addWidget(btn_recheck)
        layout.addWidget(diag_group)

        # 2. Configuración de Motores y NW.js
        nw_group = QGroupBox("🎮 Configuración de RPG Maker y NW.js")
        nw_layout = QVBoxLayout(nw_group)
        nw_layout.setSpacing(8)

        nw_path_layout = QHBoxLayout()
        nw_lbl = QLabel("Ruta a nw.exe (opcional si está en PATH):")
        self.edit_nw_path = QLineEdit()
        self.edit_nw_path.setPlaceholderText("Dejar vacío para usar 'where nw.exe' del sistema...")
        btn_browse_nw = QPushButton("...")
        btn_browse_nw.clicked.connect(self._browse_nw)
        nw_path_layout.addWidget(self.edit_nw_path)
        nw_path_layout.addWidget(btn_browse_nw)

        nw_layout.addWidget(nw_lbl)
        nw_layout.addLayout(nw_path_layout)

        profile_lbl = QLabel("Directorio del perfil de usuario compartido:")
        self.edit_profile_path = QLineEdit()
        self.edit_profile_path.setText(r"%localappdata%\RPGM\User Data")
        nw_layout.addWidget(profile_lbl)
        nw_layout.addWidget(self.edit_profile_path)

        btn_clean_cache = QPushButton("🧹 Vaciar caché compartida de NW.js ahora")
        btn_clean_cache.clicked.connect(self._clean_nwjs_cache)
        nw_layout.addWidget(btn_clean_cache)

        layout.addWidget(nw_group)

        # 3. Ajustes Finos de Optimización
        opt_group = QGroupBox("⚙️ Ajustes Finos de Compresión")
        opt_layout = QVBoxLayout(opt_group)
        opt_layout.setSpacing(8)

        res_layout = QHBoxLayout()
        res_lbl = QLabel("Resolución objetivo de video (lado menor en píxeles):")
        self.spin_desired_res = QSpinBox()
        self.spin_desired_res.setRange(240, 2160)
        self.spin_desired_res.setValue(600)
        self.spin_desired_res.setSingleStep(20)
        res_layout.addWidget(res_lbl)
        res_layout.addWidget(self.spin_desired_res)
        opt_layout.addLayout(res_layout)

        self.chk_tag_metadata = QCheckBox("Inyectar etiqueta de metadatos 'BROptimized' (evita re-procesar en el futuro)")
        self.chk_tag_metadata.setChecked(True)
        opt_layout.addWidget(self.chk_tag_metadata)

        layout.addWidget(opt_group)

        # 4. Botones de acción inferiores
        btn_bar = QHBoxLayout()
        self.btn_reset = QPushButton("Restablecer valores predeterminados")
        self.btn_reset.clicked.connect(self.reset_defaults)
        self.btn_save = QPushButton("💾 Guardar Preferencias")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self.save_settings)

        btn_bar.addWidget(self.btn_reset)
        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_save)
        layout.addLayout(btn_bar)

        layout.addStretch()
        scroll.setWidget(container)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        self.check_binaries()

    def check_binaries(self) -> None:
        """Verifica la presencia de ffmpeg, ffprobe y nw.exe."""
        ffmpeg_path = shutil.which("ffmpeg")
        ffprobe_path = shutil.which("ffprobe")
        nw_path = self.edit_nw_path.text().strip() or shutil.which("nw") or shutil.which("nw.exe")

        if ffmpeg_path:
            self.lbl_ffmpeg.setText(f"FFmpeg: ✔ Encontrado ({ffmpeg_path})")
            self.lbl_ffmpeg.setStyleSheet("color: #4ADE80;")
        else:
            self.lbl_ffmpeg.setText("FFmpeg: ❌ No encontrado en PATH (Requerido para video y audio)")
            self.lbl_ffmpeg.setStyleSheet("color: #F87171;")

        if ffprobe_path:
            self.lbl_ffprobe.setText(f"FFprobe: ✔ Encontrado ({ffprobe_path})")
            self.lbl_ffprobe.setStyleSheet("color: #4ADE80;")
        else:
            self.lbl_ffprobe.setText("FFprobe: ❌ No encontrado en PATH")
            self.lbl_ffprobe.setStyleSheet("color: #F87171;")

        if nw_path and Path(nw_path).exists():
            self.lbl_nwjs.setText(f"NW.js: ✔ Encontrado ({nw_path})")
            self.lbl_nwjs.setStyleSheet("color: #4ADE80;")
        else:
            self.lbl_nwjs.setText("NW.js: ⚠️ No encontrado en PATH ni ruta manual")
            self.lbl_nwjs.setStyleSheet("color: #FBBF24;")

    def _browse_nw(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar nw.exe", "", "Ejecutables (*.exe)")
        if file_path:
            self.edit_nw_path.setText(file_path)
            self.check_binaries()

    def _clean_nwjs_cache(self) -> None:
        expanded_path = Path(os.path.expandvars(self.edit_profile_path.text().strip()))
        if not expanded_path.exists():
            QMessageBox.information(self, "Limpieza de Caché", "No existe un perfil previo de NW.js en la ruta.")
            return

        cache_dirs = [
            expanded_path / "Default" / "Cache",
            expanded_path / "Default" / "Code Cache",
            expanded_path / "Default" / "GPUCache",
            expanded_path / "ShaderCache",
        ]
        cleared = 0
        for cd in cache_dirs:
            if cd.exists():
                try:
                    shutil.rmtree(cd, ignore_errors=True)
                    cleared += 1
                except Exception:
                    pass

        QMessageBox.information(
            self, "Limpieza de Caché",
            f"Se limpiaron {cleared} directorios de caché de NW.js con éxito.\n(Las partidas guardadas se preservaron)."
        )

    def save_settings(self) -> None:
        """Guarda los ajustes en formato JSON."""
        data = {
            "nw_path": self.edit_nw_path.text().strip(),
            "profile_path": self.edit_profile_path.text().strip(),
            "desired_res": self.spin_desired_res.value(),
            "tag_metadata": self.chk_tag_metadata.isChecked(),
        }
        try:
            self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Preferencias", "Preferencias guardadas correctamente.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudieron guardar las preferencias: {exc}")

    def load_settings(self) -> None:
        """Carga los ajustes desde el archivo JSON si existe."""
        if not self.config_file.exists():
            return
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            self.edit_nw_path.setText(data.get("nw_path", ""))
            self.edit_profile_path.setText(data.get("profile_path", r"%localappdata%\RPGM\User Data"))
            self.spin_desired_res.setValue(data.get("desired_res", 600))
            self.chk_tag_metadata.setChecked(data.get("tag_metadata", True))
            self.check_binaries()
        except Exception:
            pass

    def reset_defaults(self) -> None:
        """Restablece los valores por defecto."""
        self.edit_nw_path.clear()
        self.edit_profile_path.setText(r"%localappdata%\RPGM\User Data")
        self.spin_desired_res.setValue(600)
        self.chk_tag_metadata.setChecked(True)
        self.check_binaries()

