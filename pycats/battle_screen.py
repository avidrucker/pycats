"""BattleScreen — the in-game battle as a managed screen object (slice 2 of #100).

De-globalizes game.py's battle: owns the battle state (player1/2, players, attacks)
and the per-frame sim step that was an inline block in the `while running` loop, so
`playing`/`pause` can be driven like the other screen managers instead of being the
loop's default branch. Render extraction is slice 2b; this slice is sim + state only.

The sim step performs the SAME primitives in the SAME order as the old inline block
(and as sim/runner.py's golden-covered loop): per-player update -> push resolution ->
attack update -> hit resolution.
"""
from __future__ import annotations

import pygame

from .config import (
    CAT_CHARACTERS,
    INITIAL_LIVES,
    PLAYER1_START_X,
    PLAYER1_START_Y,
    PLAYER2_START_X,
    PLAYER2_START_Y,
)
from .core.physics import resolve_player_push
from .entities import Player
from .systems import combat
from .systems.win_condition import winner_loser


class BattleScreen:
    """Owns battle state + the per-frame sim. Render lives in game.py for now (2b)."""

    def __init__(self, p1_keys, p2_keys):
        self.p1_keys = p1_keys
        self.p2_keys = p2_keys
        self.player1 = None
        self.player2 = None
        self.players = pygame.sprite.Group()
        self.attacks = pygame.sprite.Group()

    def create_from_selection(self, p1_char, p2_char):
        """Build the two fighters from the selected characters (statechart engine,
        per ADR-0002), mirroring game.py's create_players_from_selection."""
        p1_data = CAT_CHARACTERS[p1_char]
        p2_data = CAT_CHARACTERS[p2_char]

        self.player1 = Player(
            PLAYER1_START_X, PLAYER1_START_Y, self.p1_keys,
            p1_data["color"], eye_color=p1_data["eye_color"],
            char_name="P1", facing_right=True,
        )
        self.player2 = Player(
            PLAYER2_START_X, PLAYER2_START_Y, self.p2_keys,
            p2_data["color"], eye_color=p2_data["eye_color"],
            char_name="P2", facing_right=False,
        )
        self.player1.stripe_color = p1_data["stripe_color"]
        self.player2.stripe_color = p2_data["stripe_color"]
        self.players = pygame.sprite.Group(self.player1, self.player2)

    def reset(self):
        """Match-scoped reset (full lives, cleared stats, FSM->idle); per-life/spawn
        state is owned by Player.reset_to_spawn(). Mirrors game.py's reset_game."""
        if self.player1 and self.player2:
            for p in (self.player1, self.player2):
                p.fighter.reset_to_spawn()
                p.fighter.lives = INITIAL_LIVES
                p.fighter.attacks_made = 0
                p.fighter.hits_landed = 0
                p.fighter.suicides = 0
                p.engine.force("idle")
        self.attacks.empty()

    def step(self, frame_input, platforms):
        """One frame of battle sim — SAME primitives/order as the old inline block."""
        for p in self.players:
            p.update(frame_input, platforms, self.attacks)
        resolve_player_push(list(self.players))
        self.attacks.update()
        combat.process_hits(self.players, self.attacks)

    def winner(self):
        """(winner, loser) or (None, None) — the shared win-condition rule."""
        return winner_loser((self.player1, self.player2))
