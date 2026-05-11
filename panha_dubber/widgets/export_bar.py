"""Bottom-row export bar: Import SRT, Export SRT, Export MP3, Export Video, Cancel, CapCut."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..theme import button_qss


class ExportBar(QWidget):
    import_srt = pyqtSignal()
    export_srt = pyqtSignal()
    export_mp3 = pyqtSignal()
    export_video = pyqtSignal()
    cancel_export = pyqtSignal()
    capcut = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        def btn(label: str, role: str, signal) -> QPushButton:
            b = QPushButton(label)
            b.setStyleSheet(button_qss(role))
            b.clicked.connect(signal.emit)
            return b

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(btn("\u2935 Import SRT", "slate", self.import_srt))
        layout.addWidget(btn("\u2934 Export SRT", "teal", self.export_srt))
        layout.addStretch(1)
        layout.addWidget(btn("\U0001F3B5 Export MP3", "orange", self.export_mp3))
        layout.addWidget(btn("\U0001F3AC Export Video", "green", self.export_video))
        layout.addWidget(btn("\u2715 Cancel Export", "red", self.cancel_export))
        layout.addWidget(btn("CapCut", "pink", self.capcut))
