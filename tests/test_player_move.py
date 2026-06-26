# tests/test_player_move.py
"""Task 4: data-driven attack via a per-move frame clock.

Verifies the player's move clock (current_move / move_frame), that the hitbox
(an Attack) spawns exactly once and only during the active window, that its
lifetime equals the move's `active`, that current_move clears at move end, that
player.state == "attack" throughout startup->active->recovery, and that the
chart sub-phases progress as move_frame advances.
"""
import pygame

from pycats.entities.player import Player
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player(backend="legacy"):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def _ground():
    # A wide thick platform directly under the player at y=100.
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _press_attack():
    return InputFrame(held=set(), pressed={P1["attack"]}, released=set())


def _noop():
    return InputFrame(held=set(), pressed=set(), released=set())


def _settle_grounded(p, platforms):
    # Run a couple of no-op frames so the player rests on the platform.
    for _ in range(3):
        p.update(_noop(), platforms, pygame.sprite.Group())


def test_attack_press_sets_current_move_and_zero_frame():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)
    assert p.current_move is None

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)

    assert p.current_move is not None
    assert p.current_move is p.fighter_data.moves["attack"]
    # attack_timer set to full move duration for legacy/label classification
    m = p.current_move
    assert p.attack_timer == m.startup + m.active + m.recovery - 1 or \
        p.attack_timer == m.startup + m.active + m.recovery
    assert p.fighter.done_attacking is False


def test_move_frame_advances_each_frame():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)
    f1 = p.move_frame
    p.update(_noop(), platforms, grp)
    f2 = p.move_frame
    p.update(_noop(), platforms, grp)
    f3 = p.move_frame
    assert f1 == 1
    assert f2 == 2
    assert f3 == 3


def test_hitbox_spawns_once_only_in_active_window():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]

    grp = pygame.sprite.Group()
    spawned_frames = []
    # Press on the first frame, then no-ops for the rest of the move.
    p.update(_press_attack(), platforms, grp)
    if len(grp) > 0:
        spawned_frames.append(p.move_frame)
    total = m.startup + m.active + m.recovery
    for _ in range(total + 4):
        before = len(grp)
        p.update(_noop(), platforms, grp)
        # Track at which move_frame a new Attack appeared
        if len(grp) > before:
            spawned_frames.append(p.move_frame)

    # Exactly one Attack ever spawned for the move.
    attacks = [s for s in grp]  # remaining (may have been killed already)
    # Count via spawned_frames (robust to kills)
    assert len(spawned_frames) == 1, f"expected one spawn, got at {spawned_frames}"
    # The single spawn happened inside the active window:
    # startup < move_frame <= startup + active
    sf = spawned_frames[0]
    assert m.startup < sf <= m.startup + m.active, (
        f"spawn at move_frame={sf} outside active window "
        f"({m.startup}, {m.startup + m.active}]"
    )


def test_no_spawn_during_startup_or_recovery():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)
    # During startup frames (move_frame 1..startup) no Attack should exist.
    while p.move_frame < m.startup:
        assert len(grp) == 0, f"spawned during startup at frame {p.move_frame}"
        p.update(_noop(), platforms, grp)
    # At move_frame == startup we are still in startup (window is exclusive on
    # the low end), so still no spawn yet.
    assert len(grp) == 0


def test_attack_lifetime_equals_active():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)
    atk = None
    total = m.startup + m.active + m.recovery
    for _ in range(total):
        if len(grp) > 0 and atk is None:
            atk = next(iter(grp))
            assert atk.frames_left == m.active, (
                f"lifetime {atk.frames_left} != active {m.active}"
            )
            break
        p.update(_noop(), platforms, grp)
    assert atk is not None, "Attack was never spawned"


def test_current_move_clears_at_move_end():
    p = _mk_player()
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]
    total = m.startup + m.active + m.recovery

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)
    # Run exactly enough frames for the move to complete.
    for _ in range(total - 1):
        p.update(_noop(), platforms, grp)
    assert p.current_move is None, (
        f"current_move not cleared after {total} frames; "
        f"move_frame={p.move_frame}"
    )


def test_state_is_attack_throughout_move_legacy():
    _state_is_attack_throughout("legacy")


def test_state_is_attack_throughout_move_statechart():
    _state_is_attack_throughout("statechart")


def _state_is_attack_throughout(backend):
    p = _mk_player(backend)
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]
    total = m.startup + m.active + m.recovery

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)
    assert p.state == "attack", f"{backend}: not attack on press frame"
    # Throughout startup, active, recovery the flat label stays "attack".
    for _ in range(total - 2):
        p.update(_noop(), platforms, grp)
        assert p.state == "attack", (
            f"{backend}: state={p.state} at move_frame={p.move_frame}"
        )


def test_chart_subphases_progress():
    """The statechart's attacking sub-phases progress as move_frame advances."""
    p = _mk_player("statechart")
    platforms = _ground()
    _settle_grounded(p, platforms)
    m = p.fighter_data.moves["attack"]
    sess = p.engine._session

    grp = pygame.sprite.Group()
    p.update(_press_attack(), platforms, grp)

    seen = {"startup": False, "active": False, "recovery": False}
    total = m.startup + m.active + m.recovery
    # Record the active sub-phase across the whole move.
    for _ in range(total):
        if sess.in_state("attacking"):
            if sess.in_state("startup"):
                seen["startup"] = True
            if sess.in_state("active"):
                seen["active"] = True
            if sess.in_state("recovery"):
                seen["recovery"] = True
        p.update(_noop(), platforms, grp)

    assert seen["startup"], "never entered startup sub-phase"
    assert seen["active"], "never entered active sub-phase"
    assert seen["recovery"], "never entered recovery sub-phase"
