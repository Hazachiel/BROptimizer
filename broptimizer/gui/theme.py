"""Estilos modernos en tema oscuro para la GUI modular de BROptimizer."""

DARK_THEME_QSS = """
/* Ventana principal y fondos base */
QMainWindow, QDialog, QWidget {
    background-color: #121418;
    color: #E2E8F0;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    font-size: 13px;
}

/* Header Banner */
#HeaderBanner {
    background-color: #1A1D24;
    border-bottom: 1px solid #2D3748;
    padding: 10px 16px;
}

#BannerTitle {
    color: #F8FAFC;
    font-size: 18px;
    font-weight: 700;
}

#BannerTagline {
    color: #94A3B8;
    font-size: 12px;
}

#BannerLink {
    color: #60A5FA;
    font-size: 12px;
    text-decoration: none;
}

#BannerLink:hover {
    color: #93C5FD;
    text-decoration: underline;
}

/* Barra Lateral (Sidebar) */
#Sidebar {
    background-color: #16181D;
    border-right: 1px solid #2D3748;
    min-width: 215px;
    max-width: 215px;
}

.SidebarSectionLabel {
    color: #64748B;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 12px 4px 12px;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
}

#Sidebar QPushButton:hover {
    background-color: #1F242D;
    color: #F1F5F9;
}

#Sidebar QPushButton:checked, #Sidebar QPushButton[active="true"] {
    background-color: #2563EB;
    color: #FFFFFF;
}

/* Submenú colapsable de preferencias */
#PrefsSubmenu {
    background-color: #13151A;
    border-left: 2px solid #2D3748;
    margin-left: 14px;
    margin-bottom: 4px;
    border-radius: 0px 4px 4px 0px;
}

#PrefsSubmenu QPushButton {
    padding: 6px 10px 6px 14px;
    font-size: 11px;
    color: #94A3B8;
}

#PrefsSubmenu QPushButton:hover {
    background-color: #1D2128;
    color: #E2E8F0;
}

#PrefsSubmenu QPushButton:checked {
    background-color: #1E3A8A;
    color: #93C5FD;
    font-weight: 700;
}

/* Tablas */
QTableWidget {
    background-color: #181B20;
    border: 1px solid #2D3748;
    border-radius: 8px;
    gridline-color: #232832;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
    outline: none;
}

QHeaderView::section {
    background-color: #1E222B;
    color: #94A3B8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2D3748;
    font-weight: 600;
    font-size: 12px;
}

QTableCornerButton::section {
    background-color: #1E222B;
    border: none;
}

/* Botones estándar y de herramientas */
QPushButton {
    background-color: #242A35;
    color: #E2E8F0;
    border: 1px solid #3B4252;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2E3644;
    border-color: #4C566A;
}

QPushButton:pressed {
    background-color: #1E232B;
}

QPushButton:disabled {
    background-color: #181B20;
    color: #64748B;
    border-color: #2D3748;
}

/* Botones primarios (Acción principal) */
QPushButton#PrimaryButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #1D4ED8;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton#PrimaryButton:hover {
    background-color: #1D4ED8;
}

QPushButton#PrimaryButton:pressed {
    background-color: #1E40AF;
}

/* GroupBox y Paneles */
QGroupBox {
    background-color: #181B20;
    border: 1px solid #2D3748;
    border-radius: 8px;
    margin-top: 22px;
    font-weight: 600;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #60A5FA;
}

/* Controles de formulario: ComboBox, SpinBox, LineEdit */
QComboBox, QSpinBox, QLineEdit {
    background-color: #1E222B;
    color: #F8FAFC;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 5px 10px;
    selection-background-color: #2563EB;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border-color: #4B5563;
}

QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #1E222B;
    border: 1px solid #374151;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #2D3748;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #60A5FA;
    border: 2px solid #1E3A8A;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #93C5FD;
}

/* Checkbox y RadioButton */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #E2E8F0;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4B5563;
    border-radius: 4px;
    background-color: #1E222B;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2563EB;
    border-color: #3B82F6;
}

/* Barras de Progreso */
QProgressBar {
    background-color: #1E222B;
    border: 1px solid #2D3748;
    border-radius: 6px;
    text-align: center;
    color: #F8FAFC;
    font-size: 11px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #16181D;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #374151;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #4B5563;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
