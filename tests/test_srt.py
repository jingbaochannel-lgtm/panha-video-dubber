"""Round-trip and edge-case tests for the SRT reader/writer."""
from __future__ import annotations

from panha_dubber.services.srt import SrtCue, parse_srt, write_srt

SAMPLE = """1
00:00:01,000 --> 00:00:02,500
Hello world

2
00:00:03,000 --> 00:00:04,000
Second line
with wrap
"""


def test_parse_basic():
    cues = parse_srt(SAMPLE)
    assert len(cues) == 2
    assert cues[0].start_ms == 1000
    assert cues[0].end_ms == 2500
    assert cues[0].text == "Hello world"
    assert cues[1].text == "Second line\nwith wrap"


def test_roundtrip_is_stable():
    cues = parse_srt(SAMPLE)
    out = write_srt(cues)
    again = parse_srt(out)
    assert [(c.start_ms, c.end_ms, c.text) for c in cues] == [
        (c.start_ms, c.end_ms, c.text) for c in again
    ]


def test_handles_dotted_milliseconds():
    cues = parse_srt("1\n00:00:01.250 --> 00:00:02.000\nfoo\n")
    assert cues == [SrtCue(index=1, start_ms=1250, end_ms=2000, text="foo")]


def test_pads_short_millisecond_fields():
    # `.5` is half a second (500 ms), not 5 ms; `.25` is 250 ms.
    cues = parse_srt("1\n00:00:01.5 --> 00:00:02.25\nfoo\n")
    assert cues == [SrtCue(index=1, start_ms=1500, end_ms=2250, text="foo")]


def test_write_renumbers_indices():
    cues = [
        SrtCue(index=99, start_ms=0, end_ms=1000, text="a"),
        SrtCue(index=42, start_ms=1000, end_ms=2000, text="b"),
    ]
    out = write_srt(cues)
    assert out.splitlines()[0] == "1"
    assert "2\n" in out


def test_ignores_blank_blocks():
    cues = parse_srt("\n\n1\n00:00:00,000 --> 00:00:01,000\nx\n\n\n")
    assert len(cues) == 1
    assert cues[0].text == "x"
