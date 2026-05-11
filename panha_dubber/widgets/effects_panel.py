"""Video Effects panel — Blur, Text Overlay, Logo, Burn Subtitle settings."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..theme import BORDER, button_qss


@dataclass
class EffectsState:
    blur_enabled: bool = False
    blur_intensity: int = 10
    overlay_enabled: bool = False
    overlay_layer: str = "Text 1"
    overlay_text: str = "Panha_Dubber\nv1.0.0"
    overlay_font: str = "Sans"
    overlay_size: int = 28
    overlay_color: str = "#FFFFFF"
    overlay_bg_on: bool = False
    overlay_x: int = 20
    overlay_y: int = 20
    overlay_w: int = 360
    overlay_h: int = 50
    overlay_transition: str = "Loop Up"
    overlay_speed: int = 50
    overlay_shadow: bool = False
    logo_enabled: bool = False
    logo_path: str = ""
    logo_layer: str = "Logo 1"
    logo_x: int = 0
    logo_y: int = 246
    logo_scale: int = 35
    logo_opacity: int = 100
    logo_remove_green: bool = False
    logo_loop_reverse: bool = False
    burn_subtitle: bool = False
    subtitle_bg_pct: int = 30
    subtitle_ai_pct: int = 100
    subtitle_font: str = "Sans"
    subtitle_size: int = 18
    subtitle_color: str = "#FFFFFF"
    subtitle_bg_on: bool = True


class EffectsPanel(QGroupBox):
    apply_effects_clicked = pyqtSignal()
    state_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Video Effects", parent)
        self.state = EffectsState()

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._build_blur_section(), 0, 0)
        grid.addWidget(self._build_overlay_section(), 0, 1)
        grid.addWidget(self._build_logo_section(), 0, 2)

        apply_btn = QPushButton("\u2728 Apply Effects")
        apply_btn.setStyleSheet(button_qss("blue"))
        apply_btn.clicked.connect(self.apply_effects_clicked.emit)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(apply_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.addLayout(grid)
        layout.addLayout(bottom)

    # ----- sections ------------------------------------------------------------
    def _build_blur_section(self) -> QWidget:
        box = QGroupBox()
        v = QVBoxLayout(box)
        v.setContentsMargins(8, 8, 8, 8)
        self._blur_cb = QCheckBox("\U0001F32B Blur")
        self._blur_cb.toggled.connect(self._on_blur_changed)
        v.addWidget(self._blur_cb)

        row = QHBoxLayout()
        row.addWidget(QLabel("Intensity:"))
        self._blur_slider = QSlider(Qt.Orientation.Horizontal)
        self._blur_slider.setRange(0, 50)
        self._blur_slider.setValue(self.state.blur_intensity)
        self._blur_slider.valueChanged.connect(self._on_blur_changed)
        row.addWidget(self._blur_slider, 1)
        self._blur_val = QLabel(str(self.state.blur_intensity))
        row.addWidget(self._blur_val)
        v.addLayout(row)
        v.addStretch(1)
        return box

    def _build_overlay_section(self) -> QWidget:
        box = QGroupBox()
        v = QVBoxLayout(box)
        v.setContentsMargins(8, 8, 8, 8)

        head = QHBoxLayout()
        self._overlay_cb = QCheckBox("\u2728 Text Overlays")
        self._overlay_cb.toggled.connect(self._on_overlay_changed)
        head.addWidget(self._overlay_cb)
        head.addStretch(1)
        head.addWidget(QLabel("Layer:"))
        self._overlay_layer = QComboBox()
        self._overlay_layer.addItems(["Text 1", "Text 2", "Text 3"])
        head.addWidget(self._overlay_layer)
        remove_btn = QPushButton("\u2715")
        remove_btn.setFixedWidth(28)
        remove_btn.setStyleSheet(button_qss("red"))
        remove_btn.clicked.connect(lambda: self._overlay_text.clear())
        head.addWidget(remove_btn)
        v.addLayout(head)

        self._overlay_text = QPlainTextEdit()
        self._overlay_text.setPlainText(self.state.overlay_text)
        self._overlay_text.setFixedHeight(60)
        self._overlay_text.textChanged.connect(self._on_overlay_changed)
        v.addWidget(self._overlay_text)

        geom = QHBoxLayout()
        for label, attr, lo, hi in [("X:", "overlay_x", 0, 4000), ("Y:", "overlay_y", 0, 4000),
                                    ("W:", "overlay_w", 0, 4000), ("H:", "overlay_h", 0, 4000)]:
            geom.addWidget(QLabel(label))
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setValue(getattr(self.state, attr))
            sp.valueChanged.connect(lambda val, a=attr: self._set_state(a, val))
            geom.addWidget(sp)
        v.addLayout(geom)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font:"))
        self._overlay_font = QComboBox()
        self._overlay_font.addItems(["Sans", "AKbalthom SuperheroK", "AKbalthom Ream", "Battambang", "Khmer OS"])
        self._overlay_font.setCurrentText(self.state.overlay_font)
        self._overlay_font.currentTextChanged.connect(lambda v: self._set_state("overlay_font", v))
        font_row.addWidget(self._overlay_font, 1)
        font_row.addWidget(QLabel("Size:"))
        self._overlay_size = QSpinBox()
        self._overlay_size.setRange(6, 200)
        self._overlay_size.setValue(self.state.overlay_size)
        self._overlay_size.valueChanged.connect(lambda v: self._set_state("overlay_size", v))
        font_row.addWidget(self._overlay_size)
        v.addLayout(font_row)

        transition_row = QHBoxLayout()
        transition_row.addWidget(QLabel("Transition:"))
        self._overlay_transition = QComboBox()
        self._overlay_transition.addItems(["None", "Loop Up", "Loop Down", "Fade", "Slide L→R"])
        self._overlay_transition.setCurrentText(self.state.overlay_transition)
        self._overlay_transition.currentTextChanged.connect(lambda v: self._set_state("overlay_transition", v))
        transition_row.addWidget(self._overlay_transition)
        transition_row.addWidget(QLabel("Speed:"))
        self._overlay_speed = QSpinBox()
        self._overlay_speed.setRange(1, 999)
        self._overlay_speed.setSuffix(" px/s")
        self._overlay_speed.setValue(self.state.overlay_speed)
        self._overlay_speed.valueChanged.connect(lambda v: self._set_state("overlay_speed", v))
        transition_row.addWidget(self._overlay_speed)
        v.addLayout(transition_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self._overlay_color = QLineEdit(self.state.overlay_color)
        self._overlay_color.setFixedWidth(80)
        self._overlay_color.editingFinished.connect(
            lambda: self._set_state("overlay_color", self._overlay_color.text())
        )
        color_row.addWidget(self._overlay_color)
        color_row.addWidget(QLabel("BG:"))
        self._overlay_bg_btn = QPushButton("BG OFF")
        self._overlay_bg_btn.setCheckable(True)
        self._overlay_bg_btn.setStyleSheet(button_qss("slate"))
        self._overlay_bg_btn.toggled.connect(self._toggle_overlay_bg)
        color_row.addWidget(self._overlay_bg_btn)
        self._overlay_shadow_cb = QCheckBox("Shadow")
        self._overlay_shadow_cb.toggled.connect(lambda v: self._set_state("overlay_shadow", v))
        color_row.addWidget(self._overlay_shadow_cb)
        color_row.addStretch(1)
        v.addLayout(color_row)

        return box

    def _build_logo_section(self) -> QWidget:
        box = QGroupBox()
        v = QVBoxLayout(box)
        v.setContentsMargins(8, 8, 8, 8)

        head = QHBoxLayout()
        self._logo_cb = QCheckBox("\U0001F5BC Logo")
        self._logo_cb.toggled.connect(self._on_logo_changed)
        head.addWidget(self._logo_cb)
        v.addLayout(head)

        path_row = QHBoxLayout()
        self._logo_path = QLineEdit(self.state.logo_path)
        self._logo_path.setPlaceholderText("path/to/logo.png")
        self._logo_path.editingFinished.connect(lambda: self._set_state("logo_path", self._logo_path.text()))
        path_row.addWidget(self._logo_path, 1)
        path_row.addWidget(QLabel("Layer:"))
        self._logo_layer = QComboBox()
        self._logo_layer.addItems(["Logo 1", "Logo 2", "Logo 3"])
        path_row.addWidget(self._logo_layer)
        v.addLayout(path_row)

        coord = QHBoxLayout()
        for label, attr, lo, hi in [("X:", "logo_x", -4000, 4000),
                                    ("Y:", "logo_y", -4000, 4000),
                                    ("Scale:", "logo_scale", 1, 400)]:
            coord.addWidget(QLabel(label))
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setSuffix("%" if attr == "logo_scale" else "")
            sp.setValue(getattr(self.state, attr))
            sp.valueChanged.connect(lambda val, a=attr: self._set_state(a, val))
            coord.addWidget(sp)
        v.addLayout(coord)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity:"))
        self._logo_opacity = QSlider(Qt.Orientation.Horizontal)
        self._logo_opacity.setRange(0, 100)
        self._logo_opacity.setValue(self.state.logo_opacity)
        self._logo_opacity.valueChanged.connect(lambda v: self._set_state("logo_opacity", v))
        opacity_row.addWidget(self._logo_opacity, 1)
        self._logo_op_val = QLabel(f"{self.state.logo_opacity}%")
        self._logo_opacity.valueChanged.connect(lambda v: self._logo_op_val.setText(f"{v}%"))
        opacity_row.addWidget(self._logo_op_val)
        v.addLayout(opacity_row)

        flags_row = QHBoxLayout()
        rg = QCheckBox("Remove Green")
        rg.toggled.connect(lambda v: self._set_state("logo_remove_green", v))
        lr = QCheckBox("Loop Reverse")
        lr.toggled.connect(lambda v: self._set_state("logo_loop_reverse", v))
        flags_row.addWidget(rg)
        flags_row.addWidget(lr)
        flags_row.addStretch(1)
        v.addLayout(flags_row)

        v.addWidget(_hline())

        burn_head = QHBoxLayout()
        self._burn_cb = QCheckBox("\u270E Burn Subtitle")
        self._burn_cb.toggled.connect(lambda v: self._set_state("burn_subtitle", v))
        burn_head.addWidget(self._burn_cb)
        burn_head.addStretch(1)
        burn_head.addWidget(QLabel("BG %"))
        sub_bg = QSpinBox()
        sub_bg.setRange(0, 100)
        sub_bg.setValue(self.state.subtitle_bg_pct)
        sub_bg.valueChanged.connect(lambda v: self._set_state("subtitle_bg_pct", v))
        burn_head.addWidget(sub_bg)
        burn_head.addWidget(QLabel("AI %"))
        sub_ai = QSpinBox()
        sub_ai.setRange(0, 100)
        sub_ai.setValue(self.state.subtitle_ai_pct)
        sub_ai.valueChanged.connect(lambda v: self._set_state("subtitle_ai_pct", v))
        burn_head.addWidget(sub_ai)
        v.addLayout(burn_head)

        sub_font_row = QHBoxLayout()
        sub_font_row.addWidget(QLabel("Font:"))
        sub_font = QComboBox()
        sub_font.addItems(["Sans", "AKbalthom Ream", "Battambang", "Khmer OS"])
        sub_font.setCurrentText(self.state.subtitle_font)
        sub_font.currentTextChanged.connect(lambda v: self._set_state("subtitle_font", v))
        sub_font_row.addWidget(sub_font, 1)
        sub_font_row.addWidget(QLabel("Size:"))
        sub_size = QSpinBox()
        sub_size.setRange(6, 200)
        sub_size.setValue(self.state.subtitle_size)
        sub_size.valueChanged.connect(lambda v: self._set_state("subtitle_size", v))
        sub_font_row.addWidget(sub_size)
        v.addLayout(sub_font_row)

        sub_color_row = QHBoxLayout()
        sub_color_row.addWidget(QLabel("Color:"))
        sub_color = QLineEdit(self.state.subtitle_color)
        sub_color.setFixedWidth(80)
        sub_color.editingFinished.connect(lambda: self._set_state("subtitle_color", sub_color.text()))
        sub_color_row.addWidget(sub_color)
        sub_color_row.addWidget(QLabel("BG:"))
        self._sub_bg_btn = QPushButton("BG ON")
        self._sub_bg_btn.setCheckable(True)
        self._sub_bg_btn.setChecked(True)
        self._sub_bg_btn.setStyleSheet(button_qss("blue"))
        self._sub_bg_btn.toggled.connect(self._toggle_subtitle_bg)
        sub_color_row.addWidget(self._sub_bg_btn)
        sub_color_row.addStretch(1)
        v.addLayout(sub_color_row)

        return box

    # ----- handlers -----------------------------------------------------------
    def _on_blur_changed(self) -> None:
        self.state.blur_enabled = self._blur_cb.isChecked()
        self.state.blur_intensity = self._blur_slider.value()
        self._blur_val.setText(str(self.state.blur_intensity))
        self.state_changed.emit()

    def _on_overlay_changed(self) -> None:
        self.state.overlay_enabled = self._overlay_cb.isChecked()
        self.state.overlay_text = self._overlay_text.toPlainText()
        self.state_changed.emit()

    def _on_logo_changed(self, v: bool) -> None:
        self.state.logo_enabled = v
        self.state_changed.emit()

    def _toggle_overlay_bg(self, on: bool) -> None:
        self.state.overlay_bg_on = on
        self._overlay_bg_btn.setText("BG ON" if on else "BG OFF")
        self.state_changed.emit()

    def _toggle_subtitle_bg(self, on: bool) -> None:
        self.state.subtitle_bg_on = on
        self._sub_bg_btn.setText("BG ON" if on else "BG OFF")
        self.state_changed.emit()

    def _set_state(self, attr: str, value) -> None:
        setattr(self.state, attr, value)
        self.state_changed.emit()


def _hline() -> QWidget:
    w = QWidget()
    w.setFixedHeight(1)
    w.setStyleSheet(f"background: {BORDER};")
    return w


# silence unused-import warnings for QColor (kept for future paint helpers)
_ = QColor
