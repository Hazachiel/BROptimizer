"""Preferencias de Audio: Frecuencias de muestreo máximas y tope de bitrate."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QMessageBox, QScrollArea
)

from broptimizer.gui.views.preferences.pref_storage import load_all_settings, save_settings_dict


class AudioPreferencesView(QWidget):
    """Sub-vista de configuración para algoritmos de compresión de audio con FFmpeg."""

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

        # 1. Frecuencias de Muestreo Máximas (Sample Rates)
        sr_group = QGroupBox("🎵 Frecuencias de Muestreo Máximas (Sample Rates)")
        sr_layout = QVBoxLayout(sr_group)
        sr_layout.setSpacing(10)

        # Opus
        opus_box = QHBoxLayout()
        opus_lbl = QLabel("Frecuencia máxima para Opus:")
        self.combo_opus_sr = QComboBox()
        self.combo_opus_sr.addItems(["48000 Hz (Estándar de estudio)", "44100 Hz", "32000 Hz", "24000 Hz"])
        opus_box.addWidget(opus_lbl)
        opus_box.addWidget(self.combo_opus_sr)
        sr_layout.addLayout(opus_box)

        # Vorbis
        vorbis_box = QHBoxLayout()
        vorbis_lbl = QLabel("Frecuencia máxima para Vorbis (OGG):")
        self.combo_vorbis_sr = QComboBox()
        self.combo_vorbis_sr.addItems(["44100 Hz (Estándar CD)", "32000 Hz", "24000 Hz"])
        vorbis_box.addWidget(vorbis_lbl)
        vorbis_box.addWidget(self.combo_vorbis_sr)
        sr_layout.addLayout(vorbis_box)

        # MP3
        mp3_box = QHBoxLayout()
        mp3_lbl = QLabel("Frecuencia máxima para MP3:")
        self.combo_mp3_sr = QComboBox()
        self.combo_mp3_sr.addItems(["44100 Hz (Estándar CD)", "32000 Hz", "24000 Hz"])
        mp3_box.addWidget(mp3_lbl)
        mp3_box.addWidget(self.combo_mp3_sr)
        sr_layout.addLayout(mp3_box)

        layout.addWidget(sr_group)

        # 2. Tope de Bitrate
        br_group = QGroupBox("🎚️ Reglas de Bitrate")
        br_layout = QVBoxLayout(br_group)
        br_layout.setSpacing(8)

        br_box = QHBoxLayout()
        br_lbl = QLabel("Tope máximo de Bitrate:")
        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems([
            "64 kbps (Ahorro agresivo para voz/sfx)",
            "96 kbps (Estándar BROptimizer - Calidad transparente)",
            "128 kbps (Alta fidelidad musical)",
        ])
        self.combo_bitrate.setCurrentIndex(1)
        br_box.addWidget(br_lbl)
        br_box.addWidget(self.combo_bitrate)
        br_layout.addLayout(br_box)

        note_lbl = QLabel("Nota: Si el audio original ya tiene un bitrate inferior al tope, se preservará su bitrate menor original.")
        note_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")
        br_layout.addWidget(note_lbl)

        layout.addWidget(br_group)

        # Guardar
        btn_save = QPushButton("💾 Guardar Ajustes de Audio")
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
        opus_val = str(s.get("max_opus_samplerate", 48000))
        for i in range(self.combo_opus_sr.count()):
            if opus_val in self.combo_opus_sr.itemText(i):
                self.combo_opus_sr.setCurrentIndex(i)
                break

        vorbis_val = str(s.get("max_vorbis_samplerate", 44100))
        for i in range(self.combo_vorbis_sr.count()):
            if vorbis_val in self.combo_vorbis_sr.itemText(i):
                self.combo_vorbis_sr.setCurrentIndex(i)
                break

        br_val = str(s.get("max_audio_bitrate", 96))
        for i in range(self.combo_bitrate.count()):
            if br_val in self.combo_bitrate.itemText(i):
                self.combo_bitrate.setCurrentIndex(i)
                break

    def save_values(self) -> None:
        def extract_num(text: str, default: int) -> int:
            for part in text.split():
                if part.isdigit():
                    return int(part)
            return default

        save_settings_dict({
            "max_opus_samplerate": extract_num(self.combo_opus_sr.currentText(), 48000),
            "max_vorbis_samplerate": extract_num(self.combo_vorbis_sr.currentText(), 44100),
            "max_mp3_samplerate": extract_num(self.combo_mp3_sr.currentText(), 44100),
            "max_audio_bitrate": extract_num(self.combo_bitrate.currentText(), 96),
        })
        QMessageBox.information(self, "Preferencias de Audio", "Ajustes de audio guardados correctamente.")

