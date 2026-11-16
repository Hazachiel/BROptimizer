"""Preferencias de Sistema: Diagnóstico de binarios, NW.js, Hilos CPU y Carpeta Temporal."""

import os
from pathlib import Path
import shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QFileDialog, QSlider, QRadioButton, QMessageBox, QScrollArea
)

from broptimizer.gui.views.preferences.pref_storage import load_all_settings, save_settings_dict


class SystemPreferencesView(QWidget):
    """Sub-vista de configuración del sistema y rendimiento."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.load_values()

    def _setup_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Diagnóstico de Binarios
        diag_group = QGroupBox("🛠️ Diagnóstico del Sistema y Herramientas Externas")
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

        # 2. Configuración NW.js
        nw_group = QGroupBox("🎮 Configuración de NW.js (RPG Maker MV/MZ)")
        nw_layout = QVBoxLayout(nw_group)
        nw_layout.setSpacing(8)

        nw_box = QHBoxLayout()
        nw_lbl = QLabel("Ruta a nw.exe personalizada (opcional):")
        self.edit_nw_path = QLineEdit()
        self.edit_nw_path.setPlaceholderText("Dejar vacío para usar 'where nw.exe' del sistema...")
        btn_browse_nw = QPushButton("...")
        btn_browse_nw.clicked.connect(self._browse_nw)
        nw_box.addWidget(self.edit_nw_path)
        nw_box.addWidget(btn_browse_nw)

        nw_layout.addWidget(nw_lbl)
        nw_layout.addLayout(nw_box)

        prof_lbl = QLabel("Directorio del perfil de usuario compartido:")
        self.edit_profile_path = QLineEdit()
        nw_layout.addWidget(prof_lbl)
        nw_layout.addWidget(self.edit_profile_path)

        btn_clean_cache = QPushButton("🧹 Vaciar caché temporal de NW.js ahora")
        btn_clean_cache.clicked.connect(self._clean_nw_cache)
        nw_layout.addWidget(btn_clean_cache)
        layout.addWidget(nw_group)

        # 3. Sliders de Rendimiento e Hilos CPU
        perf_group = QGroupBox("⚡ Asignación de Hilos de Procesamiento (CPU)")
        perf_layout = QVBoxLayout(perf_group)
        perf_layout.setSpacing(10)

        max_cpu = os.cpu_count() or 4
        max_vid = max(1, max_cpu // 2)

        # Imágenes
        self.lbl_threads_img = QLabel(f"Hilos para Imágenes: {max_cpu}")
        self.slider_threads_img = QSlider(Qt.Orientation.Horizontal)
        self.slider_threads_img.setRange(1, max_cpu)
        self.slider_threads_img.setValue(max_cpu)
        self.slider_threads_img.valueChanged.connect(
            lambda v: self.lbl_threads_img.setText(f"Hilos para Imágenes: {v}")
        )
        perf_layout.addWidget(self.lbl_threads_img)
        perf_layout.addWidget(self.slider_threads_img)

        # Audio
        self.lbl_threads_aud = QLabel(f"Hilos para Audio: {max_cpu}")
        self.slider_threads_aud = QSlider(Qt.Orientation.Horizontal)
        self.slider_threads_aud.setRange(1, max_cpu)
        self.slider_threads_aud.setValue(max_cpu)
        self.slider_threads_aud.valueChanged.connect(
            lambda v: self.lbl_threads_aud.setText(f"Hilos para Audio: {v}")
        )
        perf_layout.addWidget(self.lbl_threads_aud)
        perf_layout.addWidget(self.slider_threads_aud)

        # Video
        self.lbl_threads_vid = QLabel("Videos simultáneos concurrentes: 1")
        self.slider_threads_vid = QSlider(Qt.Orientation.Horizontal)
        self.slider_threads_vid.setRange(1, max_vid)
        self.slider_threads_vid.setValue(1)
        self.slider_threads_vid.valueChanged.connect(
            lambda v: self.lbl_threads_vid.setText(f"Videos simultáneos concurrentes: {v}")
        )
        perf_layout.addWidget(self.lbl_threads_vid)
        perf_layout.addWidget(self.slider_threads_vid)

        layout.addWidget(perf_group)

        # 4. Carpeta de Trabajo Temporal
        temp_group = QGroupBox("📁 Ubicación de Trabajo Temporal")
        temp_layout = QVBoxLayout(temp_group)
        temp_layout.setSpacing(8)

        self.radio_temp_default = QRadioButton("Carpeta temporal predeterminada (creada junto a la original a procesar)")
        self.radio_temp_custom = QRadioButton("Carpeta temporal personalizada:")

        custom_box = QHBoxLayout()
        self.edit_custom_temp = QLineEdit()
        self.edit_custom_temp.setPlaceholderText("Seleccionar directorio...")
        self.btn_browse_temp = QPushButton("...")
        self.btn_browse_temp.clicked.connect(self._browse_temp)
        custom_box.addWidget(self.edit_custom_temp)
        custom_box.addWidget(self.btn_browse_temp)

        self.radio_temp_custom.toggled.connect(self._toggle_temp)

        temp_layout.addWidget(self.radio_temp_default)
        temp_layout.addWidget(self.radio_temp_custom)
        temp_layout.addLayout(custom_box)
        layout.addWidget(temp_group)

        # Guardar
        btn_save = QPushButton("💾 Guardar Ajustes de Sistema")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_values)
        layout.addWidget(btn_save)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.check_binaries()

    def check_binaries(self) -> None:
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
        p, _ = QFileDialog.getOpenFileName(self, "Seleccionar nw.exe", "", "Ejecutable (*.exe)")
        if p:
            self.edit_nw_path.setText(p)
            self.check_binaries()

    def _browse_temp(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Seleccionar directorio temporal")
        if p:
            self.edit_custom_temp.setText(p)

    def _toggle_temp(self, checked: bool) -> None:
        self.edit_custom_temp.setEnabled(checked)
        self.btn_browse_temp.setEnabled(checked)

    def _clean_nw_cache(self) -> None:
        expanded_path = Path(os.path.expandvars(self.edit_profile_path.text().strip()))
        if not expanded_path.exists():
            QMessageBox.information(self, "Limpieza de Caché", "No existe un perfil previo de NW.js.")
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
            f"Se limpiaron {cleared} carpetas de caché temporal de NW.js.\nLas partidas guardadas no sufrieron cambios."
        )

    def load_values(self) -> None:
        s = load_all_settings()
        self.edit_nw_path.setText(s.get("nw_path", ""))
        self.edit_profile_path.setText(s.get("profile_path", r"%localappdata%\RPGM\User Data"))
        self.slider_threads_img.setValue(s.get("threads_image", os.cpu_count() or 4))
        self.slider_threads_aud.setValue(s.get("threads_audio", os.cpu_count() or 4))
        self.slider_threads_vid.setValue(s.get("threads_video", 1))

        use_custom = s.get("use_custom_temp", False)
        self.radio_temp_custom.setChecked(use_custom)
        self.radio_temp_default.setChecked(not use_custom)
        self.edit_custom_temp.setText(s.get("temp_folder_custom", ""))
        self._toggle_temp(use_custom)

    def save_values(self) -> None:
        save_settings_dict({
            "nw_path": self.edit_nw_path.text().strip(),
            "profile_path": self.edit_profile_path.text().strip(),
            "threads_image": self.slider_threads_img.value(),
            "threads_audio": self.slider_threads_aud.value(),
            "threads_video": self.slider_threads_vid.value(),
            "use_custom_temp": self.radio_temp_custom.isChecked(),
            "temp_folder_custom": self.edit_custom_temp.text().strip(),
        })
        QMessageBox.information(self, "Preferencias de Sistema", "Ajustes de sistema guardados correctamente.")

