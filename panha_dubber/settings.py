"""User-settings persistence (JSON file under platform config dir)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def _config_dir() -> Path:
    """Return a writable config directory for the app on the current platform."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif "darwin" in os.sys.platform:  # type: ignore[attr-defined]
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / "panha-video-dubber"
    d.mkdir(parents=True, exist_ok=True)
    return d


SETTINGS_FILE = _config_dir() / "settings.json"


@dataclass
class Settings:
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    default_voice: str = "Sreymom (Khmer)"
    target_language: str = "en"
    source_language: str = "auto"
    deepl_api_key: str = ""
    elevenlabs_api_key: str = ""
    openai_api_key: str = ""
    ffmpeg_path: str = "ffmpeg"
    auto_remove_vocal: bool = True
    auto_sync_video_speed: bool = True
    lock_speed_plus_25: bool = True
    auto_detect_gender: bool = False
    output_dir: str = str(Path.home() / "PanhaDubber")
    recent_files: list[str] = field(default_factory=list)

    # --- persistence ------------------------------------------------------
    @classmethod
    def load(cls) -> Settings:
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                allowed = {f for f in cls.__dataclass_fields__}
                return cls(**{k: v for k, v in data.items() if k in allowed})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        SETTINGS_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def touch_recent(self, path: str, limit: int = 10) -> None:
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:limit]
