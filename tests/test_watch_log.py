"""watch.py --log flag — print the derived battle event-log after a run (#300).

main() is made injectable (argv, presenter) so the flag is testable headlessly with a
null presenter (LivePresenter pops SDL_VIDEODRIVER + opens a real window, so it can't
drive a headless integration test). battle_log_text() is the formatting seam.
"""
import watch


class _NullPresenter:
    def show(self, platforms, players, attacks, frame, inputs=None):
        pass

    def close(self):
        pass


def _part(name, state="idle", percent=0.0, lives=3, jumps=2, on_ground=True):
    return (name, state, 0, 0, 0.0, 0.0, on_ground, float(percent), 0.0, lives,
            lives > 0, jumps, 0, 0, 0, 0, 0, True, False, "none", 0)


def _atk(owner):
    return (0, 0, 5, owner, True, 0.0, 0.0, 0.0)


def _snap(parts, atk=(), winner=None):
    return (tuple(parts), tuple(atk), "play", winner)


def test_battle_log_text_includes_tally_and_render_lines():
    # frame 1: P1 jumps (2->1) AND starts an attack -> 2 events.
    snaps = [_snap([_part("P1", jumps=2)]),
             _snap([_part("P1", jumps=1)], atk=[_atk("P1")])]
    text = watch.battle_log_text(snaps)
    assert "battle log: 2 events" in text
    assert "ATTACK:1" in text and "JUMP:1" in text
    assert "P1" in text and "JUMP" in text and "ATTACK" in text


def test_battle_log_text_empty_run():
    s = _snap([_part("P1")])
    text = watch.battle_log_text([s, s])
    assert "battle log: 0 events" in text


def test_log_flag_prints_event_log(capsys):
    watch.main(["--p1-level", "5", "--p2-level", "5", "--seed", "3",
                "--frames", "60", "--uncapped", "--log"],
               presenter=_NullPresenter())
    out = capsys.readouterr().out
    assert "battle log:" in out                       # the --log flag fired
    assert len(out.strip().splitlines()) >= 2, out    # header + at least one event line


def test_no_log_flag_is_silent(capsys):
    watch.main(["--p1-level", "5", "--p2-level", "5", "--seed", "3",
                "--frames", "60", "--uncapped"],
               presenter=_NullPresenter())
    out = capsys.readouterr().out
    assert "battle log:" not in out
