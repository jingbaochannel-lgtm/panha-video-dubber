"""Dark theme + named button styles used across the app.

Color palette is loosely based on the reference screenshot the project was
modeled after: dark slate background with vivid action-button accents.
"""
from __future__ import annotations

# --- core palette --------------------------------------------------------------
BG_WINDOW = "#2a2933"
BG_PANEL = "#34333d"
BG_PANEL_LIGHT = "#3d3c47"
BG_INPUT = "#2f2e38"
BORDER = "#46454f"
TEXT = "#e6e6ea"
TEXT_DIM = "#a8a8b3"
ACCENT = "#7c4dff"

# --- button colour roles -------------------------------------------------------
BTN = {
    "pink":   ("#e91e63", "#ffffff"),
    "yellow": ("#fbc02d", "#1c1c1c"),
    "purple": ("#7b1fa2", "#ffffff"),
    "red":    ("#c62828", "#ffffff"),
    "blue":   ("#1976d2", "#ffffff"),
    "teal":   ("#00838f", "#ffffff"),
    "green":  ("#2e7d32", "#ffffff"),
    "orange": ("#ef6c00", "#ffffff"),
    "indigo": ("#3949ab", "#ffffff"),
    "slate":  ("#455a64", "#ffffff"),
}


def button_qss(role: str) -> str:
    """Return a QSS snippet for a colour-named button role."""
    bg, fg = BTN.get(role, (BG_PANEL_LIGHT, TEXT))
    return f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {_lighten(bg, 0.08)}; }}
        QPushButton:pressed {{ background: {_darken(bg, 0.10)}; }}
        QPushButton:disabled {{ background: #555560; color: #9a9aa3; }}
    """


def app_qss() -> str:
    """Global stylesheet applied to the QApplication."""
    return f"""
        QMainWindow, QWidget {{
            background: {BG_WINDOW};
            color: {TEXT};
            font-size: 12px;
        }}
        QGroupBox {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 10px;
            padding: 8px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: {TEXT};
        }}
        QLabel {{ color: {TEXT}; }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
            background: {BG_INPUT};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 3px 6px;
            selection-background-color: {ACCENT};
        }}
        QComboBox::drop-down {{ width: 16px; }}
        QHeaderView::section {{
            background: {BG_PANEL_LIGHT};
            color: {TEXT};
            padding: 6px 8px;
            border: 0;
            border-right: 1px solid {BORDER};
            font-weight: 600;
        }}
        QTableWidget, QTableView {{
            background: {BG_INPUT};
            color: {TEXT};
            gridline-color: {BORDER};
            alternate-background-color: {BG_PANEL_LIGHT};
            selection-background-color: {ACCENT};
        }}
        QCheckBox {{ color: {TEXT}; }}
        QSlider::groove:horizontal {{
            background: {BG_INPUT};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {ACCENT};
            width: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QStatusBar {{
            background: {BG_PANEL};
            color: {TEXT_DIM};
            border-top: 1px solid {BORDER};
        }}
        QToolTip {{
            background: #1c1c24;
            color: {TEXT};
            border: 1px solid {BORDER};
            padding: 4px 6px;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {BG_PANEL};
            border: 0;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {BG_PANEL_LIGHT};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{ background: transparent; height: 0; width: 0; }}
        QMenuBar, QMenu {{ background: {BG_PANEL}; color: {TEXT}; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {ACCENT}; }}
    """


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, c)) for c in rgb))


def _lighten(h: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(h)
    return _rgb_to_hex((int(r + (255 - r) * amount), int(g + (255 - g) * amount), int(b + (255 - b) * amount)))


def _darken(h: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(h)
    return _rgb_to_hex((int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount))))
