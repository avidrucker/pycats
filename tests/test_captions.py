"""On-screen captions for sims/demos (#306, epic #308).

Captions are plain data (a `Caption` list), composed and drawn over the battle by the
presenters — a presentation overlay only (sim/goldens untouched). Tested with the
offscreen-surface oracle (the #205 render-test pattern); the presenter wiring is tested
with a fake video writer (no ffmpeg).
"""
import pygame
import pytest

from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.sim.captions import (
    BOTTOM_CENTER,
    CAPTION_MARGIN,
    MIDDLE_CENTER,
    TOP_CENTER,
    Caption,
    anchored_rect,
    draw_captions,
    is_active,
    render_caption_surface,
)


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    pygame.font.init()
    yield


# --- frame-window gating -------------------------------------------------------

def test_is_active_untimed_is_always_on():
    c = Caption("x", frames=None)
    assert is_active(c, 0) and is_active(c, 999)


def test_is_active_respects_inclusive_window():
    c = Caption("x", frames=(10, 20))
    assert not is_active(c, 9)
    assert is_active(c, 10) and is_active(c, 15) and is_active(c, 20)
    assert not is_active(c, 21)


# --- anchored geometry ---------------------------------------------------------

def test_anchored_rect_three_anchors():
    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    ts = (200, 40)
    top = anchored_rect(TOP_CENTER, size, ts)
    mid = anchored_rect(MIDDLE_CENTER, size, ts)
    bot = anchored_rect(BOTTOM_CENTER, size, ts)
    assert top.midtop == (SCREEN_WIDTH // 2, CAPTION_MARGIN)
    assert mid.center == (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    assert bot.midbottom == (SCREEN_WIDTH // 2, SCREEN_HEIGHT - CAPTION_MARGIN)


def test_anchored_rect_rejects_unknown_anchor():
    with pytest.raises(ValueError):
        anchored_rect("somewhere", (100, 100), (10, 10))


# --- font / size ---------------------------------------------------------------

def test_size_scales_caption_footprint():
    small = render_caption_surface(Caption("HELLO", size=12))
    big = render_caption_surface(Caption("HELLO", size=48))
    assert big.get_width() > small.get_width()
    assert big.get_height() > small.get_height()


# --- drawing + active-only composition ----------------------------------------

def _count(surface, color):
    arr = pygame.surfarray.array3d(surface)
    return int(((arr[:, :, 0] == color[0]) &
                (arr[:, :, 1] == color[1]) &
                (arr[:, :, 2] == color[2])).sum())


def test_draw_captions_renders_active_and_skips_inactive():
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill((0, 0, 0))
    active = Caption("TOP", anchor=TOP_CENTER, size=48, color=(255, 0, 0), frames=(0, 10))
    inactive = Caption("BOT", anchor=BOTTOM_CENTER, size=48, color=(0, 255, 0), frames=(100, 200))
    draw_captions(surface, [active, inactive], frame=5)
    assert _count(surface, (255, 0, 0)) > 0, "active caption should paint"
    assert _count(surface, (0, 255, 0)) == 0, "inactive caption must not paint"


# --- presenter wiring (fake writer, no ffmpeg) --------------------------------

def test_video_presenter_draws_captions(monkeypatch):
    frames_out = []

    class _FakeWriter:
        def append_data(self, arr):
            frames_out.append(arr)

        def close(self):
            pass

    import imageio.v2 as imageio
    monkeypatch.setattr(imageio, "get_writer", lambda *a, **k: _FakeWriter())
    from pycats.sim.presenters import VideoPresenter

    cap = Caption("HELLO", anchor=TOP_CENTER, size=48, color=(255, 0, 0), frames=(0, 10))
    vp = VideoPresenter("ignored.mp4", captions=[cap])
    empty = pygame.sprite.Group()
    vp.show([], empty, empty, frame=5)     # caption active
    vp.show([], empty, empty, frame=100)   # caption inactive

    assert len(frames_out) == 2

    def reds(arr):
        return int(((arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 0)).sum())

    assert reds(frames_out[0]) > 0, "active frame should carry the caption"
    assert reds(frames_out[1]) == 0, "inactive frame should not"
