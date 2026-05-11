"""Left-hand 'Tools' panel beneath the video preview.

Houses the four utility buttons (Auto-Sync, Auto-Speed, Video Sync, Cutter),
license badge, and the four runtime toggles (auto sync, auto detect gender,
lock speed +25%, auto remove vocal).
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..settings import Settings
from ..theme import TEXT_DIM, button_qss


class ToolsPanel(QGroupBox):
    """Tools box with quick actions and persisted runtime toggles."""

    auto_sync_clicked = pyqtSignal()
    auto_speed_clicked = pyqtSignal()
    video_sync_clicked = pyqtSignal()
    cutter_clicked = pyqtSignal()
    toggle_changed = pyqtSignal(str, bool)

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__("Tools", parent)
        self._settings = settings

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        def make_btn(label: str, role: str, signal) -> QPushButton:
            btn = QPushButton(label)
            btn.setStyleSheet(button_qss(role))
            btn.clicked.connect(signal.emit)
            return btn

        grid.addWidget(make_btn("\u21bb Auto-Sync", "red", self.auto_sync_clicked), 0, 0)
        grid.addWidget(make_btn("Auto-Speed", "orange", self.auto_speed_clicked), 0, 1)
        grid.addWidget(make_btn("Video Sync", "purple", self.video_sync_clicked), 1, 0)
        grid.addWidget(make_btn("\u2702 Cutter", "yellow", self.cutter_clicked), 1, 1)

        license_lbl = QLabel("\u221e License: Lifetime")
        license_lbl.setStyleSheet(f"color: {TEXT_DIM}; padding: 6px 2px;")

        self._cb_auto_sync = QCheckBox("Auto Sync Video Speed")
        self._cb_auto_sync.setChecked(self._settings.auto_sync_video_speed)
        self._cb_auto_sync.toggled.connect(lambda v: self._on_toggle("auto_sync_video_speed", v))

        self._cb_detect_gender = QCheckBox("Auto detect Gender")
        self._cb_detect_gender.setChecked(self._settings.auto_detect_gender)
        self._cb_detect_gender.toggled.connect(lambda v: self._on_toggle("auto_detect_gender", v))

        self._cb_lock_speed = QCheckBox("Lock Speed (+25%)")
        self._cb_lock_speed.setChecked(self._settings.lock_speed_plus_25)
        self._cb_lock_speed.toggled.connect(lambda v: self._on_toggle("lock_speed_plus_25", v))

        self._cb_remove_vocal = QCheckBox("Auto remove Vocal")
        self._cb_remove_vocal.setChecked(self._settings.auto_remove_vocal)
        self._cb_remove_vocal.toggled.connect(lambda v: self._on_toggle("auto_remove_vocal", v))

        toggles = QGridLayout()
        toggles.setVerticalSpacing(4)
        toggles.addWidget(self._cb_auto_sync, 0, 0)
        toggles.addWidget(self._cb_detect_gender, 0, 1)
        toggles.addWidget(self._cb_lock_speed, 1, 0)
        toggles.addWidget(self._cb_remove_vocal, 1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.addLayout(grid)
        layout.addWidget(license_lbl)
        layout.addLayout(toggles)
        layout.addStretch(1)

    def _on_toggle(self, name: str, value: bool) -> None:
        setattr(self._settings, name, value)
        self._settings.save()
        self.toggle_changed.emit(name, value)
