"""STATUS_SOURCES registry — identity guard + one-record-add proof (#522).

`active_tint` and `timer_bar_specs` are unified behind one declarative
`STATUS_SOURCES` table (research #513 plan). This refactor is **behaviour-neutral**:
the two functions must produce byte-identical output to the pre-refactor code for
every status source.

- **Characterization guard** (`EXPECTED_TINT` / `EXPECTED_BARS`): a frozen snapshot of
  the pre-refactor outputs across a state/timer matrix, captured from the old code. The
  refactor must reproduce it exactly. Able-to-fail: perturb any registry record and a
  cell diverges.
- **One-record-add proof:** a synthetic `StatusSource` monkeypatched into the table must
  surface in **both** `active_tint` and `timer_bar_specs` with no code edits — the whole
  point of the registry (and the path #531 / #506 take).
"""
import os
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402


def st(**kw):
    """A flat status stand-in: self-refs `.fighter` so both `active_tint` (reads
    `p.fighter.*`) and `timer_bar_specs` (reads `p.state` + `p.fighter.*`) are fed by
    one object. Every timer field both functions read is present and defaults inert."""
    fields = dict(
        state="idle", hurt_timer=0, stun_timer=0, dodge_timer=0,
        getup_roll_timer=0, getup_attack_timer=0, ledge_invuln_timer=0,
        shield_hp=rb.SHIELD_MAX_HP, prone_timer=0,
        ledge_regrab_lockout_timer=0, invulnerable=False, smash_charge_timer=0,
    )
    fields.update(kw)
    ns = types.SimpleNamespace(**fields, rect=pygame.Rect(100, 200, 40, 60))
    ns.fighter = ns
    return ns


def _matrix():
    return {
        "calm": st(),
        "hurt": st(hurt_timer=5),
        "stun_tint": st(stun_timer=5),
        "dodge": st(dodge_timer=5),
        "hurt+stun": st(hurt_timer=5, stun_timer=5),
        "stun+dodge": st(stun_timer=5, dodge_timer=5),
        "shield": st(state="shield", shield_hp=25),
        "dizzy": st(stun_timer=240),
        "shield+stun": st(state="shield", shield_hp=30, stun_timer=100),
        "hang": st(state="ledge_hang"),
        "prone": st(state="prone", prone_timer=40),
        "lockout": st(ledge_regrab_lockout_timer=20),
        "invuln_dodge": st(invulnerable=True, dodge_timer=15),
        "invuln_getuproll": st(invulnerable=True, getup_roll_timer=10),
        "invuln_getupatk": st(invulnerable=True, getup_attack_timer=12),
        "invuln_suppressed_hang": st(
            state="ledge_hang", invulnerable=True, dodge_timer=15),
        "charge": st(smash_charge_timer=30),
        "overlay_combo": st(
            ledge_regrab_lockout_timer=20, invulnerable=True, dodge_timer=15, smash_charge_timer=30),
        "excl+overlays": st(stun_timer=240, ledge_regrab_lockout_timer=20, smash_charge_timer=30),
    }


# Frozen snapshot of the PRE-refactor outputs (captured from the old active_tint /
# timer_bar_specs). The registry must reproduce these byte-for-byte.
EXPECTED_TINT = {
    "calm": None, "hurt": (255, 0, 0), "stun_tint": (255, 255, 0), "dodge": (255, 255, 255),
    "hurt+stun": (255, 0, 0), "stun+dodge": (255, 255, 0), "shield": None, "dizzy": (255, 255, 0),
    "shield+stun": (255, 255, 0), "hang": None, "prone": None, "lockout": None,
    "invuln_dodge": (255, 255, 255), "invuln_getuproll": None, "invuln_getupatk": None,
    "invuln_suppressed_hang": (255, 255, 255), "charge": None,
    "overlay_combo": (255, 255, 255), "excl+overlays": (255, 255, 0),
}

