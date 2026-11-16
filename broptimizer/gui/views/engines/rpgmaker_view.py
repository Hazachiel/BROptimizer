"""Vista para RPG Maker Moderno (MV, MZ)."""

from typing import Any
from PySide6.QtWidgets import QVBoxLayout, QCheckBox

from broptimizer.gui.views.engines.base_engine import BaseEngineQueueView


class RPGMakerModernView(BaseEngineQueueView):
    """Vista especializada para RPG Maker MV y MZ."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            engine_id="engine_rpgmaker",
            title="RPG Maker Moderno (MV / MZ)",
            parent=parent
        )

    def setup_engine_options(self, layout: QVBoxLayout) -> None:
        self.chk_decrypt = QCheckBox("Desencriptar archivos (.rpgmvp, .rpgmvm, .rpgmvo, .png_, .ogg_, .m4a_)")
        self.chk_decrypt.setChecked(False)

        self.chk_delete_encrypted = QCheckBox("Borrar archivos encriptados luego de la desencriptación exitosa")
        self.chk_delete_encrypted.setChecked(False)

        self.chk_overwrite_smaller = QCheckBox("Reemplazar automáticamente si el resultado final es más pequeño")
        self.chk_overwrite_smaller.setChecked(True)

        self.chk_nwjs_clean = QCheckBox("Aplicar parche y limpieza NW.js (elimina runtime redundante y genera launcher)")
        self.chk_nwjs_clean.setChecked(True)

        layout.addWidget(self.chk_decrypt)
        layout.addWidget(self.chk_delete_encrypted)
        layout.addWidget(self.chk_overwrite_smaller)
        layout.addWidget(self.chk_nwjs_clean)

    def get_engine_specific_options(self) -> dict[str, Any]:
        return {
            "decrypt": self.chk_decrypt.isChecked(),
            "delete_encrypted": self.chk_delete_encrypted.isChecked(),
            "overwrite_smaller": self.chk_overwrite_smaller.isChecked(),
            "apply_nwjs_clean": self.chk_nwjs_clean.isChecked(),
        }

