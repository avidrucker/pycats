"""--demo-speed slow-motion playback scalar (#351).

Slow-motion is presentation-only: the sim is fixed-timestep (#166/#80), so the
*display* of frames is paced slower while the sim stays byte-identical. Two pure
helpers pin the math (video frame-duplication + live tick pacing), plus a
VideoPresenter integration confirming the duplication actually happens.
"""
import pygame as pg
import pytest

from pycats.config import FPS
from pycats.sim.presenters import frames_per_output, tick_fps


def test_frames_per_output_duplicates_for_slow_motion():
    assert frames_per_output(1.0) == 1          # real time: 1 video frame / sim frame
    assert frames_per_output(0.5) == 2          # half speed -> 2 video frames / sim frame
    assert frames_per_output(0.25) == 4
    assert frames_per_output(2.0) == 1          # fast-forward never drops below 1 frame


def test_tick_fps_scales_the_live_pacing():
    assert tick_fps(1.0) == FPS                 # 60
    assert tick_fps(0.5) == round(FPS * 0.5)    # 30 -> ~2x wall-clock
    assert tick_fps(0.25) == round(FPS * 0.25)  # 15
    assert tick_fps(2.0) == FPS * 2             # 120


def test_video_presenter_duplicates_frames_at_half_speed(monkeypatch):
    iio = pytest.importorskip("imageio.v2")
    pg.init()
    import pycats.sim.presenters as pr
    monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
    monkeypatch.setattr(pr, "render_attacks", lambda *a, **k: None)
    monkeypatch.setattr(pr, "draw_captions", lambda *a, **k: None)

    class _FakeWriter:
        def __init__(self):
            self.count = 0
        def append_data(self, arr):
            self.count += 1
        def close(self):
            pass

    fake = _FakeWriter()
    monkeypatch.setattr(iio, "get_writer", lambda path, fps: fake)
    vp = pr.VideoPresenter(path="unused.mp4", speed=0.5)
    vp.show([], [], [], 0)
    assert fake.count == 2, "0.5x must write 2 video frames per sim frame"
    vp.show([], [], [], 1)
    assert fake.count == 4

    fake1 = _FakeWriter()
    monkeypatch.setattr(iio, "get_writer", lambda path, fps: fake1)
    vp1 = pr.VideoPresenter(path="unused.mp4")   # speed defaults to 1.0
    vp1.show([], [], [], 0)
    assert fake1.count == 1, "default (1.0x) writes exactly one frame per sim frame"
