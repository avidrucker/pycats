"""ScreenshotPresenter captures a PNG per caption for visual demo inspection (#411)."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.sim.demo import DEMOS, demo_captions, demo_frames, demo_timeline
from pycats.sim.presenters import ScreenshotPresenter
from pycats.sim.runner import KEYMAPS, run_battle


def test_screenshot_presenter_writes_a_shot_per_caption(tmp_path):
    d = DEMOS["showcase"]
    caps = demo_captions(d)
    pres = ScreenshotPresenter(str(tmp_path), captions=caps)
    run_battle(frame_inputs=demo_timeline(d, KEYMAPS), frames=demo_frames(d),
               p1_char=d.p1_char, p2_char=d.p2_char, presenter=pres)

    pngs = sorted(tmp_path.glob("*.png"))
    # At least one shot per captioned segment (the default captures start/mid/end).
    assert len(pngs) >= len(caps), f"{len(pngs)} shots for {len(caps)} captions"
    assert all(f.stat().st_size > 0 for f in pngs), "every PNG is non-empty"
    # A manifest maps shots to captions, one line per saved shot.
    manifest = tmp_path / "MANIFEST.txt"
    assert manifest.exists()
    assert len(manifest.read_text().strip().splitlines()) == len(pres.saved)


def test_screenshot_presenter_honours_explicit_frames(tmp_path):
    d = DEMOS["showcase"]
    pres = ScreenshotPresenter(str(tmp_path), captions=demo_captions(d),
                               frames={10: "a", 50: "b", 90: "c"})
    run_battle(frame_inputs=demo_timeline(d, KEYMAPS), frames=demo_frames(d),
               p1_char=d.p1_char, p2_char=d.p2_char, presenter=pres)
    assert sorted(f.name for f in tmp_path.glob("*.png")) == ["a.png", "b.png", "c.png"]
