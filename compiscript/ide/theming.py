from __future__ import annotations
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

# Simple, dependency-free light/dark theme using Fusion style

def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(30, 30, 30))
    p.setColor(QPalette.WindowText, QColor(220, 220, 220))
    p.setColor(QPalette.Base, QColor(25, 25, 25))
    p.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    p.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    p.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    p.setColor(QPalette.Text, QColor(220, 220, 220))
    p.setColor(QPalette.Button, QColor(45, 45, 45))
    p.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    p.setColor(QPalette.BrightText, QColor(255, 0, 0))
    p.setColor(QPalette.Highlight, QColor(76, 163, 224))
    p.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    p.setColor(QPalette.Link, QColor(85, 170, 255))
    return p


def apply_theme(app: QApplication, mode: str) -> None:
    mode = (mode or "dark").lower()
    # Use Fusion so the palette applies consistently across platforms
    app.setStyle("Fusion")
    if mode == "dark":
        app.setPalette(_dark_palette())
    else:
        # Reset to the default palette for light mode
        app.setPalette(app.style().standardPalette())