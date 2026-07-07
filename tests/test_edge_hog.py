"""True PM edge-hog (#311) — fixed-burst ledge invincibility (#543/#683), hog
timing, and half-animation regrab. Grounded by #297. Builds on #14's ledge-hang.

Contract, not implementation: exercised through Player.update + the Ledge model.
"""

import pygame

from pycats import config
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.ledge import LEFT, ledge_invuln_frames, ledges_from_platforms
from pycats.entities.platform import Platform

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _player():
    return Player(200, 200, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _empty_frame():
    return _frame()


def p_attack_group():
    return pygame.sprite.Group()


def _stage():
    return [Platform(pygame.Rect(80, 410, 800, 80), thin=False)]


def _grab_left(p, plats, ledges):
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.x, p.fighter.vel.y = 0, 5
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state == "ledge_hang"


# --- Piece 1: fixed-burst invincibility (#543/#683 — no longer percent-scaled) --


def test_ledge_invuln_frames_is_fixed_constant():
    # #543/#683: the burst is a flat PM 3.6 value (21f) — no percent arg, no cap.
    # Able-to-fail: reverting to `BASE + round(pct*PER_PERCENT)` reds this (the old
    # signature took a percent, and 23 != 21).
    assert ledge_invuln_frames() == config.LEDGE_INVULN_BASE_FRAMES
    assert config.LEDGE_INVULN_BASE_FRAMES == 21


def test_percent_does_not_change_ledge_invuln_window():
    # Damage-independent now: a 0% grab and a 150% grab get the same burst. Able-to-
    # fail: the old percent-scaling made high > low, reddening the equality below.
    plats = _stage()
    low = _player()
    low.fighter.percent = 0
    high = _player()
    high.fighter.percent = 150
    _grab_left(low, plats, ledges_from_platforms(plats))
    _grab_left(high, plats, ledges_from_platforms(plats))
    assert high.fighter.ledge_invuln_timer == low.fighter.ledge_invuln_timer
    assert low.fighter.ledge_invuln_timer == ledge_invuln_frames()


def test_grab_sets_invuln_burst_not_full_hang():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    p.fighter.percent = 0
    _grab_left(p, plats, ledges)
    assert p.fighter.invulnerable is True
    # the intangibility burst is the fixed window (#475: there is no full-hang
    # timeout to compare against — the hang itself is untimed).
    assert p.fighter.ledge_invuln_timer == ledge_invuln_frames()
    assert p.fighter.ledge_invuln_timer == config.LEDGE_INVULN_BASE_FRAMES  # the fixed burst


def test_invuln_lapses_while_still_hanging():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    p.fighter.percent = 0
    _grab_left(p, plats, ledges)
    # run past the burst but well within the hang window, holding nothing
    for _ in range(ledge_invuln_frames() + 2):
        p.update(_empty_frame(), plats, p_attack_group(), ledges)
        if p.state != "ledge_hang":
            break
    assert p.state == "ledge_hang"  # still hanging
    assert p.fighter.ledge_invuln_timer == 0
    assert p.fighter.invulnerable is False  # but no longer intangible


# --- Piece 3: half-animation regrab -----------------------------------------


def test_getup_frees_edge_at_half_animation_not_before():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    left = next(l for l in ledges if l.side == LEFT)
    p = _player()
    p.fighter.percent = 0
    _grab_left(p, plats, ledges)
    p.update(_frame("up"), plats, p_attack_group(), ledges)  # start the getup climb
    assert p.state == "ledge_getup"
    assert left.occupied_by is p  # still occupied at climb start
    half = config.LEDGE_GETUP_FRAMES // 2
    # step to just before half — edge stays occupied (can't regrab yet)
    for _ in range(half - 2):
        p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert left.occupied_by is p  # still hogged in first half
    # step past half — edge frees to others mid-getup
    for _ in range(3):
        p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert left.occupied_by is None  # re-grabbable mid-getup


# --- Piece 2: percent-gated hog timing + eviction ---------------------------


def test_hog_denies_grab_while_occupant_invincible():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p1 = _player()
    p1.fighter.percent = 100  # percent no longer affects the burst (#683); a fresh grab is intangible
    p2 = _player()
    p2.fighter.percent = 0
    _grab_left(p1, plats, ledges)
    assert p1.fighter.ledge_invuln_timer > 0
    # p2 enters the same catch region while p1 is still intangible -> denied
    p2.rect.topleft = (80 - 40, 420)
    p2.fighter.vel.y = 5
    p2.fighter.on_ground = False
    p2.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p2.fighter.grabbed_ledge is None
    assert p2.state != "ledge_hang"


def test_hog_grab_succeeds_and_evicts_once_invuln_lapses():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    left = next(l for l in ledges if l.side == LEFT)
    p1 = _player()
    p1.fighter.percent = 0
    p2 = _player()
    p2.fighter.percent = 0
    _grab_left(p1, plats, ledges)
    # let p1's invincibility lapse (hold nothing; stay hanging)
    for _ in range(ledge_invuln_frames() + 1):
        p1.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p1.fighter.ledge_invuln_timer == 0
    assert p1.state == "ledge_hang"
    # now p2 grabs the occupied edge -> succeeds, p1 evicted
    p2.rect.topleft = (80 - 40, 420)
    p2.fighter.vel.y = 5
    p2.fighter.on_ground = False
    p2.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p2.state == "ledge_hang"
    assert left.occupied_by is p2
    assert p1.fighter.grabbed_ledge is None  # p1 lost the ledge
    assert p1.fighter.ledge_regrab_lockout_timer > 0
    # p1's chart routes to fall on its next tick
    p1.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p1.state == "fall"
