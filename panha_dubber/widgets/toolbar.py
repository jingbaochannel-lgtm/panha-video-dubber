"""The wide action toolbar above the segments table.

Buttons (left to right):
  Load Video | Batch Load | [Whisper model dropdown] | Transcribe | Vid to MP3 |
  Detect Gender | us Translate | Settings | Video Downloader | Chrome manager |
  RVC | VoxCPM2
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from ..theme import BG_INPUT, BORDER, TEXT, button_qss


class ActionToolbar(QWidget):
    load_video = pyqtSignal()
    batch_load = pyqtSignal()
    transcribe = pyqtSignal()
    vid_to_mp3 = pyqtSignal()
    detect_gender = pyqtSignal()
    translate = pyqtSignal()
    open_settings = pyqtSignal()
    open_downloader = pyqtSignal()
    open_chrome_manager = pyqtSignal()
    open_rvc = pyqtSignal()
    open_voxcpm = pyqtSignal()
    model_changed = pyqtSignal(str)

    WHISPER_MODELS = [
        "DeepInfra Whisper Large v3",
        "OpenAI Whisper (local) — tiny",
        "OpenAI Whisper (local) — base",
        "OpenAI Whisper (local) — small",
        "OpenAI Whisper (local) — medium",
        "OpenAI Whisper (local) — large-v3",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = QComboBox()
        self._model.addItems(self.WHISPER_MODELS)
        self._model.setCurrentIndex(0)
        self._model.currentTextChanged.connect(self.model_changed.emit)
        self._model.setMinimumWidth(220)
        self._model.setStyleSheet(
            f"QComboBox {{ background: {BG_INPUT}; color: {TEXT}; border: 1px solid {BORDER};"
            f" border-radius: 4px; padding: 5px 8px; }}"
        )

        def btn(label: str, role: str, signal) -> QPushButton:
            b = QPushButton(label)
            b.setStyleSheet(button_qss(role))
            b.clicked.connect(signal.emit)
            return b

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(btn("\u25b6 Load Video", "pink", self.load_video))
        layout.addWidget(btn("\U0001F4E6 Batch Load", "pink", self.batch_load))
        layout.addWidget(self._model)
        layout.addWidget(btn("\u270F Transcribe", "yellow", self.transcribe))
        layout.addWidget(btn("\U0001F3B5 Vid to MP3", "purple", self.vid_to_mp3))
        layout.addWidget(btn("\u2640 Detect Gender", "red", self.detect_gender))
        layout.addWidget(btn("us Translate", "teal", self.translate))
        layout.addWidget(btn("\u2699 Settings", "slate", self.open_settings))
        layout.addWidget(btn("Video Downloader", "slate", self.open_downloader))
        layout.addWidget(btn("Chrome manager", "slate", self.open_chrome_manager))
        layout.addWidget(btn("\u266B RVC", "blue", self.open_rvc))
        layout.addWidget(btn("VoxCPM2", "indigo", self.open_voxcpm))
        layout.addStretch(1)

    def current_model(self) -> str:
        return self._model.currentText()
