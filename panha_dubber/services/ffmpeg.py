"""Thin ffmpeg wrappers for the operations the UI exposes.

We shell out to the `ffmpeg` binary rather than depending on a Python ffmpeg
binding, so the only runtime requirement is a working ffmpeg on PATH.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FfmpegNotFoundError(RuntimeError):
    pass


def ensure_ffmpeg(binary: str = "ffmpeg") -> str:
    """Return an absolute path to a usable ffmpeg binary or raise."""
    path = shutil.which(binary)
    if not path:
        raise FfmpegNotFoundError(
            f"ffmpeg binary {binary!r} not found on PATH. Install ffmpeg or set the path in Settings."
        )
    return path


def extract_audio_to_mp3(
    video_path: str | Path,
    out_path: str | Path,
    *,
    bitrate: str = "192k",
    ffmpeg: str = "ffmpeg",
) -> Path:
    """Extract audio track from `video_path` and encode it to an MP3 at `out_path`."""
    ffmpeg = ensure_ffmpeg(ffmpeg)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", bitrate,
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def burn_subtitles(
    video_path: str | Path,
    srt_path: str | Path,
    out_path: str | Path,
    *,
    font_name: str = "Sans",
    font_size: int = 18,
    primary_color: str = "&H00FFFFFF",
    outline_color: str = "&H80000000",
    ffmpeg: str = "ffmpeg",
) -> Path:
    """Burn an SRT into a video using ffmpeg's libass-backed `subtitles=` filter."""
    ffmpeg = ensure_ffmpeg(ffmpeg)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    style = (
        f"FontName={font_name},FontSize={font_size},"
        f"PrimaryColour={primary_color},OutlineColour={outline_color},BorderStyle=1,Outline=1,Shadow=0"
    )
    # ffmpeg's subtitles filter requires path escaping: backslashes and colons.
    escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:")
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vf", f"subtitles='{escaped}':force_style='{style}'",
        "-c:a", "copy",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def render_video_with_overlay(
    video_path: str | Path,
    out_path: str | Path,
    *,
    text_overlay: str | None = None,
    overlay_font_size: int = 28,
    ffmpeg: str = "ffmpeg",
) -> Path:
    """Re-encode the video, optionally drawing a text overlay in the top-left corner."""
    ffmpeg = ensure_ffmpeg(ffmpeg)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg, "-y", "-i", str(video_path)]
    if text_overlay:
        # The single quotes around the text are intentional — ffmpeg drawtext requires them.
        safe = text_overlay.replace("'", "\\'").replace(":", "\\:")
        cmd += [
            "-vf",
            f"drawtext=text='{safe}':fontcolor=white:fontsize={overlay_font_size}:x=20:y=20:"
            f"box=1:boxcolor=black@0.5:boxborderw=8",
        ]
    cmd += ["-c:a", "copy", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def probe_duration_ms(video_path: str | Path, *, ffprobe: str = "ffprobe") -> int | None:
    """Return media duration in milliseconds, or None if ffprobe is missing/fails."""
    if not shutil.which(ffprobe):
        return None
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            check=True, capture_output=True, text=True,
        )
        seconds = float(result.stdout.strip() or 0)
        return int(seconds * 1000)
    except (subprocess.CalledProcessError, ValueError):
        return None
