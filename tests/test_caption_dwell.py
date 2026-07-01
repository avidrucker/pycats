"""Caption dwell — freeze the frame ~2.5s when a caption appears (#352).

The demo choreography is ONE continuous, frame-tuned timeline with OVERLAPPING caption
windows (e.g. the jump spans fall inside the approach window; the jab/KO beats are
position-tuned). So a dwell can't insert idle timeline frames — that would desync the
tuned beats. Instead it's a presenter-level freeze: hold (re-present) the caption's first
frame for `dwell` sim-frame-durations. Presentation-only; sim + goldens byte-identical.
"""
import pytest
import pygame as pg

from pycats.config import FPS
from pycats.sim.captions import Caption, caption_hold_frames
from pycats.sim.demo import DemoSegment, Demo, demo_captions, DEMOS
from pycats.sim.input_script import InputSpan


def test_caption_hold_frames_at_a_dwelling_caption_start():
    caps = [Caption("intro", frames=(10, 60), dwell=150)]
    assert caption_hold_frames(caps, 10) == 150   # holds at its window start
    assert caption_hold_frames(caps, 11) == 0     # not after
    assert caption_hold_frames(caps, 9) == 0      # not before


def test_caption_hold_frames_ignores_zero_dwell_and_untimed():
    assert caption_hold_frames([Caption("a", frames=(5, 9))], 5) == 0  # dwell defaults 0
    assert caption_hold_frames([Caption("a", dwell=150)], 0) == 0      # no window -> no hold


def test_caption_hold_frames_takes_the_max_when_captions_coincide():
    caps = [Caption("a", frames=(10, 20), dwell=90),
            Caption("b", frames=(10, 15), dwell=150)]
    assert caption_hold_frames(caps, 10) == 150


def test_demo_default_dwell_flows_into_captions_with_per_segment_override():
    demo = Demo(name="d", default_dwell=150, segments=(
        DemoSegment("s1", spans=(InputSpan(10, 40, 1, "right"),)),
        DemoSegment("s2", spans=(InputSpan(50, 51, 1, "up"),), dwell=30),
    ))
    caps = demo_captions(demo)
    assert caps[0].dwell == 150   # inherits the demo default
    assert caps[1].dwell == 30    # per-segment override wins


def test_showcase_captions_dwell_for_readability():
    caps = demo_captions(DEMOS["showcase"])
    assert caps, "showcase has captions"
    assert all(c.dwell == round(2.5 * FPS) == 150 for c in caps), "each caption holds ~2.5s"


def test_video_presenter_freezes_on_a_dwelling_caption(monkeypatch):
    iio = pytest.importorskip("imageio.v2")
    pg.init()
    import pycats.sim.presenters as pr
    monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
    monkeypatch.setattr(pr, "render_attacks", lambda *a, **k: None)
    monkeypatch.setattr(pr, "draw_captions", lambda *a, **k: None)

    class _FW:
        def __init__(self):
            self.count = 0
        def append_data(self, arr):
            self.count += 1
        def close(self):
            pass

    fw = _FW()
    monkeypatch.setattr(iio, "get_writer", lambda path, fps: fw)
    vp = pr.VideoPresenter(path="x.mp4")             # speed 1.0 -> 1 frame/sim-frame
    vp.captions = [Caption("hold", frames=(0, 5), dwell=3)]
    vp.show([], [], [], 0)                           # caption starts -> 1*(1+3) = 4 frames
    assert fw.count == 4
    vp.show([], [], [], 1)                           # no caption start -> +1
    assert fw.count == 5
