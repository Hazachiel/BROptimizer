"""Vista para RPG Maker Clásico / Legacy (XP, VX, VX Ace)."""

from typing import Any
from PySide6.QtWidgets import QVBoxLayout, QCheckBox

from broptimizer.gui.views.engines.base_engine import BaseEngineQueueView


class RPGMakerLegacyView(BaseEngineQueueView):
    """Vista especializada para RPG Maker XP, VX y VX Ace (RGSS)."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            engine_id="engine_legacy_rpg",
            title="RPG Maker Legacy (XP, VX, VX Ace)",
            parent=parent
        )

    def setup_engine_options(self, layout: QVBoxLayout) -> None:
        self.chk_decrypt = QCheckBox("Desencriptar archivos (.rgssad, .rgss2a, .rgss3a)")
        self.chk_decrypt.setChecked(False)

        self.chk_delete_encrypted = QCheckBox("Borrar archivos encriptados luego de la desencriptación exitosa")
        self.chk_delete_encrypted.setChecked(False)

        self.chk_overwrite_smaller = QCheckBox("Reemplazar automáticamente si el resultado final es más pequeño")
        self.chk_overwrite_smaller.setChecked(True)

        layout.addWidget(self.chk_decrypt)
        layout.addWidget(self.chk_delete_encrypted)
        layout.addWidget(self.chk_overwrite_smaller)

    def get_engine_specific_options(self) -> dict[str, Any]:
        return {
            "decrypt": self.chk_decrypt.isChecked(),
            "delete_encrypted": self.chk_delete_encrypted.isChecked(),
            "overwrite_smaller": self.chk_overwrite_smaller.isChecked(),
        }

