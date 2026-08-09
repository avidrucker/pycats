"""Dev breadcrumb log for not-yet-implemented action attempts (#587).

OFF by default: the logger only writes when PYCATS_DEV_LOG is set, so the sim /
golden / test path does zero file I/O and stays byte-identical. These tests set
the flag PER-TEST via monkeypatch (never at module top level — that would leak
into the whole session) and point the log at a tmp path.
"""

import pygame as pg

from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player
from pycats.storage import dev_log, runtime_settings

MSG_CORE = "attempted to use"


def _enable(monkeypatch, tmp_path):
    log = tmp_path / "LOGS.txt"
    monkeypatch.setenv("PYCATS_DEV_LOG", "1")
    monkeypatch.setenv("PYCATS_DEV_LOG_PATH", str(log))
    dev_log.reset()  # clear per-session de-dupe memory
    return log


def _enable_via_dev_mode(monkeypatch, tmp_path):
    """Turn the logger on via the dev-mode gate (#1332), env explicitly UNSET — so the
    test proves the coupling, not the env path. The autouse _reset_runtime_settings
    fixture restores dev_mode to False after the test."""
    log = tmp_path / "LOGS.txt"
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    monkeypatch.setenv("PYCATS_DEV_LOG_PATH", str(log))
    runtime_settings.set_dev_mode(True)
    dev_log.reset()
    return log


# ---- unit: the logger itself -------------------------------------------------


def test_off_by_default_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    monkeypatch.setenv("PYCATS_DEV_LOG_PATH", str(tmp_path / "LOGS.txt"))
    dev_log.reset()
    wrote = dev_log.log_unimplemented("Birky", "up_b", "up+special", ["a.py", "b.py"])
    assert wrote is False
    assert not (tmp_path / "LOGS.txt").exists(), "OFF by default → no file I/O"


def test_on_writes_formatted_line(tmp_path, monkeypatch):
    log = _enable(monkeypatch, tmp_path)
    wrote = dev_log.log_unimplemented(
        "Birky", "up_b", "up+special", ["combat/move_select.py", "characters/birky_cat.py"]
    )
    assert wrote is True
    text = log.read_text()
    assert "Birky attempted to use up_b with up+special but it's not yet implemented" in text
    assert "see relevant files for implementation area(s)" in text
    assert "[combat/move_select.py, characters/birky_cat.py]" in text


def test_dedupes_same_fighter_move(tmp_path, monkeypatch):
    log = _enable(monkeypatch, tmp_path)
    dev_log.log_unimplemented("Birky", "up_b", "up+special", ["x.py"])
    second = dev_log.log_unimplemented("Birky", "up_b", "up+special", ["x.py"])
    assert second is False, "a repeated (fighter, move) must not spam the log"
    assert log.read_text().count("Birky attempted") == 1


def test_different_fighters_both_log(tmp_path, monkeypatch):
    log = _enable(monkeypatch, tmp_path)
    dev_log.log_unimplemented("Birky", "up_b", "up+special", ["x.py"])
    dev_log.log_unimplemented("Narz", "up_b", "up+special", ["x.py"])
    text = log.read_text()
    assert "Birky attempted" in text and "Narz attempted" in text


# ---- unit: the dev-mode coupling (#1332, B10) --------------------------------


def test_enabled_true_under_dev_mode_env_unset(tmp_path, monkeypatch):
    """#1332: a dev launch / F1-into-dev-mode turns the logger on with no env set."""
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    runtime_settings.set_dev_mode(True)
    assert dev_log.enabled() is True


def test_enabled_false_when_both_off(tmp_path, monkeypatch):
    """The determinism guard: dev mode off + env unset → OFF (shipping/sim path)."""
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    runtime_settings.set_dev_mode(False)
    assert dev_log.enabled() is False


def test_enabled_live_tracks_dev_mode_toggle(tmp_path, monkeypatch):
    """#1332 live-tracks F1: flip into dev mode → on; flip out → off (env unset)."""
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    runtime_settings.set_dev_mode(False)
    assert dev_log.enabled() is False
    runtime_settings.toggle_dev_mode()  # F1 into dev mode
    assert dev_log.enabled() is True
    runtime_settings.toggle_dev_mode()  # F1 back out
    assert dev_log.enabled() is False


def test_dev_mode_on_writes_breadcrumb_env_unset(tmp_path, monkeypatch):
    """The unit-level write path fires under dev mode alone (no env)."""
    log = _enable_via_dev_mode(monkeypatch, tmp_path)
    wrote = dev_log.log_unimplemented("Birky", "up_b", "up+special", ["x.py"])
    assert wrote is True
    assert "Birky attempted" in log.read_text()


# ---- integration: the fighter_input call site --------------------------------

CONTROLS = {
    "left": pg.K_a,
    "right": pg.K_d,
    "up": pg.K_w,
    "down": pg.K_s,
    "shield": pg.K_q,
    "attack": pg.K_e,
    "special": pg.K_c,
}


def _frame(keys):
    return InputFrame(held=set(keys), pressed=set(keys), released=set())


def _airborne_default():
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 2000, 960, 40), thin=False))
    p = Player(x=300, y=100, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE, char_name="P1", facing_right=True)
    for _ in range(3):
        p.update(_frame(set()), plats, pg.sprite.Group())
    return p, plats


def test_undefined_special_logs_when_enabled(tmp_path, monkeypatch):
    """Neutral+special on the default cat resolves to `neutral_b`, which it does not
    define → the input no-ops in play but leaves a breadcrumb when the flag is on."""
    log = _enable(monkeypatch, tmp_path)
    p, plats = _airborne_default()
    p.update(_frame({pg.K_c}), plats, pg.sprite.Group())  # neutral + special
    assert log.exists(), "an undefined special should leave a breadcrumb when enabled"
    assert MSG_CORE in log.read_text()
    assert "neutral_b" in log.read_text()


def test_undefined_special_silent_when_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("PYCATS_DEV_LOG", raising=False)
    monkeypatch.setenv("PYCATS_DEV_LOG_PATH", str(tmp_path / "LOGS.txt"))
    dev_log.reset()
    p, plats = _airborne_default()
    p.update(_frame({pg.K_c}), plats, pg.sprite.Group())
    assert not (tmp_path / "LOGS.txt").exists(), "OFF → the sim/golden path writes nothing"


def test_undefined_special_logs_under_dev_mode_env_unset(tmp_path, monkeypatch):
    """#1332: the fighter_input breadcrumb fires on the sim path in a dev-mode launch
    with PYCATS_DEV_LOG unset — the default-on-under-dev-mode acceptance criterion."""
    log = _enable_via_dev_mode(monkeypatch, tmp_path)
    p, plats = _airborne_default()
    p.update(_frame({pg.K_c}), plats, pg.sprite.Group())  # neutral + special
    assert log.exists(), "dev mode alone should leave a breadcrumb (env unset)"
    assert MSG_CORE in log.read_text()
    assert "neutral_b" in log.read_text()
