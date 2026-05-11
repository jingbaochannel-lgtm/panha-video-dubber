"""Tiny SRT reader/writer that works without external deps.

Format reference: https://en.wikipedia.org/wiki/SubRip
We accept the standard `HH:MM:SS,mmm --> HH:MM:SS,mmm` time format and the
common `.` variant produced by some transcribers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})")


@dataclass
class SrtCue:
    index: int
    start_ms: int
    end_ms: int
    text: str


def _parse_timestamp(s: str) -> int:
    m = _TIME_RE.search(s)
    if not m:
        raise ValueError(f"bad timestamp: {s!r}")
    h, mi, se, ms = (int(x) for x in m.groups())
    return ((h * 60 + mi) * 60 + se) * 1000 + ms


def _format_timestamp(ms: int) -> str:
    if ms < 0:
        ms = 0
    h, ms = divmod(ms, 3_600_000)
    mi, ms = divmod(ms, 60_000)
    se, ms = divmod(ms, 1000)
    return f"{h:02d}:{mi:02d}:{se:02d},{ms:03d}"


def parse_srt(text: str) -> list[SrtCue]:
    """Parse SRT content into a list of cues. Tolerant to blank-line variance."""
    cues: list[SrtCue] = []
    # Normalize line endings, then split on blank-line boundaries.
    blocks = re.split(r"\r?\n\r?\n+", text.strip().replace("\r\n", "\n"))
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip() != ""]
        if len(lines) < 2:
            continue
        # The first line is usually the index; if it isn't a number we still try the next line.
        idx_line, time_line, *rest = lines
        if "-->" not in time_line and "-->" in idx_line:
            time_line = idx_line
            idx_line = str(len(cues) + 1)
            rest = lines[1:]
        try:
            idx = int(idx_line.strip())
        except ValueError:
            idx = len(cues) + 1
        if "-->" not in time_line:
            continue
        a, b = (p.strip() for p in time_line.split("-->", 1))
        cues.append(
            SrtCue(
                index=idx,
                start_ms=_parse_timestamp(a),
                end_ms=_parse_timestamp(b),
                text="\n".join(rest).strip(),
            )
        )
    return cues


def write_srt(cues: list[SrtCue]) -> str:
    """Render a list of cues back to SRT text."""
    out: list[str] = []
    for i, c in enumerate(cues, 1):
        out.append(str(i))
        out.append(f"{_format_timestamp(c.start_ms)} --> {_format_timestamp(c.end_ms)}")
        out.append(c.text.strip())
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def load_srt(path: str | Path) -> list[SrtCue]:
    return parse_srt(Path(path).read_text(encoding="utf-8", errors="replace"))


def save_srt(path: str | Path, cues: list[SrtCue]) -> None:
    Path(path).write_text(write_srt(cues), encoding="utf-8")
