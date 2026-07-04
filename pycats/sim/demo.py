# pycats/sim/demo.py
"""Demo composition + SRT captions (#314, epic #308).

A demo is **plain data**: an ordered list of `DemoSegment`s, each composing the
input-script spans that drive the fighters with a caption that labels the beat. The
segments are independent, so a demo is authored/edited/reordered without touching any
render or sim code. Captions can also be authored as a standard **SRT** file — the most
editable caption source — and overlaid on *any* run.

Playback: `demo_timeline(demo, keymaps)` compiles the segments into one `InputFrame`
timeline (feed to `run_battle(frame_inputs=…)`); `demo_captions(demo)` builds the timed
`Caption` list (hand to the presenter). Both are pure and deterministic (#166).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..config import FPS
from .captions import BOTTOM_CENTER, Caption
from .input_script import InputSpan, compile_timeline


@dataclass(frozen=True)
class DemoSegment:
    """One choreographed beat: the `InputSpan`s driving the fighters + a caption.

    The caption's frame window defaults to the spans' extent (`[min start, max end)`,
    inclusive last frame); `start`/`end` override it (e.g. an untimed intro caption over
    a segment with no spans)."""
    caption: str
    spans: Tuple[InputSpan, ...] = ()
    start: Optional[int] = None
    end: Optional[int] = None
    anchor: str = BOTTOM_CENTER
    size: int = 32
    font: Optional[str] = None
    # #352: frames to FREEZE the display on this caption so a viewer can read it
    # (presenter-level hold, NOT idle timeline frames — the choreography is frame-tuned).
    # None = inherit the demo's `default_dwell`.
    dwell: Optional[int] = None
    # #412: the frame to freeze on. None = the window start (default). A beat whose action
    # lands late in its window points this at the payoff frame so the frozen frame shows
    # the action, not a pre-action pose. Must lie within window() (validated in demo_captions).
    dwell_at: Optional[int] = None

    def window(self) -> Optional[Tuple[int, int]]:
        if self.start is not None and self.end is not None:
            return (self.start, self.end)
        if self.spans:
            return (min(s.start for s in self.spans),
                    max(s.end for s in self.spans) - 1)
        return None  # always-on


@dataclass(frozen=True)
class Demo:
    """A named, playable choreography: ordered segments + the fighters to build."""
    name: str
    segments: Tuple[DemoSegment, ...]
    p1_char: Optional[str] = None
    p2_char: Optional[str] = None
    default_dwell: int = 0  # #352: caption freeze applied to segments that don't set `dwell`


def demo_captions(demo: Demo) -> List[Caption]:
    """One timed Caption per segment (list order = draw order).

    Each caption's text is prefixed with its 1-based position `i/n — ` (#356) so a
    viewer can track which beat they're on; the numbering derives from segment order +
    count, so reordering/adding a segment renumbers automatically. Numbering is
    demo-choreography only — SRT / `--captions` overlays (captions_from_srt) stay raw.
    Each caption also carries its dwell (#352): the segment's `dwell` if set, else the
    demo's `default_dwell`. A segment may also set `dwell_at` (#412) to freeze on a chosen
    frame instead of the window start — validated here to lie within the caption's window,
    so a mis-set value fails loudly rather than freezing a caption-less frame."""
    n = len(demo.segments)
    caps = []
    for i, seg in enumerate(demo.segments, 1):
        win = seg.window()
        if seg.dwell_at is not None:
            if win is None:
                raise ValueError(
                    f"segment {i} ({seg.caption!r}) sets dwell_at={seg.dwell_at} but has no "
                    f"frame window to anchor to")
            if not (win[0] <= seg.dwell_at <= win[1]):
                raise ValueError(
                    f"segment {i} ({seg.caption!r}) dwell_at={seg.dwell_at} is outside its "
                    f"window {win}")
        caps.append(Caption(
            f"{i}/{n} — {seg.caption}", anchor=seg.anchor, size=seg.size, font=seg.font,
            frames=win, dwell=(seg.dwell if seg.dwell is not None else demo.default_dwell),
            dwell_at=seg.dwell_at))
    return caps


def demo_timeline(demo: Demo, keymaps):
    """Compile every segment's spans into one InputFrame timeline."""
    spans = [s for seg in demo.segments for s in seg.spans]
    return compile_timeline(spans, keymaps)


def demo_frames(demo: Demo) -> int:
    """Total frames = the furthest span end across all segments (0 if scriptless)."""
    ends = [s.end for seg in demo.segments for s in seg.spans]
    return max(ends) if ends else 0


# --------------------------------------------------------------------------- #
# SRT captions — the editable caption source
# --------------------------------------------------------------------------- #

_TS = r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
_TIME_LINE = re.compile(rf"{_TS}\s*-->\s*{_TS}")


def _ts_to_seconds(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def captions_from_srt(srt_text: str, fps: int = FPS, anchor: str = BOTTOM_CENTER,
                      size: int = 32, font: Optional[str] = None) -> List[Caption]:
    """Parse SRT subtitle text into timed Captions (timestamps -> frame windows).

    Each entry's `[start, end)` seconds map to the inclusive frame window
    `(round(start*fps), round(end*fps) - 1)`, so consecutive entries don't overlap.
    Multi-line text is joined with spaces."""
    captions: List[Caption] = []
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip() != ""]
        if not lines:
            continue
        time_idx = next((i for i, ln in enumerate(lines) if _TIME_LINE.search(ln)), None)
        if time_idx is None:
            continue
        m = _TIME_LINE.search(lines[time_idx])
        start_s = _ts_to_seconds(*m.group(1, 2, 3, 4))
        end_s = _ts_to_seconds(*m.group(5, 6, 7, 8))
        text = " ".join(lines[time_idx + 1:]).strip()
        if not text:
            continue
        start_f = round(start_s * fps)
        end_f = max(start_f, round(end_s * fps) - 1)
        captions.append(Caption(text, anchor=anchor, size=size, font=font,
                                frames=(start_f, end_f)))
    return captions


# --------------------------------------------------------------------------- #
# Registry — one minimal example (curated Nalio-vs-Birky content is child 3)
# --------------------------------------------------------------------------- #

_EXAMPLE = Demo(
    name="example",
    p1_char="nalio", p2_char="birky",
    segments=(
        DemoSegment("Nalio walks in", spans=(InputSpan(10, 40, 1, "right"),)),
        DemoSegment("Nalio jumps", spans=(InputSpan(50, 51, 1, "up"),)),
        DemoSegment("Nalio attacks", spans=(InputSpan(90, 91, 1, "attack"),)),
    ),
)

DEMOS = {_EXAMPLE.name: _EXAMPLE}

# The curated showcase lives in its own module (long span list); register it here.
# Imported at the bottom so `Demo`/`DemoSegment` are already defined (no import cycle).
from .showcase import SHOWCASE  # noqa: E402

DEMOS[SHOWCASE.name] = SHOWCASE
