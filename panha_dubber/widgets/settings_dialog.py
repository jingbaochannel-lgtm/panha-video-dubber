"""Modal settings dialog backed by the persisted Settings dataclass."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self._settings = settings

        form = QFormLayout()

        self._whisper_model = QComboBox()
        self._whisper_model.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self._whisper_model.setCurrentText(settings.whisper_model)
        form.addRow("Whisper model:", self._whisper_model)

        self._whisper_device = QComboBox()
        self._whisper_device.addItems(["cpu", "cuda", "mps"])
        self._whisper_device.setCurrentText(settings.whisper_device)
        form.addRow("Whisper device:", self._whisper_device)

        self._source_lang = QLineEdit(settings.source_language)
        form.addRow("Source language (auto / en / km / ...):", self._source_lang)

        self._target_lang = QLineEdit(settings.target_language)
        form.addRow("Target language:", self._target_lang)

        self._deepl = QLineEdit(settings.deepl_api_key)
        self._deepl.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("DeepL API key:", self._deepl)

        self._elevenlabs = QLineEdit(settings.elevenlabs_api_key)
        self._elevenlabs.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("ElevenLabs API key:", self._elevenlabs)

        self._openai = QLineEdit(settings.openai_api_key)
        self._openai.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("OpenAI API key:", self._openai)

        self._ffmpeg = QLineEdit(settings.ffmpeg_path)
        form.addRow("ffmpeg binary:", self._ffmpeg)

        out_row = QHBoxLayout()
        self._out_dir = QLineEdit(settings.output_dir)
        browse = QPushButton("Browse\u2026")
        browse.clicked.connect(self._browse_output)
        out_row.addWidget(self._out_dir, 1)
        out_row.addWidget(browse)
        out_wrap = QWidget()
        out_wrap.setLayout(out_row)
        form.addRow("Output directory:", out_wrap)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose output directory", self._out_dir.text())
        if path:
            self._out_dir.setText(path)

    def _save(self) -> None:
        s = self._settings
        s.whisper_model = self._whisper_model.currentText()
        s.whisper_device = self._whisper_device.currentText()
        s.source_language = self._source_lang.text().strip() or "auto"
        s.target_language = self._target_lang.text().strip() or "en"
        s.deepl_api_key = self._deepl.text()
        s.elevenlabs_api_key = self._elevenlabs.text()
        s.openai_api_key = self._openai.text()
        s.ffmpeg_path = self._ffmpeg.text().strip() or "ffmpeg"
        s.output_dir = self._out_dir.text().strip() or s.output_dir
        s.save()
        self.accept()
