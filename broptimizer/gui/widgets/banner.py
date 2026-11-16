"""Banner superior de la aplicación con branding, versión y enlaces."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel


class HeaderBanner(QWidget):
    """Encabezado superior compacto de BROptimizer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderBanner")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Contenedor izquierdo: Logo/Título y Tagline
        left_box = QVBoxLayout()
        left_box.setSpacing(2)

        title_lbl = QLabel("🚀 BROptimizer v2.0")
        title_lbl.setObjectName("BannerTitle")

        tagline_lbl = QLabel("Optimizador multimedia inteligente para juegos indie y assets")
        tagline_lbl.setObjectName("BannerTagline")

        left_box.addWidget(title_lbl)
        left_box.addWidget(tagline_lbl)
        layout.addLayout(left_box)

        layout.addStretch()

        # Contenedor derecho: Enlaces y créditos
        right_box = QVBoxLayout()
        right_box.setSpacing(2)
        right_box.setAlignment(Qt.AlignmentFlag.AlignRight)

        author_lbl = QLabel("Autor: Hazachiel")
        author_lbl.setObjectName("BannerTagline")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        github_link = QLabel('<a href="https://github.com/Hazachiel/BROptimizer" style="color: #60A5FA; text-decoration: none;">GitHub Repository ↗</a>')
        github_link.setObjectName("BannerLink")
        github_link.setAlignment(Qt.AlignmentFlag.AlignRight)
        github_link.setTextFormat(Qt.TextFormat.RichText)
        github_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        github_link.setOpenExternalLinks(True)

        right_box.addWidget(author_lbl)
        right_box.addWidget(github_link)
        layout.addLayout(right_box)

