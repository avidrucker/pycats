"""Demo composition + SRT captions (#314, epic #308).

A demo composes input-script spans with captions over one timeline; captions can also
come from an editable SRT file. All pure data + pure functions (no sim run needed).
"""
from pycats.sim.captions import TOP_CENTER, BOTTOM_CENTER
from pycats.sim.input_script import InputSpan
from pycats.sim.runner import KEYMAPS
from pycats.sim.demo import (
    Caption, DemoSegment, Demo, demo_captions, demo_timeline, demo_frames,
    captions_from_srt, DEMOS,
)


# --- SRT captions --------------------------------------------------------------

def test_captions_from_srt_maps_timestamps_to_frame_windows():
    srt = ("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n"
           "2\n00:00:01,000 --> 00:00:02,500\nWorld\n")
    caps = captions_from_srt(srt, fps=60)
    assert len(caps) == 2
    assert caps[0].text == "Hello"
    assert caps[0].frames == (0, 59)      # [0s, 1s) -> frames 0..59 at 60fps
    assert caps[1].text == "World"
    assert caps[1].frames == (60, 149)    # [1s, 2.5s) -> 60..149


def test_captions_from_srt_joins_multiline_text():
    srt = "1\n00:00:00,000 --> 00:00:01,000\nLine one\nLine two\n"
    caps = captions_from_srt(srt)
    assert caps[0].text == "Line one Line two"


def test_captions_from_srt_honors_anchor_default():
    srt = "1\n00:00:00,000 --> 00:00:01,000\nHi\n"
    caps = captions_from_srt(srt, anchor=TOP_CENTER)
    assert caps[0].anchor == TOP_CENTER


# --- demo segment / composition ------------------------------------------------

def test_segment_window_derived_from_spans():
    seg = DemoSegment("jump", spans=(InputSpan(50, 55, 1, "up"),))
    assert seg.window() == (50, 54)       # [start, end) -> inclusive last frame


def test_segment_window_explicit_overrides():
    seg = DemoSegment("hi", start=10, end=30)
    assert seg.window() == (10, 30)


def test_demo_captions_one_per_segment_with_windows():
    demo = Demo("t", segments=(
        DemoSegment("A", start=0, end=10, anchor=TOP_CENTER),
        DemoSegment("B", start=11, end=20),
    ))
    caps = demo_captions(demo)
    assert [c.text for c in caps] == ["A", "B"]
    assert caps[0].anchor == TOP_CENTER and caps[0].frames == (0, 10)
    assert caps[1].frames == (11, 20)


def test_demo_timeline_compiles_all_segment_spans():
    demo = Demo("t", segments=(
        DemoSegment("walk", spans=(InputSpan(0, 5, 1, "right"),)),
        DemoSegment("jump", spans=(InputSpan(10, 11, 1, "up"),)),
    ))
    tl = demo_timeline(demo, KEYMAPS)
    assert len(tl) == 11                  # max span end
    assert tl[0].held and tl[4].held      # P1 walking frames 0..4
    assert not tl[7].held                 # gap
    assert tl[10].held                    # P1 jump frame 10
    assert demo_frames(demo) == 11


def test_registry_has_a_playable_example():
    assert DEMOS, "at least one example demo registered"
    demo = next(iter(DEMOS.values()))
    assert demo.segments
    assert len(demo_captions(demo)) == len(demo.segments)
    assert demo_frames(demo) > 0