EXPECTED_BARS = {
    "calm": [], "hurt": [], "dodge": [],
    "stun_tint": [(0.01020408163265306, "1s", (210, 90, 220), "DIZZY")],
    "hurt+stun": [(0.01020408163265306, "1s", (210, 90, 220), "DIZZY")],
    "stun+dodge": [(0.01020408163265306, "1s", (210, 90, 220), "DIZZY")],
    "shield": [(0.5, "3s", (70, 130, 255), "SHIELD")],
    "dizzy": [(0.4897959183673469, "4s", (210, 90, 220), "DIZZY")],
    "shield+stun": [(0.6, "3s", (70, 130, 255), "SHIELD")],
    "hang": [],  # #475: HANG bar removed (no hang timeout); ledge-invuln bar is #531
    "prone": [(1.3333333333333333, "1s", (255, 140, 45), "DOWN")],
    "lockout": [(0.6666666666666666, "1s", (230, 70, 70), "LOCKOUT")],
    "invuln_dodge": [(1.0714285714285714, "1s", (95, 225, 120), "INVULN")],
    "invuln_getuproll": [(0.625, "1s", (95, 225, 120), "INVULN")],
    "invuln_getupatk": [(0.5714285714285714, "1s", (95, 225, 120), "INVULN")],
    "invuln_suppressed_hang": [],  # #475: HANG gone; INVULN still suppressed in ledge_hang
    "charge": [(0.5, "50%·1s", (255, 205, 40), "CHARGE")],
    "overlay_combo": [
        (1.0714285714285714, "1s", (95, 225, 120), "INVULN"),
        (0.6666666666666666, "1s", (230, 70, 70), "LOCKOUT"),
        (0.5, "50%·1s", (255, 205, 40), "CHARGE")],
    "excl+overlays": [
        (0.6666666666666666, "1s", (230, 70, 70), "LOCKOUT"),
        (0.5, "50%·1s", (255, 205, 40), "CHARGE"),
        (0.4897959183673469, "4s", (210, 90, 220), "DIZZY")],
}


@pytest.mark.parametrize("name", list(_matrix()))
def test_active_tint_matches_snapshot(name):
    assert rb.active_tint(_matrix()[name]) == EXPECTED_TINT[name]


@pytest.mark.parametrize("name", list(_matrix()))
def test_timer_bar_specs_matches_snapshot(name):
    got = [tuple(b) for b in rb.timer_bar_specs(_matrix()[name])]
    assert got == EXPECTED_BARS[name]


def test_new_status_is_a_one_record_add(monkeypatch):
    """Registering a status is a single `StatusSource` that surfaces in BOTH
    `active_tint` and `timer_bar_specs` purely by being in `STATUS_SOURCES` — no new
    branches. Also able-to-fail: the baseline half proves nothing else handles the
    synthetic timer, the add half proves the registry actually drives both outputs."""
    p = st(_synth=50)  # otherwise-calm fighter carrying a fabricated timer field
    # baseline — an unregistered status affects neither output (no hidden branch)
    assert rb.active_tint(p) is None
    assert all(b.label != "SYNTH" for b in rb.timer_bar_specs(p))
    # add exactly one record → it drives the tint AND a bar, no code edits
    synth = rb.StatusSource(
        "synth", 99, active=lambda f, p: getattr(f, "_synth", 0) > 0,
        tint=(7, 7, 7), bar_color=(9, 9, 9), bar_label="SYNTH", bar_class="overlay",
        ratio=lambda f, p: f._synth / 100, readout=lambda f, p: "9s",
        recency=lambda f, p: 0.0)
    monkeypatch.setattr(rb, "STATUS_SOURCES", rb.STATUS_SOURCES + [synth])
    assert rb.active_tint(p) == (7, 7, 7)
    assert (0.5, "9s", (9, 9, 9), "SYNTH") in [tuple(b) for b in rb.timer_bar_specs(p)]
