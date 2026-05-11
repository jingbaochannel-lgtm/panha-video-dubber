"""Left-hand 'Video Preview' panel: video display + play/stop + scrub time."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..theme import BG_INPUT, BORDER, TEXT, TEXT_DIM, button_qss


class VideoPreview(QGroupBox):
    """Panel showing a single-video preview with play / stop / time."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Video Preview", parent)

        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        self._video_widget = QVideoWidget(self)
        self._video_widget.setMinimumSize(220, 280)
        self._video_widget.setStyleSheet(
            f"background: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 6px;"
        )
        self._player.setVideoOutput(self._video_widget)

        self._placeholder = QLabel("No Video Loaded", self._video_widget)
        self._placeholder.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; font-size: 13px;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setGeometry(0, 0, 220, 280)

        self._play_btn = QPushButton("\u25b6 Play")
        self._play_btn.setStyleSheet(button_qss("green"))
        self._play_btn.clicked.connect(self._toggle_play)

        self._stop_btn = QPushButton("\u25a0 Stop")
        self._stop_btn.setStyleSheet(button_qss("red"))
        self._stop_btn.clicked.connect(self._stop)

        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet(f"color: {TEXT}; padding-left: 6px;")

        controls = QHBoxLayout()
        controls.addWidget(self._play_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(self._time_label, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.addWidget(self._video_widget, 1)
        layout.addLayout(controls)

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

    # ----- public API ---------------------------------------------------------
    def load_file(self, path: str) -> None:
        self._player.setSource(QUrl.fromLocalFile(path))
        self._placeholder.hide()
        self._player.play()

    # ----- internals ----------------------------------------------------------
    def _toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _stop(self) -> None:
        self._player.stop()

    def _on_position_changed(self, pos_ms: int) -> None:
        self._time_label.setText(f"{_fmt(pos_ms)} / {_fmt(self._player.duration())}")

    def _on_duration_changed(self, dur_ms: int) -> None:
        self._time_label.setText(f"{_fmt(self._player.position())} / {_fmt(dur_ms)}")

    def _on_state_changed(self, _state: QMediaPlayer.PlaybackState) -> None:
        playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self._play_btn.setText("\u2759\u2759 Pause" if playing else "\u25b6 Play")

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._placeholder.setGeometry(self._video_widget.rect())


def _fmt(ms: int) -> str:
    if ms <= 0:
        return "00:00"
    total = ms // 1000
    mm, ss = divmod(total, 60)
    if mm < 60:
        return f"{mm:02d}:{ss:02d}"
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"
