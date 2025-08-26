from __future__ import annotations
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Paletas base (sin libs externas)
def _light_palette() -> QPalette:
    p = QPalette()
    # Fondo y texto principales
    p.setColor(QPalette.Window, QColor("#FFFFFF"))
    p.setColor(QPalette.WindowText, QColor("#000000"))
    p.setColor(QPalette.Base, QColor("#FFFFFF"))
    p.setColor(QPalette.AlternateBase, QColor("#F5F5F5"))
    p.setColor(QPalette.Text, QColor("#000000"))
    p.setColor(QPalette.Button, QColor("#FFFFFF"))
    p.setColor(QPalette.ButtonText, QColor("#000000"))
    p.setColor(QPalette.ToolTipBase, QColor("#FFFFDD"))
    p.setColor(QPalette.ToolTipText, QColor("#000000"))

    # Selección
    p.setColor(QPalette.Highlight, QColor("#2979FF"))           # azul accesible
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))

    # Links
    p.setColor(QPalette.Link, QColor("#1A73E8"))
    p.setColor(QPalette.LinkVisited, QColor("#7B1FA2"))

    # Disabled
    disabled = QColor("#808080")
    p.setColor(QPalette.Disabled, QPalette.Text, disabled)
    p.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    p.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    p.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#B0B0B0"))
    p.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#FFFFFF"))

    return p

def _dark_palette() -> QPalette:
    p = QPalette()
    bg = QColor("#121212")
    base = QColor("#1E1E1E")
    text = QColor("#E6E6E6")
    subtle = QColor("#2A2A2A")

    p.setColor(QPalette.Window, bg)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, base)
    p.setColor(QPalette.AlternateBase, subtle)
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, base)
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, QColor("#333333"))
    p.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))

    p.setColor(QPalette.Highlight, QColor("#2D64FF"))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))

    p.setColor(QPalette.Link, QColor("#64B5F6"))
    p.setColor(QPalette.LinkVisited, QColor("#90CAF9"))

    disabled = QColor("#8A8A8A")
    p.setColor(QPalette.Disabled, QPalette.Text, disabled)
    p.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    p.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    p.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#404040"))
    p.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#C0C0C0"))
    return p

# QSS suave para afinar contraste y bordes
_LIGHT_QSS = """
QTreeView, QPlainTextEdit, QLineEdit, QTableView, QTextEdit {
    background: white; color: black; selection-background-color: #2979FF; selection-color: white;
}
QToolBar { background: #FFFFFF; border: 0; }
QStatusBar { background: #FFFFFF; }
QDockWidget::title { background: #F5F5F5; padding: 4px; }
"""

_DARK_QSS = """
QTreeView, QPlainTextEdit, QLineEdit, QTableView, QTextEdit {
    background: #1E1E1E; color: #E6E6E6; selection-background-color: #2D64FF; selection-color: white;
}
QToolBar { background: #1E1E1E; border: 0; }
QStatusBar { background: #121212; }
QDockWidget::title { background: #1A1A1A; padding: 4px; }
"""

def apply_theme(app: QApplication, theme: str = "dark") -> None:
    """Aplica tema 'light' (blanco/negro) u 'dark' (fondo oscuro)."""
    if not isinstance(app, QApplication):
        return

    app.setStyle("Fusion")  # base consistente cross-platform

    if (theme or "").lower() == "light":
        app.setPalette(_light_palette())
        app.setStyleSheet(_LIGHT_QSS)
        app.setProperty("theme", "light")
    else:
        app.setPalette(_dark_palette())
        app.setStyleSheet(_DARK_QSS)
        app.setProperty("theme", "dark")

def theme_is_dark(app: QApplication) -> bool:
    return (app.property("theme") or "dark") == "dark"
