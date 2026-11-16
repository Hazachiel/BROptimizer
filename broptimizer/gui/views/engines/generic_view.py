"""Vista para carpetas multimedia genéricas y archivos sueltos."""

from typing import Any
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox
)

from broptimizer.gui.views.engines.base_engine import BaseEngineQueueView


class GenericView(BaseEngineQueueView):
    """Vista especializada para carpetas de assets genéricos y archivos individuales."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            engine_id="engine_generic",
            title="Multimedia Genérico / Archivos Sueltos",
            parent=parent
        )

    def setup_engine_options(self, layout: QVBoxLayout) -> None:
        # Checkboxes principales
        self.chk_preserve_ext = QCheckBox("Preservar extensión original de los archivos procesados")
        self.chk_preserve_ext.setChecked(True)

        self.chk_overwrite_smaller = QCheckBox("Reemplazar automáticamente si el resultado final es más pequeño")
        self.chk_overwrite_smaller.setChecked(True)

        layout.addWidget(self.chk_preserve_ext)
        layout.addWidget(self.chk_overwrite_smaller)

        # Selectores rápidos de conversión para genéricos
        fmt_layout = QHBoxLayout()
        fmt_layout.setSpacing(16)

        # Imágenes
        img_box = QHBoxLayout()
        img_lbl = QLabel("Formato Imágenes:")
        self.combo_img_fmt = QComboBox()
        self.combo_img_fmt.addItems(["WebP", "PNG Optimizado", "JPEG"])
        img_box.addWidget(img_lbl)
        img_box.addWidget(self.combo_img_fmt)
        fmt_layout.addLayout(img_box)

        # Audio
        aud_box = QHBoxLayout()
        aud_lbl = QLabel("Formato Audio:")
        self.combo_aud_fmt = QComboBox()
        self.combo_aud_fmt.addItems(["Vorbis / OGG", "Opus", "MP3"])
        aud_box.addWidget(aud_lbl)
        aud_box.addWidget(self.combo_aud_fmt)
        fmt_layout.addLayout(aud_box)

        # Video
        vid_box = QHBoxLayout()
        vid_lbl = QLabel("Códec Video:")
        self.combo_vid_codec = QComboBox()
        self.combo_vid_codec.addItems(["H.264", "VP8", "VP9"])
        vid_box.addWidget(vid_lbl)
        vid_box.addWidget(self.combo_vid_codec)
        fmt_layout.addLayout(vid_box)

        layout.addSpacing(6)
        layout.addLayout(fmt_layout)

    def get_engine_specific_options(self) -> dict[str, Any]:
        return {
            "preserve_extension": self.chk_preserve_ext.isChecked(),
            "overwrite_smaller": self.chk_overwrite_smaller.isChecked(),
            "target_image_format": self.combo_img_fmt.currentText(),
            "target_audio_format": self.combo_aud_fmt.currentText(),
            "target_video_codec": self.combo_vid_codec.currentText(),
        }

