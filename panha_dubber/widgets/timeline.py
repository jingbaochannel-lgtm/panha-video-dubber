"""Timeline editor section — zoomable cue strip + voice/echo controls."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..services.srt import SrtCue
from ..theme import ACCENT, BG_INPUT, BG_PANEL_LIGHT, BORDER, TEXT, TEXT_DIM, button_qss


class TimelineStrip(QWidget):
    """Read-only horizontal strip showing cues against the media duration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._duration_ms: int = 60_000
        self._cues: list[SrtCue] = []
        self._zoom: float = 1.0
        self._playhead_ms: int = 0
        self.setMinimumHeight(150)
        self.setStyleSheet(f"background: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 4px;")
        self._update_width()

    # ----- public API ---------------------------------------------------------
    def set_duration_ms(self, ms: int) -> None:
        self._duration_ms = max(1000, int(ms))
        self._update_width()
        self.update()

    def set_cues(self, cues: list[SrtCue]) -> None:
        self._cues = list(cues)
        if cues:
            self._duration_ms = max(self._duration_ms, cues[-1].end_ms + 1000)
        self._update_width()
        self.update()

    def set_zoom(self, zoom_pct: int) -> None:
        # zoom_pct 1..100 → 0.5x..4x
        z = max(1, min(100, zoom_pct)) / 100.0
        self._zoom = 0.5 + z * 3.5
        self._update_width()
        self.update()

    def set_playhead_ms(self, ms: int) -> None:
        self._playhead_ms = max(0, min(self._duration_ms, ms))
        self.update()

    # ----- internals ----------------------------------------------------------
    def _update_width(self) -> None:
        # 1 second = 30 px at zoom 1.0
        secs = self._duration_ms / 1000.0
        width = int(max(600, secs * 30 * self._zoom))
        self.setMinimumWidth(width)

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()

        # ruler at the top
        ruler_h = 22
        painter.fillRect(0, 0, rect.width(), ruler_h, QColor(BG_PANEL_LIGHT))
        painter.setPen(QPen(QColor(TEXT_DIM)))
        secs = self._duration_ms / 1000.0
        px_per_sec = rect.width() / max(secs, 1)
        # tick every 1s, label every 5s
        s = 0
        while s <= secs:
            x = int(s * px_per_sec)
            tall = (s % 5 == 0)
            painter.drawLine(x, ruler_h - (10 if tall else 5), x, ruler_h)
            if tall:
                painter.drawText(x + 3, ruler_h - 6, _fmt_secs(s))
            s += 1

        # cue lanes
        lane_y = ruler_h + 8
        lane_h = 22
        for i, cue in enumerate(self._cues):
            x1 = int(cue.start_ms / 1000.0 * px_per_sec)
            x2 = int(cue.end_ms / 1000.0 * px_per_sec)
            y = lane_y + (i % 3) * (lane_h + 4)
            cue_rect = QRectF(x1, y, max(2, x2 - x1), lane_h)
            painter.setBrush(QBrush(QColor(ACCENT)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(cue_rect, 4, 4)
            painter.setPen(QPen(QColor(TEXT)))
            label = cue.text.split("\n", 1)[0][:48]
            painter.drawText(cue_rect.adjusted(6, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter, label)

        # playhead
        if self._duration_ms:
            ph_x = int(self._playhead_ms / self._duration_ms * rect.width())
            painter.setPen(QPen(QColor("#ff5252"), 2))
            painter.drawLine(ph_x, 0, ph_x, rect.height())


def _fmt_secs(s: int) -> str:
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"


class TimelineEditor(QGroupBox):
    align_to_playhead_clicked = pyqtSignal()
    apply_voice_to_all_clicked = pyqtSignal(str)
    voice_clone_clicked = pyqtSignal()
    echo_all_rows_clicked = pyqtSignal(int)  # echo intensity %

    def __init__(self, voices: list[str], parent: QWidget | None = None) -> None:
        super().__init__("Timeline Editor (\u17a2\u17bb\u179f - \u1797\u17d2\u1787\u17b6\u1794\u17cb Timing)", parent)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Zoom:"))
        self._zoom = QSlider(Qt.Orientation.Horizontal)
        self._zoom.setRange(1, 100)
        self._zoom.setValue(25)
        self._zoom.setFixedWidth(140)
        zoom_row.addWidget(self._zoom)

        align_btn = QPushButton("\u2316 Align to Playhead")
        align_btn.setStyleSheet(button_qss("teal"))
        align_btn.clicked.connect(self.align_to_playhead_clicked.emit)
        zoom_row.addWidget(align_btn)

        zoom_row.addSpacing(10)
        zoom_row.addWidget(QLabel("\U0001F3A4 Voice:"))
        self._voice = QComboBox()
        self._voice.addItems(voices)
        self._voice.setMinimumWidth(180)
        zoom_row.addWidget(self._voice)

        apply_btn = QPushButton("\u2713 Apply to All")
        apply_btn.setStyleSheet(button_qss("blue"))
        apply_btn.clicked.connect(lambda: self.apply_voice_to_all_clicked.emit(self._voice.currentText()))
        zoom_row.addWidget(apply_btn)

        clone_btn = QPushButton("\u00b7 Clone Voice")
        clone_btn.setStyleSheet(button_qss("blue"))
        clone_btn.clicked.connect(self.voice_clone_clicked.emit)
        zoom_row.addWidget(clone_btn)

        zoom_row.addSpacing(10)
        zoom_row.addWidget(QLabel("\U0001F50A Echo Intensity:"))
        self._echo = QSpinBox()
        self._echo.setRange(0, 100)
        self._echo.setValue(50)
        self._echo.setSuffix("%")
        zoom_row.addWidget(self._echo)

        echo_btn = QPushButton("\u2728 Echo All Rows")
        echo_btn.setStyleSheet(button_qss("purple"))
        echo_btn.clicked.connect(lambda: self.echo_all_rows_clicked.emit(self._echo.value()))
        zoom_row.addWidget(echo_btn)
        zoom_row.addStretch(1)

        self.strip = TimelineStrip()
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setWidget(self.strip)
        scroll.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.addLayout(zoom_row)
        layout.addWidget(scroll, 1)

        self._zoom.valueChanged.connect(self.strip.set_zoom)
