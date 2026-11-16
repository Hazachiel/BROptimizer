"""Vista placeholder para herramientas futuras de desempaquetado de assets."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ToolsView(QWidget):
    """Vista de herramientas avanzadas y desempaquetado."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("📦 Herramientas y Desempaquetador de Assets")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #60A5FA;")
        
        info = QLabel(
            "Próximamente disponible:\n\n"
            "• Extracción automática de paquetes Ren'Py (.rpa)\n"
            "• Extracción y desencriptado de RPG Maker (.rpgmvp, .rpgmvm, .rgssad)\n"
            "• Desempaquetador de Wolf RPG Editor (.wolf)\n\n"
            "Los assets extraídos podrán enviarse directamente a la Cola de Optimización."
        )
        info.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.6;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addSpacing(15)
        layout.addWidget(info)

