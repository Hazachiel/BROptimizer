"""Preferencias de Video: desired_res, multiplicadores de calidad, yuv420p y muxer Matroska."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSpinBox, QCheckBox, QComboBox, QMessageBox, QScrollArea
)

from broptimizer.gui.views.preferences.pref_storage import load_all_settings, save_settings_dict


class VideoPreferencesView(QWidget):
    """Sub-vista de configuración para algoritmos de compresión y reglas de video con FFmpeg."""

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

        # 1. Códec y Resolución Objetivo
        res_group = QGroupBox("🎬 Códec y Resolución Objetivo")
        res_layout = QVBoxLayout(res_group)
        res_layout.setSpacing(10)

        # Códec
        codec_box = QHBoxLayout()
        codec_lbl = QLabel("Códec de video predeterminado:")
        self.combo_codec = QComboBox()
        self.combo_codec.addItem("H.264 (Recomendado)", "h264")
        self.combo_codec.addItem("VP8 (Máxima compatibilidad web)", "vp8")
        self.combo_codec.addItem("VP9 (Mayor compresión)", "vp9")
        codec_box.addWidget(codec_lbl)
        codec_box.addWidget(self.combo_codec)
        res_layout.addLayout(codec_box)

        # CRF
        crf_box = QHBoxLayout()
        crf_lbl = QLabel("Factor de tasa constante (CRF):")
        self.combo_crf = QComboBox()
        self.combo_crf.addItem("26 (Equilibrado / Recomendado)", 26)
        self.combo_crf.addItem("15 (Nearlossless / Máxima calidad)", 15)
        self.combo_crf.addItem("31 (Máximo ahorro de espacio)", 31)
        crf_box.addWidget(crf_lbl)
        crf_box.addWidget(self.combo_crf)
        res_layout.addLayout(crf_box)

        res_box = QHBoxLayout()
        res_lbl = QLabel("Resolución objetivo (lado menor en píxeles, desired_res):")
        self.spin_desired_res = QSpinBox()
        self.spin_desired_res.setRange(240, 2160)
        self.spin_desired_res.setValue(600)
        self.spin_desired_res.setSingleStep(20)
        res_box.addWidget(res_lbl)
        res_box.addWidget(self.spin_desired_res)
        res_layout.addLayout(res_box)

        res_info = QLabel("Valor por defecto: 600 px. Se ajusta automáticamente a dimensiones pares para compatibilidad.")
        res_info.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")
        res_layout.addWidget(res_info)

        layout.addWidget(res_group)

        # 2. Multiplicadores de Calidad de la Fórmula Dinámica
        mult_group = QGroupBox("⚖️ Multiplicadores de Calidad de Bitrate")
        mult_layout = QVBoxLayout(mult_group)
        mult_layout.setSpacing(10)

        # H.264
        h264_box = QHBoxLayout()
        h264_lbl = QLabel("Multiplicador para H.264 (200 - 600):")
        self.spin_mult_h264 = QSpinBox()
        self.spin_mult_h264.setRange(200, 600)
        self.spin_mult_h264.setValue(400)
        self.spin_mult_h264.setSingleStep(25)
        h264_box.addWidget(h264_lbl)
        h264_box.addWidget(self.spin_mult_h264)
        mult_layout.addLayout(h264_box)

        # VP8 / VP9
        vpx_box = QHBoxLayout()
        vpx_lbl = QLabel("Multiplicador para VP8 / VP9 (100 - 400):")
        self.spin_mult_vpx = QSpinBox()
        self.spin_mult_vpx.setRange(100, 400)
        self.spin_mult_vpx.setValue(250)
        self.spin_mult_vpx.setSingleStep(25)
        vpx_box.addWidget(vpx_lbl)
        vpx_box.addWidget(self.spin_mult_vpx)
        mult_layout.addLayout(vpx_box)

        layout.addWidget(mult_group)

        # 3. Reglas de Compatibilidad Universal
        compat_group = QGroupBox("🛡️ Reglas de Compatibilidad Universal")
        compat_layout = QVBoxLayout(compat_group)
        compat_layout.setSpacing(8)

        self.chk_force_yuv420p = QCheckBox("Forzar formato de píxeles universal (-pix_fmt yuv420p) para compatibilidad total con reproductores")
        self.chk_force_yuv420p.setChecked(True)

        self.chk_force_matroska = QCheckBox("Forzar Muxer Matroska (-f matroska) al preservar extensión .webm para evitar fallos de muxer")
        self.chk_force_matroska.setChecked(True)

        compat_layout.addWidget(self.chk_force_yuv420p)
        compat_layout.addWidget(self.chk_force_matroska)
        layout.addWidget(compat_group)

        # Guardar
        btn_save = QPushButton("💾 Guardar Ajustes de Video")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self.save_values)
        layout.addWidget(btn_save)

        layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load_values(self) -> None:
        s = load_all_settings()
        # Códec
        saved_codec = str(s.get("video_codec", "h264")).lower()
        idx_codec = self.combo_codec.findData(saved_codec)
        if idx_codec >= 0:
            self.combo_codec.setCurrentIndex(idx_codec)

        # CRF
        saved_crf = int(s.get("crf", 26))
        idx_crf = self.combo_crf.findData(saved_crf)
        if idx_crf >= 0:
            self.combo_crf.setCurrentIndex(idx_crf)

        self.spin_desired_res.setValue(s.get("desired_res", 600))
        self.spin_mult_h264.setValue(s.get("quality_mult_h264", 400))
        self.spin_mult_vpx.setValue(s.get("quality_mult_vpx", 250))
        self.chk_force_yuv420p.setChecked(s.get("force_yuv420p", True))
        self.chk_force_matroska.setChecked(s.get("force_matroska_webm", True))

    def save_values(self) -> None:
        save_settings_dict({
            "video_codec": self.combo_codec.currentData(),
            "crf": self.combo_crf.currentData(),
            "desired_res": self.spin_desired_res.value(),
            "quality_mult_h264": self.spin_mult_h264.value(),
            "quality_mult_vpx": self.spin_mult_vpx.value(),
            "force_yuv420p": self.chk_force_yuv420p.isChecked(),
            "force_matroska_webm": self.chk_force_matroska.isChecked(),
        })
        QMessageBox.information(self, "Preferencias de Video", "Ajustes de video guardados correctamente.")

