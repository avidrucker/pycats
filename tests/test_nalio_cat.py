"""'Nalio' cat archetype data (#123, first impl slice of #117).

Nalio is the feline character that plays as the balanced all-rounder (Project M
Mario) archetype. Per the #119 spec (PM3.6 canonical, #120 unit convention):
combat numbers drop in raw; weight 100 == pycats default.

These tests pin Nalio as DISTINCT data reachable through the load_fighter_data
seam — without touching the default cat (so goldens stay green: the sim path
loads "P1"/"P2", never "nalio").
"""
import pygame

from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.combat.data import FighterData, load_fighter_data
from pycats.entities import Player

P1_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                   down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                   shield=pygame.K_x)


def test_nalio_is_distinct_fighter_data():
    """load_fighter_data("nalio") returns its own FighterData, not the shared
    default object every other key still maps to."""
    fd = load_fighter_data("nalio")
    assert isinstance(fd, FighterData)
    assert fd is not DEFAULT_FIGHTER_DATA


def test_nalio_weight_is_pm_mario_100():
    """PM3.6 Mario weight = 100 (== pycats default → no knockback change)."""
    assert load_fighter_data("nalio").weight == 100


def test_nalio_falls_on_pm_mario_baseline():
    """Nalio (Mario) is pinned to the PM-Mario-calibrated fall baseline (#557).

    #528 established that Nalio's `gravity`/`max_fall_speed` were the *generic
    engine defaults*, uncited as Mario's — yet they serve as the anchor every
    other cat's fall is scaled against (Birky's #229 ratios were derived from
    them). The pin (#530 routing: already-sourced → DEV) binds Nalio explicitly
    to `config.GRAVITY` / `config.MAX_FALL_SPEED`, which already carry provenance
    to PM Mario: GRAVITY is FOUND (PM Mario 0.095 u/f^2 -> PX_PER_UNIT, #384);
    MAX_FALL_SPEED is the documented single-cap DIVERGENCE (~ Mario fast-fall).
    No runtime value change — the guard locks the *relationship* so Nalio can't
    silently drift off the Mario baseline with a divergent literal.
    """
    from pycats import config

    fd = load_fighter_data("nalio")
    assert fd.gravity == config.GRAVITY
    assert fd.max_fall_speed == config.MAX_FALL_SPEED


def test_fighter_data_weight_defaults_to_100():
    """The default cat keeps the Smash baseline weight without specifying it."""
    assert DEFAULT_FIGHTER_DATA.weight == 100


def test_nalio_attack_is_pm_down_tilt():
    """Nalio's 'attack' slot carries PM3.6 Mario's down-tilt (AttackLw3),
    entered raw per #120: dmg 9, BKB 30, KBG 80, angle 80, startup 5 / active 4 /
    recovery 21. Able-to-fail: any wrong value (or falling back to the default
    jab — dmg 10, angle 0, KBG 100) breaks this."""
    move = load_fighter_data("nalio").moves["attack"]
    assert (move.startup, move.active, move.recovery) == (5, 4, 21)
    hb = move.hitboxes[0]
    assert hb.damage == 9.0
    assert hb.angle == 80
    assert hb.base_knockback == 30.0
    assert hb.knockback_growth == 80.0


def test_nalio_jab_is_pm_attack11():
    """Nalio's neutral-A key carries PM3.6 Mario Attack11 (#154, WDSK applied #212).

    rukaidata Attack11: total 16f / IASA 16, hitboxes active 2-3, three same-set
    hitboxes — all SET knockback (WDSK 20, BKB 0, KBG 100). The #211 gate now
    represents WDSK, so `set_knockback=20` replaces the old deferred approximation.
    Radii are round(size u × 5.4): 3.52->19, 2.34->13, 2.73->15.
    """
    move = load_fighter_data("nalio").moves["jab"]
    assert move.name == "jab"
    assert move.in_air is False
    assert (move.startup, move.active, move.recovery) == (1, 2, 13)
    assert len(move.hitboxes) == 3
    assert tuple(hb.damage for hb in move.hitboxes) == (3.0, 3.0, 3.0)
    assert tuple(hb.angle for hb in move.hitboxes) == (83, 83, 85)
    assert tuple(hb.base_knockback for hb in move.hitboxes) == (0.0, 0.0, 0.0)
    assert tuple(hb.knockback_growth for hb in move.hitboxes) == (100.0, 100.0, 100.0)
    assert tuple(hb.set_knockback for hb in move.hitboxes) == (20, 20, 20)  # WDSK (#212)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (19, 13, 15)


