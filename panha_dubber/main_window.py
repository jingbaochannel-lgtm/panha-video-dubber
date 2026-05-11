"""Top-level QMainWindow that stitches all the panels together."""
from __future__ import annotations

import os
import subprocess
import threading
import traceback
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__
from .services import ffmpeg as ffmpeg_svc
from .services import whisper as whisper_svc
from .services.srt import SrtCue, load_srt, save_srt
from .settings import Settings
from .theme import TEXT_DIM, app_qss
from .widgets.effects_panel import EffectsPanel
from .widgets.export_bar import ExportBar
from .widgets.segments_table import SegmentsTable
from .widgets.settings_dialog import SettingsDialog
from .widgets.timeline import TimelineEditor
from .widgets.toolbar import ActionToolbar
from .widgets.tools_panel import ToolsPanel
from .widgets.video_preview import VideoPreview


# ---------------------------------------------------------------------------- #
# Background worker for long-running ffmpeg / whisper calls
# ---------------------------------------------------------------------------- #
class _Job(QObject):
    finished = pyqtSignal(object)  # result
    failed = pyqtSignal(str)        # traceback string

    def __init__(self, fn, *args, **kwargs) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception:  # noqa: BLE001 — surface any failure to UI
            self.failed.emit(traceback.format_exc())
        else:
            self.finished.emit(result)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.load()
        self._current_video: str | None = None
        self._jobs: list[tuple[QThread, _Job]] = []  # keep refs alive

        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        # Default to a comfortable size on FHD-and-up displays; shrink if the screen is smaller.
        screen = self.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            self.resize(min(1500, avail.width() - 40), min(920, avail.height() - 80))
        else:
            self.resize(1280, 800)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(app_qss())

        # ----- left column ----------------------------------------------------
        self.video_preview = VideoPreview()
        self.tools_panel = ToolsPanel(self.settings)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.video_preview, 3)
        left_layout.addWidget(self.tools_panel, 2)

        # ----- right column ---------------------------------------------------
        title = QLabel(f"\U0001F3AC  {APP_NAME}  \u2014  Ultimate Edition")
        title.setStyleSheet("font-size: 16px; font-weight: 700; padding: 2px 6px;")
        title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.toolbar = ActionToolbar()
        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(self.toolbar, 1)
        toolbar_row.addWidget(title, 0)

        self.segments = SegmentsTable()
        self.timeline = TimelineEditor(voices=SegmentsTable.DEFAULT_VOICES)
        self.effects = EffectsPanel()
        self.export_bar = ExportBar()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addLayout(toolbar_row)
        right_layout.addWidget(self.segments, 3)
        right_layout.addWidget(self.timeline, 2)
        right_layout.addWidget(self.effects, 2)
        right_layout.addWidget(self.export_bar, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, max(700, self.width() - 320)])

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(10, 10, 10, 10)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

        self._status = QStatusBar()
        self._status.setStyleSheet(f"color: {TEXT_DIM};")
        self.setStatusBar(self._status)
        self._set_status("Ready.")

        # ----- wire signals ---------------------------------------------------
        self._wire_signals()

    # ----- signal wiring ------------------------------------------------------
    def _wire_signals(self) -> None:
        self.toolbar.load_video.connect(self.on_load_video)
        self.toolbar.batch_load.connect(self.on_batch_load)
        self.toolbar.transcribe.connect(self.on_transcribe)
        self.toolbar.vid_to_mp3.connect(self.on_vid_to_mp3)
        self.toolbar.detect_gender.connect(lambda: self._not_implemented("Detect Gender"))
        self.toolbar.translate.connect(lambda: self._not_implemented("Translate (DeepL / OpenAI)"))
        self.toolbar.open_settings.connect(self.on_open_settings)
        self.toolbar.open_downloader.connect(self.on_open_downloader)
        self.toolbar.open_chrome_manager.connect(lambda: self._not_implemented("Chrome manager"))
        self.toolbar.open_rvc.connect(lambda: self._not_implemented("RVC voice conversion"))
        self.toolbar.open_voxcpm.connect(lambda: self._not_implemented("VoxCPM2"))

        self.segments.play_row_clicked.connect(self._on_play_row)
        self.timeline.align_to_playhead_clicked.connect(lambda: self._not_implemented("Align to Playhead"))
        self.timeline.apply_voice_to_all_clicked.connect(self._apply_voice_to_all)
        self.timeline.echo_all_rows_clicked.connect(lambda pct: self._set_status(f"Echo intensity set to {pct}% (queued)."))
        self.timeline.voice_clone_clicked.connect(lambda: self._not_implemented("Voice Clone"))

        self.tools_panel.auto_sync_clicked.connect(lambda: self._not_implemented("Auto-Sync"))
        self.tools_panel.auto_speed_clicked.connect(lambda: self._not_implemented("Auto-Speed"))
        self.tools_panel.video_sync_clicked.connect(lambda: self._not_implemented("Video Sync"))
        self.tools_panel.cutter_clicked.connect(lambda: self._not_implemented("Cutter"))

        self.effects.apply_effects_clicked.connect(lambda: self._set_status("Effects state saved (apply on Export Video)."))

        self.export_bar.import_srt.connect(self.on_import_srt)
        self.export_bar.export_srt.connect(self.on_export_srt)
        self.export_bar.export_mp3.connect(self.on_vid_to_mp3)
        self.export_bar.export_video.connect(self.on_export_video)
        self.export_bar.cancel_export.connect(self._on_cancel_export)
        self.export_bar.capcut.connect(lambda: self._not_implemented("Open in CapCut"))

    # ----- handlers -----------------------------------------------------------
    def on_load_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Video", str(Path.home()),
            "Videos (*.mp4 *.mov *.mkv *.webm *.avi);;All files (*)",
        )
        if not path:
            return
        self._current_video = path
        self.video_preview.load_file(path)
        self.settings.touch_recent(path)
        self.settings.save()
        dur_ms = ffmpeg_svc.probe_duration_ms(path) or 0
        if dur_ms:
            self.timeline.strip.set_duration_ms(dur_ms)
        self._set_status(f"Loaded: {Path(path).name}")

    def on_batch_load(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Batch Load Videos", str(Path.home()),
            "Videos (*.mp4 *.mov *.mkv *.webm *.avi);;All files (*)",
        )
        if not paths:
            return
        for p in paths:
            self.settings.touch_recent(p)
        self.settings.save()
        self._current_video = paths[0]
        self.video_preview.load_file(paths[0])
        self._set_status(f"Batch-loaded {len(paths)} file(s); previewing first.")

    def on_transcribe(self) -> None:
        if not self._current_video:
            self._warn("Load a video first.")
            return
        model_label = self.toolbar.current_model()
        if model_label.startswith("DeepInfra"):
            self._not_implemented(f"{model_label} (requires DeepInfra API key in Settings)")
            return
        model_name = model_label.split("—")[-1].strip()
        if not whisper_svc.is_available():
            QMessageBox.information(
                self, "Whisper not installed",
                "openai-whisper is not installed in this environment.\n\n"
                "Install with:\n  pip install openai-whisper\n\n"
                "Until then, use 'Import SRT' to load an existing transcript.",
            )
            return
        self._set_status(f"Transcribing with {model_name}\u2026 this can take a while.")
        self._run_async(
            whisper_svc.transcribe,
            self._current_video,
            model_name=model_name,
            device=self.settings.whisper_device,
            language=None if self.settings.source_language in ("", "auto") else self.settings.source_language,
            on_done=self._on_transcribe_done,
        )

    def _on_transcribe_done(self, cues: list[SrtCue]) -> None:
        self.segments.load_cues(cues)
        self.timeline.strip.set_cues(cues)
        self._set_status(f"Transcribed {len(cues)} segments.")

    def on_vid_to_mp3(self) -> None:
        if not self._current_video:
            self._warn("Load a video first.")
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export MP3", str(Path(self.settings.output_dir) / (Path(self._current_video).stem + ".mp3")),
            "MP3 (*.mp3)",
        )
        if not out_path:
            return
        self._set_status(f"Extracting MP3 \u2192 {out_path}\u2026")
        self._run_async(
            ffmpeg_svc.extract_audio_to_mp3,
            self._current_video, out_path,
            ffmpeg=self.settings.ffmpeg_path,
            on_done=lambda p: self._set_status(f"MP3 saved: {p}"),
        )

    def on_import_srt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import SRT", str(Path.home()),
            "Subtitle files (*.srt);;All files (*)",
        )
        if not path:
            return
        try:
            cues = load_srt(path)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"Could not parse SRT:\n{exc}")
            return
        self.segments.load_cues(cues)
        self.timeline.strip.set_cues(cues)
        self._set_status(f"Imported {len(cues)} cues from {Path(path).name}")

    def on_export_srt(self) -> None:
        cues = self.segments.to_cues()
        if not cues:
            self._warn("Nothing to export — the segments table is empty.")
            return
        suggested = "transcript.srt"
        if self._current_video:
            suggested = str(Path(self.settings.output_dir) / (Path(self._current_video).stem + ".srt"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Export SRT", suggested, "SubRip (*.srt)",
        )
        if not path:
            return
        save_srt(path, cues)
        self._set_status(f"SRT saved: {path}")

    def on_export_video(self) -> None:
        if not self._current_video:
            self._warn("Load a video first.")
            return
        cues = self.segments.to_cues()
        burn = self.effects.state.burn_subtitle and bool(cues)

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export Video",
            str(Path(self.settings.output_dir) / (Path(self._current_video).stem + ".export.mp4")),
            "MP4 video (*.mp4)",
        )
        if not out_path:
            return

        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)

        if burn:
            srt_tmp = Path(self.settings.output_dir) / (Path(self._current_video).stem + ".tmp.srt")
            save_srt(srt_tmp, cues)
            self._set_status("Burning subtitles into video\u2026")
            self._run_async(
                ffmpeg_svc.burn_subtitles,
                self._current_video, srt_tmp, out_path,
                font_name=self.effects.state.subtitle_font,
                font_size=self.effects.state.subtitle_size,
                ffmpeg=self.settings.ffmpeg_path,
                on_done=lambda p: self._set_status(f"Video exported: {p}"),
            )
        elif self.effects.state.overlay_enabled:
            self._set_status("Rendering with text overlay\u2026")
            self._run_async(
                ffmpeg_svc.render_video_with_overlay,
                self._current_video, out_path,
                text_overlay=self.effects.state.overlay_text,
                overlay_font_size=self.effects.state.overlay_size,
                ffmpeg=self.settings.ffmpeg_path,
                on_done=lambda p: self._set_status(f"Video exported: {p}"),
            )
        else:
            self._set_status("Re-encoding video\u2026")
            self._run_async(
                ffmpeg_svc.render_video_with_overlay,
                self._current_video, out_path,
                ffmpeg=self.settings.ffmpeg_path,
                on_done=lambda p: self._set_status(f"Video exported: {p}"),
            )

    def on_open_settings(self) -> None:
        if SettingsDialog(self.settings, self).exec():
            self._set_status("Settings saved.")

    def on_open_downloader(self) -> None:
        url, ok = _input_text(self, "Video Downloader", "Paste a YouTube / TikTok / FB URL:")
        if not ok or not url.strip():
            return
        if not _has_binary("yt-dlp"):
            QMessageBox.information(
                self, "yt-dlp not installed",
                "yt-dlp is not installed. Install with:\n  pip install yt-dlp\n\n"
                "After installing it'll show up here automatically.",
            )
            return
        out_dir = Path(self.settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self._set_status(f"Downloading {url}\u2026")
        threading.Thread(
            target=self._download_url,
            args=(url.strip(), str(out_dir)),
            daemon=True,
        ).start()

    def _download_url(self, url: str, out_dir: str) -> None:
        try:
            subprocess.run(
                ["yt-dlp", "-o", os.path.join(out_dir, "%(title)s.%(ext)s"), url],
                check=True,
            )
            self._set_status(f"Download complete \u2192 {out_dir}")
        except subprocess.CalledProcessError as exc:
            self._set_status(f"Download failed: {exc}")

    # ----- helpers ------------------------------------------------------------
    def _on_play_row(self, _row: int) -> None:
        # Future: scrub video preview to cue start_ms.
        self._set_status("Per-row preview is on the roadmap.")

    def _apply_voice_to_all(self, voice: str) -> None:
        for row in range(self.segments.rowCount()):
            combo = self.segments.cellWidget(row, 6)
            if combo is not None and hasattr(combo, "setCurrentText"):
                combo.setCurrentText(voice)
        self._set_status(f"Applied voice '{voice}' to {self.segments.rowCount()} row(s).")

    def _on_cancel_export(self) -> None:
        self._set_status("Cancel requested (jobs cannot be aborted mid-ffmpeg in this build).")

    def _not_implemented(self, name: str) -> None:
        QMessageBox.information(
            self, "Coming soon",
            f"{name} isn't wired up in this build.\n\n"
            "Add the relevant API key in Settings and this action will become available.",
        )

    def _warn(self, msg: str) -> None:
        QMessageBox.warning(self, APP_NAME, msg)

    def _set_status(self, msg: str) -> None:
        self._status.showMessage(msg)

    def _run_async(self, fn, *args, on_done=None, **kwargs) -> None:
        thread = QThread(self)
        job = _Job(fn, *args, **kwargs)
        job.moveToThread(thread)
        thread.started.connect(job.run)

        def cleanup(result=None, error: str | None = None) -> None:
            thread.quit()
            thread.wait(100)
            if error:
                QMessageBox.critical(self, "Task failed", error.splitlines()[-1] if error else "Unknown error")
                self._set_status("Task failed.")
            elif on_done is not None:
                try:
                    on_done(result)
                except Exception:  # noqa: BLE001
                    traceback.print_exc()

        job.finished.connect(lambda result: cleanup(result=result))
        job.failed.connect(lambda err: cleanup(error=err))
        thread.start()
        self._jobs.append((thread, job))


# ---------------------------------------------------------------------------- #
# small utilities
# ---------------------------------------------------------------------------- #
def _has_binary(name: str) -> bool:
    from shutil import which

    return which(name) is not None


def _input_text(parent: QWidget, title: str, label: str) -> tuple[str, bool]:
    from PyQt6.QtWidgets import QInputDialog

    text, ok = QInputDialog.getText(parent, title, label)
    return text, ok
