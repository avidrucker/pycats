"""Shield-break 'dizzy' stun (#12).

A fighter whose shield is depleted to 0 enters a `stun` state that locks ALL
inputs for a damage-scaled duration, matching Project M / Melee. Three concerns:

1. Duration formula (combat.shield.shield_break_stun_frames) — Melee/PM
   `(400 - p) + 90` frames, clamped [90, 490], DECREASING with damage.
2. State wiring — the (previously dormant) `stun` state is reachable from
   `shield` and exits to idle/fall when the timer expires.
3. Input lock — while stunned, held inputs neither move nor act on the fighter.
"""
import pygame as pg

from pycats.combat.shield import shield_break_stun_frames
from pycats.config import SHIELD_BREAK_STUN_MAX, SHIELD_BREAK_STUN_MIN
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x)


def _mk_player():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


# ----------------------------------------------------------------- 1. formula
def test_formula_matches_melee_pm_at_key_percents():
    # (400 - p) + 90 = 490 - p, clamped [90, 490].
    assert shield_break_stun_frames(0) == 490      # max at 0%
    assert shield_break_stun_frames(100) == 390
    assert shield_break_stun_frames(400) == 90     # floor reached at 400%


def test_formula_is_clamped_and_monotonic_decreasing():
    assert shield_break_stun_frames(500) == SHIELD_BREAK_STUN_MIN   # >=400% floors
    assert shield_break_stun_frames(0) == SHIELD_BREAK_STUN_MAX
    # strictly non-increasing as damage rises (inverse of normal stun)
    seq = [shield_break_stun_frames(p) for p in range(0, 450, 25)]
    assert seq == sorted(seq, reverse=True)


# ------------------------------------------------------------ 2. state wiring
def test_shield_break_sets_timer_from_formula():
    p = _mk_player()
    p.fighter.percent = 100
    p.fighter._start_stun()
    assert p.fighter.stun_timer == shield_break_stun_frames(100) == 390


def test_shield_to_stun_entry_and_exit():
    p = _mk_player()
    # get into the shield state first
    p.fighter.on_ground = True
    p.fighter.shield_attempting = True
    p.engine.tick(None)
    assert p.state == "shield", p.state
    # shield breaks -> stun_timer set; next tick must enter `stun`
    p.fighter.stun_timer = 30
    p.engine.tick(None)
    assert p.state == "stun", p.state
    # timer runs down; on_ground -> idle when it expires
    p.fighter.stun_timer = 0
    p.engine.tick(None)
    assert p.state == "idle", p.state


# ------------------------------------------ 3. passive-drain-to-0 break (#341)
def test_holding_shield_until_drained_to_zero_breaks_it():
    """#341: a shield drained to 0 by HOLDING (passive drain, no hit) must break
    into the dizzy `stun`, matching Melee/PM — a shield reaching 0 by ANY means
    breaks, not only by a connecting hit. Able-to-fail: pre-fix the drain path
    never calls _start_stun(), so the fighter sits in `shield` at 0 hp forever."""
    p = _mk_player()
    plats = pg.sprite.Group(Platform(pg.Rect(0, 160, 400, 40), thin=False))
    noop = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(30):                             # settle until grounded (falls ~16f)
        p.update(noop, plats, pg.sprite.Group())
        if p.fighter.on_ground:
            break
    assert p.fighter.on_ground, "fighter never landed to shield from"
    p.fighter.shield_hp = 1.0                       # a few drain ticks from empty (fast)
    # HELD (not a fresh press — a press spot-dodges); hold shield until it drains out.
    hold_shield = InputFrame(held={pg.K_x}, pressed=set(), released=set())
    broke = False
    for _ in range(12):
        p.update(hold_shield, plats, pg.sprite.Group())
        if p.fighter.stun_timer > 0:
            broke = True
            break
    assert broke, "holding shield until shield_hp hit 0 did not break it (#341)"
    assert p.state == "stun", p.state               # drain-to-0 broke into the dizzy


# ------------------------------------------------------- 4. dizzy animation
def _nonblack_pixel_count(surf, bg=(0, 0, 0)):
    n = 0
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            if tuple(surf.get_at((x, y)))[:3] != bg:
                n += 1
    return n


def test_draw_dizzy_stars_only_when_stunned():
    from pycats.render_battle import draw_dizzy_stars
    p = _mk_player()
    p.rect.topleft = (60, 60)   # leave room above the head on the surface

    blank = pg.Surface((160, 160))
    blank.fill((0, 0, 0))
    p.fighter.stun_timer = 0
    draw_dizzy_stars(blank, p)
    assert _nonblack_pixel_count(blank) == 0, "drew dizzy stars while not stunned"

    lit = pg.Surface((160, 160))
    lit.fill((0, 0, 0))
    p.fighter.stun_timer = 200
    draw_dizzy_stars(lit, p)
    assert _nonblack_pixel_count(lit) > 0, "no dizzy stars drawn while stunned"


def test_draw_dizzy_stars_animate_between_frames():
    from pycats.render_battle import draw_dizzy_stars
    p = _mk_player()
    p.rect.topleft = (60, 60)

    def _frame(timer):
        s = pg.Surface((160, 160))
        s.fill((0, 0, 0))
        p.fighter.stun_timer = timer
        draw_dizzy_stars(s, p)
        return pg.image.tobytes(s, "RGB")

    # consecutive stun ticks ⇒ orbit advanced ⇒ different pixels
    assert _frame(200) != _frame(199), "dizzy stars did not animate as stun ticks"


def test_render_battle_invokes_dizzy_for_stunned_player(monkeypatch):
    from pycats import render_battle as rb
    calls = []
    monkeypatch.setattr(rb, "draw_dizzy_stars", lambda surf, p: calls.append(p.fighter.stun_timer))
    surf = pg.Surface((400, 300))

    calm = _mk_player()
    calm.fighter.stun_timer = 0
    rb.render_battle(surf, [calm], pg.sprite.Group())
    assert calls == [], "dizzy drawn for a non-stunned fighter"

    dizzy = _mk_player()
    dizzy.fighter.stun_timer = 200
    rb.render_battle(surf, [dizzy], pg.sprite.Group())
    assert calls == [200], "render_battle did not draw dizzy for a stunned fighter"


# ------------------------------------------------------------- 5. input lock
def test_all_inputs_locked_while_stunned():
    p = _mk_player()
    plats = pg.sprite.Group(Platform(pg.Rect(0, 160, 400, 40), thin=False))
    # settle on ground
    noop = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(5):
        p.update(noop, plats, pg.sprite.Group())
    p.fighter._start_stun()            # break the shield -> dizzy
    x0 = p.rect.x
    held_right = InputFrame(held={pg.K_d}, pressed={pg.K_d, pg.K_v, pg.K_w},
                            released=set())
    for _ in range(10):
        p.update(held_right, plats, pg.sprite.Group())
    assert p.rect.x == x0, "stunned fighter moved despite locked inputs"
    assert p.fighter.jumps_remaining == 2, "stunned fighter jumped despite locked inputs"