def test_nalio_dtilt_is_three_hitboxes():
    """Nalio's down-tilt is PM3.6 Mario's real 3-hitbox AttackLw3 (#132, on the
    #130 multi-hitbox engine) — not the single-hit approximation. All three are
    active 5-8 (simultaneous), angle 80 / BKB 30 / KBG 80; damages 9/9/8 and
    radii 13/17/21 (sizes 2.34/3.13/3.91 u × 5.4), in priority order (id 0->2).
    Able-to-fail: today's single box reds this."""
    move = load_fighter_data("nalio").moves["attack"]
    assert len(move.hitboxes) == 3, "down-tilt should declare its 3 real hitboxes"
    assert tuple(hb.damage for hb in move.hitboxes) == (9.0, 9.0, 8.0)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (13, 17, 21)
    for hb in move.hitboxes:
        assert hb.angle == 80
        assert hb.base_knockback == 30.0
        assert hb.knockback_growth == 80.0


def test_nalio_ftilt_is_pm_attacks3():
    """Nalio's forward tilt is PM3.6 Mario AttackS3 (forward/mid angle) — the
    FIRST move to use the Sakurai-angle sentinel (361, #203). rukaidata: active
    5-7 (startup 4 / active 3), FAF 30 (recovery 23); 3 hitboxes in priority order
    (id 0->2), all damage 9 / angle 361 / BKB 6 / KBG 100; radii 21/17/15 (sizes
    3.91/3.13/2.73 u × 5.4). Able-to-fail: an absent ftilt key falls back to the
    d-tilt alias (angle 80, BKB 30) and reds this."""
    move = load_fighter_data("nalio").moves["ftilt"]
    assert move.in_air is False
    assert (move.startup, move.active, move.recovery) == (4, 3, 23)
    assert len(move.hitboxes) == 3
    assert tuple(hb.damage for hb in move.hitboxes) == (9.0, 9.0, 9.0)
    assert tuple(hb.angle for hb in move.hitboxes) == (361, 361, 361)
    assert tuple(hb.base_knockback for hb in move.hitboxes) == (6.0, 6.0, 6.0)
    assert tuple(hb.knockback_growth for hb in move.hitboxes) == (100.0, 100.0, 100.0)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (21, 17, 15)


def test_nalio_utilt_is_pm_attackhi3():
    """Nalio's up tilt is PM3.6 Mario AttackHi3 (rukaidata). Active 5-11 (startup
    4 / active 7), IASA 30 (recovery 19); 3 hitboxes priority id 0->2, all damage
    8 / angle 96 (literal, up-and-slightly-back) / BKB 26 / WDSK 0; per-box KBG
    125/122/120; radii 15/19/25 (sizes 2.73/3.52/4.69 u × 5.4). Able-to-fail: an
    absent utilt key falls back to the d-tilt alias (angle 80, KBG 80) and reds
    this."""
    move = load_fighter_data("nalio").moves["utilt"]
    assert move.in_air is False
    assert (move.startup, move.active, move.recovery) == (4, 7, 19)
    assert len(move.hitboxes) == 3
    assert tuple(hb.damage for hb in move.hitboxes) == (8.0, 8.0, 8.0)
    assert tuple(hb.angle for hb in move.hitboxes) == (96, 96, 96)
    assert tuple(hb.base_knockback for hb in move.hitboxes) == (26.0, 26.0, 26.0)
    assert tuple(hb.knockback_growth for hb in move.hitboxes) == (125.0, 122.0, 120.0)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (15, 19, 25)


def test_nalio_fair_is_pm_attackairf_two_windows():
    """Nalio's f-air is PM3.6 Mario AttackAirF (rukaidata) — the first move to use
    the #204 per-hitbox temporal windows. Active 16-22 (startup 15 / active 7),
    IASA 45 (recovery 23). Two windows: early [16,17] (angle 60, strong) then the
    meteor late [18,22] (angle 280, downward spike). Able-to-fail: an absent fair
    key falls back to nair, and collapsing the windows breaks the per-box timing."""
    move = load_fighter_data("nalio").moves["fair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (15, 7, 23)
    assert len(move.hitboxes) == 4

    early = [hb for hb in move.hitboxes if hb.active_start == 16]
    late = [hb for hb in move.hitboxes if hb.active_start == 18]
    assert len(early) == 2 and len(late) == 2

    # Early window [16, 17].
    assert all(hb.active_end == 17 for hb in early)
    assert tuple(hb.damage for hb in early) == (17.0, 16.0)
    assert all(hb.angle == 60 for hb in early)
    assert tuple(hb.base_knockback for hb in early) == (50.0, 40.0)
    assert all(hb.knockback_growth == 100.0 for hb in early)
    assert tuple(hb.circle.r for hb in early) == (17, 24)

    # Late window [18, 22] — the meteor (angle 280 = downward).
    assert all(hb.active_end == 22 for hb in late)
    assert tuple(hb.damage for hb in late) == (15.0, 15.0)
    assert all(hb.angle == 280 for hb in late)
    assert all(hb.base_knockback == 30.0 for hb in late)
    assert all(hb.knockback_growth == 70.0 for hb in late)
    assert tuple(hb.circle.r for hb in late) == (17, 21)


def test_nalio_fair_spawns_two_windows_through_player_update():
    """End-to-end (#204): driving the real f-air through Player.update spawns the
    early window as one Attack on frame 16 and the meteor late window as a SEPARATE
    Attack on frame 18."""
    from pycats.core.input import InputFrame
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    p._clock.start(load_fighter_data("nalio").moves["fair"])

    seen: set[int] = set()
    appeared: list[tuple[int, int]] = []  # (frame, first-box angle)
    for frame in range(1, 24):
        p.update(neutral, [], group)  # airborne, no platforms; clock still ticks
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].angle))

    assert appeared == [(16, 60), (18, 280)], "early then meteor, separate Attacks"


