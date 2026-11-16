"""Vista para juegos creados con Wolf RPG Editor."""

from typing import Any
from PySide6.QtWidgets import QVBoxLayout, QCheckBox

from broptimizer.gui.views.engines.base_engine import BaseEngineQueueView


class WolfRPGView(BaseEngineQueueView):
    """Vista especializada para juegos de Wolf RPG Editor."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            engine_id="engine_wolfrpg",
            title="Wolf RPG Editor",
            parent=parent
        )

    def setup_engine_options(self, layout: QVBoxLayout) -> None:
        self.chk_decrypt = QCheckBox("Desempaquetar archivos (.wolf)")
        self.chk_decrypt.setChecked(False)

        self.chk_delete_encrypted = QCheckBox("Borrar archivos empaquetados luego de desempaquetar")
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

