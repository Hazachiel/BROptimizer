"""Preferencias de Imágenes: Calidad WebP, compresión PNG/JPEG y metadatos."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSlider, QComboBox, QCheckBox, QMessageBox, QScrollArea
)

from broptimizer.gui.views.preferences.pref_storage import load_all_settings, save_settings_dict


class ImagePreferencesView(QWidget):
    """Sub-vista de configuración para algoritmos de compresión de imágenes."""

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

        # 1. Configuración WebP
        webp_group = QGroupBox("🖼️ Ajustes de WebP")
        webp_layout = QVBoxLayout(webp_group)
        webp_layout.setSpacing(10)

        # Calidad Lossy
        self.lbl_webp_q = QLabel("Calidad WebP (Lossy): 82")
        self.slider_webp_q = QSlider(Qt.Orientation.Horizontal)
        self.slider_webp_q.setRange(50, 100)
        self.slider_webp_q.setValue(82)
        self.slider_webp_q.valueChanged.connect(
            lambda v: self.lbl_webp_q.setText(f"Calidad WebP (Lossy): {v}")
        )
        webp_layout.addWidget(self.lbl_webp_q)
        webp_layout.addWidget(self.slider_webp_q)

        # Método / Esfuerzo
        meth_box = QHBoxLayout()
        meth_lbl = QLabel("Nivel de esfuerzo / Método WebP:")
        self.combo_webp_method = QComboBox()
        self.combo_webp_method.addItems([
            "0 - Muy rápido (Mínima compresión)",
            "1 - Rápido",
            "2 - Normal",
            "3 - Bueno",
            "4 - Muy bueno",
            "5 - Excelente",
            "6 - Máxima compresión (Recomendado)",
        ])
        self.combo_webp_method.setCurrentIndex(6)
        meth_box.addWidget(meth_lbl)
        meth_box.addWidget(self.combo_webp_method)
        webp_layout.addLayout(meth_box)

        layout.addWidget(webp_group)

        # 2. PNG y JPEG
        legacy_group = QGroupBox("🎨 Ajustes de PNG y JPEG")
        legacy_layout = QVBoxLayout(legacy_group)
        legacy_layout.setSpacing(10)

        # Compresión PNG
        self.lbl_png_comp = QLabel("Nivel de compresión PNG (0 = ninguna, 9 = máxima): 9")
        self.slider_png_comp = QSlider(Qt.Orientation.Horizontal)
        self.slider_png_comp.setRange(0, 9)
        self.slider_png_comp.setValue(9)
        self.slider_png_comp.valueChanged.connect(
            lambda v: self.lbl_png_comp.setText(f"Nivel de compresión PNG (0 = ninguna, 9 = máxima): {v}")
        )
        legacy_layout.addWidget(self.lbl_png_comp)
        legacy_layout.addWidget(self.slider_png_comp)

        # Calidad JPEG
        self.lbl_jpeg_q = QLabel("Calidad JPEG: 80")
        self.slider_jpeg_q = QSlider(Qt.Orientation.Horizontal)
        self.slider_jpeg_q.setRange(50, 100)
        self.slider_jpeg_q.setValue(80)
        self.slider_jpeg_q.valueChanged.connect(
            lambda v: self.lbl_jpeg_q.setText(f"Calidad JPEG: {v}")
        )
        legacy_layout.addWidget(self.lbl_jpeg_q)
        legacy_layout.addWidget(self.slider_jpeg_q)

        layout.addWidget(legacy_group)

        # 3. Metadatos
        meta_group = QGroupBox("🏷️ Integridad y Metadatos")
        meta_layout = QVBoxLayout(meta_group)
        self.chk_tag_metadata = QCheckBox("Inyectar etiqueta 'BROptimized' (evita re-optimizar si se procesa la misma carpeta dos veces)")
        self.chk_tag_metadata.setChecked(True)
        meta_layout.addWidget(self.chk_tag_metadata)
        layout.addWidget(meta_group)

        # Botón Guardar
        btn_save = QPushButton("💾 Guardar Ajustes de Imágenes")
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
        self.slider_webp_q.setValue(s.get("webp_quality", 82))
        method_idx = min(6, max(0, s.get("webp_method", 6)))
        self.combo_webp_method.setCurrentIndex(method_idx)
        self.slider_png_comp.setValue(s.get("png_compression", 9))
        self.slider_jpeg_q.setValue(s.get("jpeg_quality", 80))
        self.chk_tag_metadata.setChecked(s.get("tag_metadata", True))

    def save_values(self) -> None:
        save_settings_dict({
            "webp_quality": self.slider_webp_q.value(),
            "webp_method": self.combo_webp_method.currentIndex(),
            "png_compression": self.slider_png_comp.value(),
            "jpeg_quality": self.slider_jpeg_q.value(),
            "tag_metadata": self.chk_tag_metadata.isChecked(),
        })
        QMessageBox.information(self, "Preferencias de Imágenes", "Ajustes de imágenes guardados correctamente.")

