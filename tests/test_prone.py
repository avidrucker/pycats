"""Prone / knockdown state (#13).

Prone is a new driven state (both engine backends, in parity): force-entry via
`Player.force_prone(frames)` (mirroring how shield-break drives `stun`), the only
self-initiated action is standing up, and the getup window is the `prone_timer`
counting to 0 -> stand to idle (on ground) / fall (airborne). The automatic
landing-velocity trigger is #145; getup-roll / getup-attack are #146.

The golden replay never forces prone, so existing goldens are unaffected; these
tests pin the new behaviour.
"""
import pygame

from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _mk(backend="legacy"):
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def _ground():
    # Wide thick (solid) platform under the player at y=100.
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _settle(p, plats):
    grp = pygame.sprite.Group()
    for _ in range(3):
        p.update(_frame(), plats, grp)


def _run(p, plats, frame, n=1):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(frame, plats, grp)


# --- Slice 1: force-entry into prone (both backends) -------------------------

def test_force_prone_enters_prone_both_backends():
    for backend in ("legacy", "statechart"):
        p = _mk(backend)
        plats = _ground()
        _settle(p, plats)
        assert p.state == "idle", backend
        p.force_prone(20)
        assert p.state == "prone", backend


# --- Slice 2: getup window — prone persists, then stands to idle --------------

def test_prone_persists_then_stands_up_both_backends():
    for backend in ("legacy", "statechart"):
        p = _mk(backend)
        plats = _ground()
        _settle(p, plats)
        p.force_prone(5)
        # holds prone while the getup window runs down...
        for _ in range(4):
            _run(p, plats, _frame())
            assert p.state == "prone", backend
        # ...then the window elapses and the fighter stands up.
        _run(p, plats, _frame())
        assert p.state == "idle", backend


# --- Slice 3: only stand-up is allowed — actions are locked out --------------

def test_prone_locks_out_actions_both_backends():
    for backend in ("legacy", "statechart"):
        p = _mk(backend)
        plats = _ground()
        _settle(p, plats)
        p.force_prone(10)
        # Mashing attack must not start a move...
        _run(p, plats, _frame("attack"), n=3)
        assert p.state == "prone", backend
        assert p.attack_timer == 0, backend
        # ...and mashing jump ('up') must not launch the fighter off the ground.
        _run(p, plats, _frame("up"), n=3)
        assert p.state == "prone", backend
        assert p.fighter.on_ground, backend


# --- Slice 4: prone runtime is byte-identical across both backends ------------

def test_prone_state_sequence_parity_both_backends():
    """A force_prone + getup scenario must produce the same per-frame state
    label on legacy and statechart, and must actually reach prone (so the
    parity check is meaningful)."""
    legacy = _mk("legacy")
    state = _mk("statechart")
    plats = _ground()
    _settle(legacy, plats)
    _settle(state, plats)
    legacy.force_prone(6)
    state.force_prone(6)
    seq_legacy, seq_state = [], []
    for _ in range(10):
        _run(legacy, plats, _frame())
        _run(state, plats, _frame())
        seq_legacy.append(legacy.state)
        seq_state.append(state.state)
    assert seq_legacy == seq_state, f"{seq_legacy} != {seq_state}"
    assert "prone" in seq_legacy, "scenario never reached prone — parity is vacuous"
