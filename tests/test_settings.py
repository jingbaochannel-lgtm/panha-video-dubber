"""Settings persistence smoke tests."""
from __future__ import annotations

import json

from panha_dubber import settings as settings_module
from panha_dubber.settings import Settings


def test_defaults_round_trip(tmp_path, monkeypatch):
    config_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", config_file)

    s = Settings()
    s.whisper_model = "medium"
    s.deepl_api_key = "secret"
    s.touch_recent("/tmp/clip.mp4")
    s.save()

    loaded = Settings.load()
    assert loaded.whisper_model == "medium"
    assert loaded.deepl_api_key == "secret"
    assert loaded.recent_files == ["/tmp/clip.mp4"]

    data = json.loads(config_file.read_text())
    assert data["whisper_model"] == "medium"


def test_recent_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "s.json")
    s = Settings()
    for i in range(15):
        s.touch_recent(f"/tmp/{i}.mp4", limit=5)
    assert len(s.recent_files) == 5
    # most-recent first
    assert s.recent_files[0] == "/tmp/14.mp4"