def test_nalio_bair_is_pm_attackairb_two_windows():
    """Nalio's b-air is PM3.6 Mario AttackAirB (rukaidata) — a clean→late sex-kick
    using BOTH gates. Active 6-17 (startup 5 / active 12), IASA 29 (recovery 12).
    Clean [6,8]: angle 28, dmg 11, BKB 43, KBG 65. Late [9,17]: angle 361 (the
    Sakurai sentinel, #203), dmg 9, BKB 20, KBG 100. Able-to-fail: an absent key
    falls back to nair; collapsing the windows breaks the per-box timing."""
    move = load_fighter_data("nalio").moves["bair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (5, 12, 12)
    assert len(move.hitboxes) == 4

    clean = [hb for hb in move.hitboxes if hb.active_start == 6]
    late = [hb for hb in move.hitboxes if hb.active_start == 9]
    assert len(clean) == 2 and len(late) == 2

    # Clean window [6, 8].
    assert all(hb.active_end == 8 for hb in clean)
    assert tuple(hb.damage for hb in clean) == (11.0, 11.0)
    assert all(hb.angle == 28 for hb in clean)
    assert all(hb.base_knockback == 43.0 for hb in clean)
    assert all(hb.knockback_growth == 65.0 for hb in clean)
    assert tuple(hb.circle.r for hb in clean) == (25, 19)

    # Late window [9, 17] — the Sakurai-angle (361) weak hit.
    assert all(hb.active_end == 17 for hb in late)
    assert tuple(hb.damage for hb in late) == (9.0, 9.0)
    assert all(hb.angle == 361 for hb in late)
    assert all(hb.base_knockback == 20.0 for hb in late)
    assert all(hb.knockback_growth == 100.0 for hb in late)
    assert tuple(hb.circle.r for hb in late) == (25, 19)


def test_nalio_bair_spawns_two_windows_through_player_update():
    """End-to-end (#204): the clean window spawns one Attack on frame 6 and the
    Sakurai late window a SEPARATE Attack on frame 9."""
    from pycats.core.input import InputFrame
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    p._clock.start(load_fighter_data("nalio").moves["bair"])

    seen: set[int] = set()
    appeared: list[tuple[int, int]] = []
    for frame in range(1, 19):
        p.update(neutral, [], group)
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].angle))

    assert appeared == [(6, 28), (9, 361)], "clean then Sakurai late, separate Attacks"


def test_nalio_uair_is_pm_attackairhi_two_windows():
    """Nalio's u-air is PM3.6 Mario AttackAirHi (rukaidata) — a two-window upward
    juggle. Active 4-9 (startup 3 / active 6), IASA 28 (recovery 19). Clean [4,5]
    dmg 11, late [6,9] dmg 10; both angle 55, BKB 0 (pure-growth), KBG 100, r 19/25.
    Able-to-fail: an absent key falls back to nair; collapsing the windows breaks
    the per-box timing."""
    move = load_fighter_data("nalio").moves["uair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (3, 6, 19)
    assert len(move.hitboxes) == 4

    clean = [hb for hb in move.hitboxes if hb.active_start == 4]
    late = [hb for hb in move.hitboxes if hb.active_start == 6]
    assert len(clean) == 2 and len(late) == 2

    # Clean window [4, 5].
    assert all(hb.active_end == 5 for hb in clean)
    assert tuple(hb.damage for hb in clean) == (11.0, 11.0)
    # Late window [6, 9].
    assert all(hb.active_end == 9 for hb in late)
    assert tuple(hb.damage for hb in late) == (10.0, 10.0)
    # Shared across both windows.
    for hb in move.hitboxes:
        assert hb.angle == 55
        assert hb.base_knockback == 0.0
        assert hb.knockback_growth == 100.0
    assert tuple(hb.circle.r for hb in clean) == (19, 25)
    assert tuple(hb.circle.r for hb in late) == (19, 25)


def test_nalio_uair_spawns_two_windows_through_player_update():
    """End-to-end (#204): the clean window spawns one Attack on frame 4 and the
    late window a SEPARATE Attack on frame 6."""
    from pycats.core.input import InputFrame
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    p._clock.start(load_fighter_data("nalio").moves["uair"])

    seen: set[int] = set()
    appeared: list[tuple[int, float]] = []  # (frame, first-box damage)
    for frame in range(1, 11):
        p.update(neutral, [], group)
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].damage))

    assert appeared == [(4, 11.0), (6, 10.0)], "clean then late, separate Attacks"


