"""watch.py --demo / --captions playback (#314, epic #308).

Tested headlessly via an injected recording presenter (the #300 injectable main() +
#306 captions seam) — no live window / ffmpeg.
"""
import watch
from pycats.sim.demo import DEMOS, demo_captions, demo_frames


class _Rec:
    """Records the captions main() attaches + how many frames were shown."""
    def __init__(self):
        self.captions = []
        self.shows = 0

    def show(self, platforms, players, attacks, frame):
        self.shows += 1

    def close(self):
        pass


def test_captions_flag_overlays_srt_on_any_run(tmp_path):
    srt = tmp_path / "duel.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nNPC duel\n")
    pres = _Rec()
    watch.main(["--p1-char", "nalio", "--p1-level", "5",
                "--p2-char", "birky", "--p2-level", "9", "--seed", "3",
                "--frames", "20", "--uncapped", "--captions", str(srt)],
               presenter=pres)
    assert any(c.text == "NPC duel" for c in pres.captions), pres.captions
    assert pres.shows == 20  # the SRT rode along the (AI) leveled duel


def test_demo_flag_plays_registered_demo():
    pres = _Rec()
    watch.main(["--demo", "example", "--uncapped"], presenter=pres)
    demo = DEMOS["example"]
    assert [c.text for c in pres.captions] == [c.text for c in demo_captions(demo)]
    assert pres.shows == demo_frames(demo)  # ran the demo's scripted timeline


def test_no_caption_flags_leaves_injected_presenter_captions_untouched():
    # A presenter injected WITH its own captions (the #306 pattern) must not be clobbered.
    pres = _Rec()
    pres.captions = ["preset"]
    watch.main(["--p1-level", "5", "--p2-level", "5", "--seed", "3",
                "--frames", "10", "--uncapped"], presenter=pres)
    assert pres.captions == ["preset"]
