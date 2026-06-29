# pycats/sim/runner.py
"""Headless deterministic battle runner. Drives the exact real per-frame loop
(game.py:702-709) from a scripted input timeline through the statechart engine,
producing per-frame snapshots for golden checks and benchmarking."""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

if not pygame.get_init():
    pygame.init()

from ..config import (  # noqa: E402
    THICK_PLAT_DICT, THIN_PLAT_DICT_L, THIN_PLAT_DICT_R,
    PLAYER1_START_X, PLAYER1_START_Y, PLAYER2_START_X, PLAYER2_START_Y,
    CAT_CHARACTERS,
)
from ..entities import Platform, Player  # noqa: E402
from ..systems import combat  # noqa: E402
from ..core.physics import resolve_player_push  # noqa: E402
from ..systems.match_engine import make_match_engine  # noqa: E402
from .input_script import default_timeline  # noqa: E402
from ..core.input import merge_frames  # noqa: E402

P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP,
               down=pygame.K_DOWN, attack=pygame.K_SLASH, special=pygame.K_PERIOD,
               shield=pygame.K_COMMA)
KEYMAPS = [P1_KEYS, P2_KEYS]


def build_stage():
    return [
        Platform(pygame.Rect(THICK_PLAT_DICT["x"], THICK_PLAT_DICT["y"],
                             THICK_PLAT_DICT["w"], THICK_PLAT_DICT["h"]), thin=False),
        Platform(pygame.Rect(THIN_PLAT_DICT_L["x"], THIN_PLAT_DICT_L["y"],
                             THIN_PLAT_DICT_L["w"], THIN_PLAT_DICT_L["h"]), thin=True),
        Platform(pygame.Rect(THIN_PLAT_DICT_R["x"], THIN_PLAT_DICT_R["y"],
                             THIN_PLAT_DICT_R["w"], THIN_PLAT_DICT_R["h"]), thin=True),
    ]


def build_players():
    c1 = CAT_CHARACTERS["calico"]
    c2 = CAT_CHARACTERS["tabby"]
    p1 = Player(PLAYER1_START_X, PLAYER1_START_Y, P1_KEYS, c1["color"],
                eye_color=c1["eye_color"], char_name="P1", facing_right=True)
    p2 = Player(PLAYER2_START_X, PLAYER2_START_Y, P2_KEYS, c2["color"],
                eye_color=c2["eye_color"], char_name="P2", facing_right=False)
    p1.stripe_color = c1["stripe_color"]
    p2.stripe_color = c2["stripe_color"]
    return p1, p2, pygame.sprite.Group(p1, p2)


def snapshot(players, attacks, match):
    parts = []
    for p in players:
        parts.append((
            p.char_name, p.state, p.rect.x, p.rect.y,
            round(p.fighter.vel.x, 6), round(p.fighter.vel.y, 6), p.fighter.on_ground,
            round(p.fighter.percent, 6), round(p.fighter.shield_hp, 6), p.fighter.lives, p.fighter.is_alive,
            p.fighter.jumps_remaining, p.fighter.dodge_timer, p.fighter.hurt_timer, p.fighter.stun_timer,
            p.attack_timer, p.fighter.invulnerable_timer, p.fighter.facing_right, p.fighter.invulnerable,
            # Task 6: new observable state fields (appended to preserve existing indices)
            p.defensive_status,
            p.move_frame,
        ))
    atk = tuple(sorted(
        (a.rect.x, a.rect.y, a.frames_left, a.owner.char_name, a.active,
         round(a.hit_cx, 6), round(a.hit_cy, 6), round(a.hit_r, 6))
        for a in attacks
    ))
    return (tuple(parts), atk, match.phase, match.winner)


def run_battle(frames=None, frame_inputs=None, presenter=None,
               controller=None, stop_on_match_over=False, controllers=None):
    """Run the headless battle.

    Inputs come from `controller(p1, p2, frame) -> InputFrame` when given,
    otherwise from `frame_inputs` (defaulting to the scripted DEFAULT timeline).
    A controller is for live/generated battles (e.g. a chase bot); capture its
    emitted frames to freeze a deterministic input list for parity tests.
    `stop_on_match_over=True` ends the run the frame the match resolves.

    `controllers=(c1, c2)` drives BOTH players from a controller per player
    (either may be None for an idle player). Each controller is called on the
    same frame-start snapshot and their emitted frames are merged by set-union;
    this is unambiguous because P1/P2 keymaps are disjoint. To freeze a 2-NPC
    battle for replay, capture the per-controller `.emitted` lists and zip them
    through `merge_frames`. Pass at most one of `controller` / `controllers`.
    """
    if controller is not None and controllers is not None:
        raise ValueError("pass at most one of `controller` / `controllers`")
    if controller is None and controllers is None and frame_inputs is None:
        frame_inputs = default_timeline(KEYMAPS)
    if frames is None:
        frames = len(frame_inputs) if frame_inputs is not None else 0

    platforms = build_stage()
    p1, p2, players = build_players()
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2])

    snaps = []
    for f in range(frames):
        if controllers is not None:
            # Call every controller on the SAME frame-start snapshot, THEN merge
            # and apply — so neither sees the other's mutation mid-frame.
            fi = merge_frames(
                c(p1, p2, f) if c is not None else _empty_frame()
                for c in controllers
            )
        elif controller is not None:
            fi = controller(p1, p2, f)
        else:
            fi = frame_inputs[f] if f < len(frame_inputs) else _empty_frame()
        for p in players:
            p.update(fi, platforms, attacks)
        resolve_player_push(list(players))
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        snaps.append(snapshot(players, attacks, match))
        if presenter is not None:
            presenter.show(platforms, players, attacks, f)
        if stop_on_match_over and match.phase == "match_over":
            break
    if presenter is not None:
        presenter.close()
    return snaps


def _empty_frame():
    from ..core.input import InputFrame
    return InputFrame(held=set(), pressed=set(), released=set())