def test_nalio_dair_is_pm_attackairlw():
    """Nalio's d-air is PM3.6 Mario AttackAirLw (rukaidata) — a looping drill that
    composes ALL THREE gates: #204 windows (two damage phases), #213 rehit_rate
    (the loop), #211 WDSK (set-knockback launch). Active 7-27 (startup 6 / active
    21), IASA 35 (recovery 8). Phase 1 [7,15]: 3 dmg, WDSK 55, KBG 160. Phase 2
    [16,27]: 2 dmg, WDSK 30, KBG 100. Both angle 85, BKB 0. Able-to-fail: an absent
    key falls back to nair; a None rehit_rate breaks the loop."""
    move = load_fighter_data("nalio").moves["dair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (6, 21, 8)
    assert move.rehit_rate is not None, "d-air is a looping drill"
    assert len(move.hitboxes) == 2

    p1 = next(hb for hb in move.hitboxes if hb.active_start == 7)
    p2 = next(hb for hb in move.hitboxes if hb.active_start == 16)

    assert (p1.active_start, p1.active_end) == (7, 15)
    assert p1.damage == 3.0 and p1.angle == 85
    assert p1.base_knockback == 0.0
    assert p1.set_knockback == 55 and p1.knockback_growth == 160.0

    assert (p2.active_start, p2.active_end) == (16, 27)
    assert p2.damage == 2.0 and p2.angle == 85
    assert p2.base_knockback == 0.0
    assert p2.set_knockback == 30 and p2.knockback_growth == 100.0


def test_nalio_dair_spawns_looping_windows_through_player_update():
    """End-to-end: the real d-air spawns phase 1 on frame 7 and phase 2 on frame
    16 as separate Attacks, each carrying the move's rehit_rate so they loop."""
    from pycats.core.input import InputFrame
    move = load_fighter_data("nalio").moves["dair"]
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    p._clock.start(move)

    seen: set[int] = set()
    appeared: list[tuple[int, float, int]] = []  # (frame, dmg, rehit_rate)
    for frame in range(1, 28):
        p.update(neutral, [], group)
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].damage, atk.rehit_rate))

    assert appeared == [(7, 3.0, move.rehit_rate), (16, 2.0, move.rehit_rate)]


def test_nalio_nair_is_pm_neutral_air():
    """Nalio's neutral-air is PM3.6 Mario AttackAirN (#136), clean-hit form on the
    #130 multi-hitbox engine: 2 simultaneous hitboxes, in_air, damage 12, BKB 20,
    KBG 100, r15 (size 2.73 u × 5.4), startup 2 / active 4 / recovery 40. Angle is
    a literal placeholder for the Sakurai sentinel 361 (deferred). Able-to-fail:
    missing nair / wrong values red this."""
    move = load_fighter_data("nalio").moves["nair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (2, 4, 40)
    assert len(move.hitboxes) == 2
    for hb in move.hitboxes:
        assert hb.damage == 12.0
        assert hb.base_knockback == 20.0
        assert hb.knockback_growth == 100.0
        assert hb.circle.r == 15


def test_default_cat_attack_is_unchanged():
    """Regression guard: branching Nalio must NOT alter the default cat's jab
    (the sim/golden path), which stays the placeholder (dmg 10, angle 0)."""
    hb = DEFAULT_FIGHTER_DATA.moves["attack"].hitboxes[0]
    assert hb.damage == 10.0
    assert hb.angle == 0


def test_player_named_nalio_loads_nalio_data():
    """End-to-end seam: a Player given char_name='nalio' loads Nalio's distinct
    moveset, not the default jab. Able-to-fail: without the loader branch the
    Player would get the default cat (angle 0)."""
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio")
    assert p.fighter_data is load_fighter_data("nalio")
    assert p.fighter_data.moves["attack"].hitboxes[0].angle == 80
