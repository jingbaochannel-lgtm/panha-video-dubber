# Panha Video Dubber 2026

A PyQt6 desktop app for AI-powered video dubbing — Whisper transcription, per-segment voice editing, subtitle burning, and video export. Inspired by the AI Dubber Ultimate workflow but written from scratch in Python.

> Status: **v0.1 — UI shell + working core pipeline.** Whisper transcription, MP3 extraction, SRT import/export, subtitle burning and video re-encoding are wired through ffmpeg. Voice cloning (RVC / VoxCPM), translation, and the DeepInfra Whisper API path are stubbed and surface their credential requirements in Settings.

## Features

| Area | What works today | Needs API key / future work |
|---|---|---|
| Load Video | Native file dialog, QtMultimedia preview, recent-files list | — |
| Batch Load | Pick multiple files, queue in recent list | Batch processing pipeline |
| Vid → MP3 | ffmpeg audio extraction (libmp3lame, 192 kbps) | — |
| Transcribe | Local `openai-whisper` (tiny / base / small / medium / large-v3) | DeepInfra Whisper API |
| Detect Gender | — | pyannote / Resemblyzer |
| Translate | — | DeepL / OpenAI |
| Voice / RVC / VoxCPM2 | UI dropdowns | RVC / VoxCPM2 hooks |
| Video Downloader | yt-dlp shell-out | — |
| Settings | Persisted JSON in user config dir | — |
| Timeline editor | Zoomable cue strip, voice apply-to-all | Drag-to-retime |
| Video Effects | Blur, Text Overlay, Logo, Burn Subtitle parameters | Real-time preview |
| Import / Export SRT | Round-trips SRT files | — |
| Export Video | ffmpeg subtitle burn / text overlay / re-encode | Frame-accurate overlay timing |

## Requirements

- Python 3.10 +
- [ffmpeg](https://ffmpeg.org/) on PATH (the app shells out for media work)
- Optional: `openai-whisper` for local transcription, `yt-dlp` for the downloader

## Install

```bash
# clone
git clone https://github.com/jingbaochannel-lgtm/panha-video-dubber.git
cd panha-video-dubber

# pick one:
pip install -r requirements.txt          # everything
pip install -e .                         # core (PyQt6 + pysrt)
pip install -e ".[ai,downloader]"        # + whisper + yt-dlp
```

## Run

```bash
python main.py
# or, after `pip install -e .`:
panha-dubber
```

## Project layout

```
panha-video-dubber/
├── main.py                          # CLI entrypoint
├── panha_dubber/
│   ├── app.py                       # QApplication boot
│   ├── main_window.py               # wires panels together, owns workflow
│   ├── settings.py                  # persisted JSON settings
│   ├── theme.py                     # dark palette + button styles
│   ├── services/
│   │   ├── ffmpeg.py                # extract_audio_to_mp3, burn_subtitles, render
│   │   ├── whisper.py               # lazy openai-whisper wrapper
│   │   └── srt.py                   # tiny dep-free SRT reader/writer
│   └── widgets/
│       ├── video_preview.py
│       ├── tools_panel.py
│       ├── toolbar.py
│       ├── segments_table.py
│       ├── timeline.py
│       ├── effects_panel.py
│       ├── export_bar.py
│       └── settings_dialog.py
└── pyproject.toml
```

## Settings file

Persisted at:

- Linux: `~/.config/panha-video-dubber/settings.json`
- macOS: `~/Library/Application Support/panha-video-dubber/settings.json`
- Windows: `%APPDATA%/panha-video-dubber/settings.json`

API keys (DeepL, ElevenLabs, OpenAI) are stored in plaintext in this file — protect it accordingly.

## Roadmap

- Drag-to-retime in the timeline strip
- Per-row TTS preview (Voice + Pitch + Speed + Vol)
- RVC voice conversion service
- VoxCPM2 backend
- Khmer / English ASR with custom prompts
- Batch render queue UI

## License

MIT
