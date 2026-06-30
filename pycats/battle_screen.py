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
    BG_COLOR,
    CAT_CHARACTERS,
    INITIAL_LIVES,
    PLAYER1_START_X,
    PLAYER1_START_Y,
    PLAYER2_START_X,
    PLAYER2_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .core.physics import resolve_player_push
from .entities import Player
from .entities.ledge import ledges_from_platforms
from .render_battle import (
    draw_controls,
    draw_hud,
    render_attacks,
    render_battle,
    render_hitbox_overlay,
)
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
        self._ledges = None  # solid-edge ledges (#14), built lazily from platforms

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
        self._ledges = None  # rebuilt next step (clears edge occupancy; #14)

    def step(self, frame_input, platforms):
        """One frame of battle sim — SAME primitives/order as the old inline block."""
        if self._ledges is None:
            self._ledges = ledges_from_platforms(platforms)  # build once, persist (#14)
        for p in self.players:
            p.update(frame_input, platforms, self.attacks, self._ledges)
        resolve_player_push(list(self.players))
        self.attacks.update()
        combat.process_hits(self.players, self.attacks)

    def winner(self):
        """(winner, loser) or (None, None) — the shared win-condition rule."""
        return winner_loser((self.player1, self.player2))

    def _draw_battle(self, surface, platforms):
        """Fill + fighters + attacks + HUD/controls — the shared battle composite.
        SAME calls/order as game.py's old inline playing block (#205, slice 2b)."""
        surface.fill(BG_COLOR)
        render_battle(surface, self.players, platforms)
        render_attacks(surface, self.attacks)
        # Hit/hurtbox debug overlay (#219) — above fighters/attacks, gated on the
        # live toggle (default OFF, so this is a no-op until a dev flips it on).
        render_hitbox_overlay(surface, self.players, self.attacks)
        if self.player1 and self.player2:
            draw_hud(surface, self.player1, "P1")
            draw_hud(surface, self.player2, "P2", topright=True)
            draw_controls(surface, self.player1, "P1")
            draw_controls(surface, self.player2, "P2", topright=True)

    def render(self, surface, platforms):
        """Render one live battle frame onto `surface` (the playing branch's draw
        block). Chrome (FPS/fullscreen/pause/debug text) stays in game.py — it reads
        loop globals, not battle state."""
        self._draw_battle(surface, platforms)

    def render_paused(self, surface, platforms, pause_menu):
        """Render the pause frame: composite the FROZEN battle + HUD (no controls)
        onto an intermediate background surface, then delegate to the pause menu.
        Mirrors game.py's pause branch."""
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.fill(BG_COLOR)
        render_battle(background, self.players, platforms)
        render_attacks(background, self.attacks)
        render_hitbox_overlay(background, self.players, self.attacks)  # #219
        if self.player1 and self.player2:
            draw_hud(background, self.player1, "P1")
            draw_hud(background, self.player2, "P2", topright=True)
        pause_menu.render(surface, background)
