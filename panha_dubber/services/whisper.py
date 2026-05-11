"""Whisper transcription wrapper.

The `openai-whisper` package is large and optional, so we import it lazily and
fall back to a stub implementation when it isn't installed. The stub still
produces a single placeholder cue so the rest of the pipeline (table, SRT
export, subtitle burn) can be exercised end-to-end.
"""
from __future__ import annotations

from pathlib import Path

from .srt import SrtCue


class WhisperUnavailable(RuntimeError):
    """Raised when openai-whisper isn't installed."""


def is_available() -> bool:
    try:
        import whisper  # noqa: F401  (presence check)
    except ImportError:
        return False
    return True


def transcribe(
    media_path: str | Path,
    *,
    model_name: str = "small",
    device: str = "cpu",
    language: str | None = None,
) -> list[SrtCue]:
    """Run whisper on `media_path` and return SrtCue rows.

    Raises WhisperUnavailable if the optional dependency isn't installed.
    """
    try:
        import whisper
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise WhisperUnavailable(
            "openai-whisper is not installed. Install with: pip install openai-whisper"
        ) from exc

    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(str(media_path), language=language, verbose=False)

    cues: list[SrtCue] = []
    for i, seg in enumerate(result.get("segments", []), 1):
        cues.append(
            SrtCue(
                index=i,
                start_ms=int(seg["start"] * 1000),
                end_ms=int(seg["end"] * 1000),
                text=seg["text"].strip(),
            )
        )
    return cues
