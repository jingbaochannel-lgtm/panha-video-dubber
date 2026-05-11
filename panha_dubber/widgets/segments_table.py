"""Segments / subtitle-row table with per-row controls.

Columns mirror the reference screenshot:
  Start | End | Text (editable) | Pitch | Speed | Vol(dB) | Voice | Play/Stop | Audio | Download | ECO
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ..services.srt import SrtCue
from ..theme import button_qss

COLUMNS = [
    "Start", "End", "Text (Editable)",
    "Pitch", "Speed", "Vol(dB)",
    "Voice", "Play/Stop", "Audio", "Download", "ECO",
]


def _fmt_ms(ms: int) -> str:
    if ms < 0:
        ms = 0
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


class SegmentsTable(QTableWidget):
    play_row_clicked = pyqtSignal(int)
    download_row_clicked = pyqtSignal(int)

    DEFAULT_VOICES = [
        "Sreymom (Khmer)",
        "Sopheap (Khmer M)",
        "Channary (Khmer F)",
        "en-US-Female",
        "en-US-Male",
        "en-GB-Female",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        header = self.horizontalHeader()
        for col in range(len(COLUMNS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        widths = {0: 100, 1: 100, 3: 60, 4: 60, 5: 70, 6: 160, 7: 90, 8: 100, 9: 100, 10: 60}
        for c, w in widths.items():
            self.setColumnWidth(c, w)

        self.verticalHeader().setDefaultSectionSize(32)

    # ----- public API ---------------------------------------------------------
    def load_cues(self, cues: list[SrtCue]) -> None:
        self.setRowCount(0)
        for c in cues:
            self.append_cue(c)

    def append_cue(self, cue: SrtCue) -> int:
        row = self.rowCount()
        self.insertRow(row)

        start_item = QTableWidgetItem(_fmt_ms(cue.start_ms))
        end_item = QTableWidgetItem(_fmt_ms(cue.end_ms))
        text_item = QTableWidgetItem(cue.text)
        for it in (start_item, end_item, text_item):
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 0, start_item)
        self.setItem(row, 1, end_item)
        self.setItem(row, 2, text_item)

        pitch = QDoubleSpinBox()
        pitch.setRange(-12.0, 12.0)
        pitch.setSingleStep(0.5)
        pitch.setValue(0.0)
        self.setCellWidget(row, 3, pitch)

        speed = QDoubleSpinBox()
        speed.setRange(0.5, 2.0)
        speed.setSingleStep(0.05)
        speed.setValue(1.0)
        self.setCellWidget(row, 4, speed)

        vol = QSpinBox()
        vol.setRange(-30, 12)
        vol.setValue(0)
        self.setCellWidget(row, 5, vol)

        voice = QComboBox()
        voice.addItems(self.DEFAULT_VOICES)
        self.setCellWidget(row, 6, voice)

        play_btn = QPushButton("\u25b6")
        play_btn.setStyleSheet(button_qss("green"))
        play_btn.clicked.connect(lambda _=False, r=row: self.play_row_clicked.emit(r))
        self.setCellWidget(row, 7, play_btn)

        audio_item = QTableWidgetItem("\u2014")
        audio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_item.setFlags(audio_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, 8, audio_item)

        dl_btn = QPushButton("\u2b07")
        dl_btn.setStyleSheet(button_qss("blue"))
        dl_btn.clicked.connect(lambda _=False, r=row: self.download_row_clicked.emit(r))
        self.setCellWidget(row, 9, dl_btn)

        eco_holder = QWidget()
        eco_layout = QHBoxLayout(eco_holder)
        eco_layout.setContentsMargins(0, 0, 0, 0)
        eco_layout.addStretch(1)
        cb = QCheckBox()
        cb.setChecked(True)
        eco_layout.addWidget(cb)
        eco_layout.addStretch(1)
        self.setCellWidget(row, 10, eco_holder)

        return row

    def to_cues(self) -> list[SrtCue]:
        cues: list[SrtCue] = []
        for row in range(self.rowCount()):
            start = self._read_time(row, 0)
            end = self._read_time(row, 1)
            text_item = self.item(row, 2)
            text = text_item.text() if text_item else ""
            cues.append(SrtCue(index=row + 1, start_ms=start, end_ms=end, text=text))
        return cues

    # ----- internals ----------------------------------------------------------
    def _read_time(self, row: int, col: int) -> int:
        item = self.item(row, col)
        if not item:
            return 0
        return _parse_time(item.text())


def _parse_time(s: str) -> int:
    s = s.strip().replace(",", ".")
    if not s:
        return 0
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            sec = float(parts[2])
        elif len(parts) == 2:
            h = 0
            m = int(parts[0])
            sec = float(parts[1])
        else:
            h = 0
            m = 0
            sec = float(parts[0])
        return int(((h * 60 + m) * 60 + sec) * 1000)
    except ValueError:
        return 0
