"""Issue #1 — players landing on each other push apart on X, never lock on Y.

Project M "jostle": fighter-vs-fighter collision separates horizontally; there is
no vertical pushbox between fighters (vertical overlap is allowed). These tests
drive the real loop (Player.update + resolve_player_push) with two players
dropped onto the same spot and assert they separate on X and are never
repositioned / velocity-cancelled on Y.

Repro/proof of the original defect: repros/repro_issue_1.py.
"""
import pygame

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.core.physics import resolve_player_push
from pycats.config import PLAYER_SIZE

PW = PLAYER_SIZE[0]  # player width (40)

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
          attack=pygame.K_SLASH, special=pygame.K_PERIOD, shield=pygame.K_COMMA)


def _floor():
    # A wide thick (solid) platform; top at y=410.
    return [Platform(pygame.Rect(0, 410, 960, 80), thin=False)]


def _two_players():
    p1 = Player(0, 0, P1, (255, 160, 64), eye_color=(0, 0, 0),
                char_name="P1", facing_right=True, state_backend="statechart")
    p2 = Player(0, 0, P2, (160, 160, 160), eye_color=(0, 0, 0),
                char_name="P2", facing_right=False, state_backend="statechart")
    return p1, p2


def _drop_on_same_spot(p1, p2, top):
    p2.rect.midbottom = (482, top)         # settled on the floor, centre
    p2.vel = pygame.Vector2(0, 0)
    p2.on_ground = True
    p1.rect.midbottom = (478, top - 70)    # just above, almost identical x
    p1.vel = pygame.Vector2(0, 3)          # falling onto P2


def _noop():
    return InputFrame(set(), set(), set())


def _settle(p1, p2, platforms, frames=40):
    attacks = pygame.sprite.Group()
    group = pygame.sprite.Group(p1, p2)
    for _ in range(frames):
        for pl in group:
            pl.update(_noop(), platforms, attacks)
        resolve_player_push([p1, p2])


def test_stacked_players_separate_on_x():
    floor = _floor()
    p1, p2 = _two_players()
    _drop_on_same_spot(p1, p2, floor[0].rect.top)
    _settle(p1, p2, floor)

    gap = abs(p1.rect.centerx - p2.rect.centerx)
    assert not p1.rect.colliderect(p2.rect), "players still overlapping (locked)"
    assert gap >= PW, f"players not pushed apart on X (gap={gap}, need >= {PW})"


def test_landing_players_rest_on_floor_not_stacked():
    # Both must settle ON the floor, side by side — neither pinned to the
    # other's head (the old Y-lock: bottom == other.top - 1).
    floor = _floor()
    top = floor[0].rect.top
    p1, p2 = _two_players()
    _drop_on_same_spot(p1, p2, top)
    _settle(p1, p2, floor)

    assert p1.rect.bottom == top and p2.rect.bottom == top, \
        "a player did not settle on the floor (left stacked on a head)"
    assert p1.rect.bottom != p2.rect.top - 1 and p2.rect.bottom != p1.rect.top - 1, \
        "a player is Y-locked onto the other's head"


def test_push_never_touches_vertical_velocity():
    # The resolver must not mutate vel.y (the old vertical branch zeroed/halved
    # it). Overlap two players and call the push once with sentinel Y velocities.
    p1, p2 = _two_players()
    p1.rect.midbottom = (480, 410)
    p2.rect.midbottom = (490, 410)   # overlaps p1 on X and Y
    p1.vel = pygame.Vector2(0, 7.0)
    p2.vel = pygame.Vector2(0, -3.0)
    assert p1.rect.colliderect(p2.rect)  # guard: scenario actually triggers push

    resolve_player_push([p1, p2])

    assert p1.vel.y == 7.0 and p2.vel.y == -3.0, "push modified vertical velocity"


class _FakeFighter:
    """Minimal stand-in: resolve_player_push only reads .state/.rect/.vel.
    Used because Player.state is a read-only property we can't force to 'dodge'
    without a full dodge input sequence."""
    def __init__(self, midbottom, state="idle"):
        self.rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        self.rect.midbottom = midbottom
        self.vel = pygame.Vector2(0, 0)
        self.state = state


def test_dodge_player_skips_push():
    # A fighter in the "dodge" state is intangible to the push (preserved guard).
    a = _FakeFighter((480, 410), state="dodge")
    b = _FakeFighter((490, 410))
    assert a.rect.colliderect(b.rect)  # guard: they overlap
    before = (a.rect.x, b.rect.x)

    resolve_player_push([a, b])

    assert (a.rect.x, b.rect.x) == before, "dodging fighter was pushed"


def test_perfectly_stacked_separates_deterministically():
    # Identical centerx (worst case): one push must move them apart on X the same
    # way every time — no jitter, no giant shove, deterministic tie-break.
    def push_once():
        a, b = _two_players()
        a.rect.midbottom = (480, 410)
        b.rect.midbottom = (480, 410)   # exactly stacked
        resolve_player_push([a, b])
        return a.rect.centerx, b.rect.centerx

    r1 = push_once()
    r2 = push_once()
    assert r1 == r2, "tie-break is non-deterministic"
    assert r1[0] != r1[1], "perfectly-stacked players did not separate on X"
