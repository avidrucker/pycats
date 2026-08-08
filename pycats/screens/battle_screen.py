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

from ..characters.roster import palette_for
from ..config import (
    BG_COLOR,
    INITIAL_LIVES,
    PLAYER1_START_X,
    PLAYER1_START_Y,
    PLAYER2_START_X,
    PLAYER2_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from ..core.physics import resolve_player_push
from ..entities import Player
from ..entities.ledge import ledges_from_platforms
from ..loadout import Selection, Skin, assign_distinct_skins, build_fighter, character_for, starting_lives
from ..render_battle import (
    draw_controls,
    draw_hud,
    draw_input_history,
    draw_pause_hint,
    render_attacks,
    render_battle,
    render_hitbox_overlay,
)
from ..shell.input_history import InputHistory
from ..storage import runtime_settings
from ..systems import hit_resolution
from ..systems.win_condition import winner_loser


class BattleScreen:
    """Owns battle state + the per-frame sim. Render lives in game.py for now (2b)."""

    def __init__(self, p1_keys, p2_keys):
        self.p1_keys = p1_keys
        self.p2_keys = p2_keys
        self.player1 = None
        self.player2 = None
        # #1202: each player's drafted starting stock count, so a rematch (reset)
        # re-applies the Phoenix bonus instead of snapping back to INITIAL_LIVES.
        # Defaults to INITIAL_LIVES until create_from_selection resolves the draft.
        self._p1_start_lives = INITIAL_LIVES
        self._p2_start_lives = INITIAL_LIVES
        self.players = pygame.sprite.Group()
        self.attacks = pygame.sprite.Group()
        self._ledges = None  # solid-edge ledges (#14), built lazily from platforms
        # Per-fighter input-history buffers (#21) — a render-only side buffer fed
        # on the press-edge; does not participate in the sim.
        self.p1_history = InputHistory()
        self.p2_history = InputHistory()

    def create_from_selection(self, p1_char, p2_char, p1_palette=None, p2_palette=None, p1_cards=(), p2_cards=()):
        """Build the two fighters from the selected ARCHETYPES (#268, #127 Part 1):
        cosmetic from the chosen OG-skin palette (#650, Part 3), fighter data from
        load_fighter_data(key). char_name stays "P1"/"P2" so win-attribution
        (stats_print) and name rendering are unchanged.

        p1_palette/p2_palette are chosen OG-skin keys from the char-select skin cycler;
        None → the archetype's own default palette, so the no-cycle path is byte-identical
        to before (golden/parity-safe)."""
        # Phase 1b (#672): build through the domain build_fighter port. Cosmetics
        # still resolve via palette_for (the chosen OG-skin, else the archetype's
        # default) and mechanics via the char key, wrapped as a Selection, so every
        # Player is byte-identical; Phase 2 migrates to resolve_selection + named cats.
        # #1202: an optional per-player drafted-card list rides the Selection. Defaults
        # to () → starting_lives returns INITIAL_LIVES → the no-draft path is byte-identical
        # (render-parity + goldens safe). The stocks seam is match-level (fighter.lives), so
        # it applies below as a starting-lives hook, not by build_fighter's FighterData patch.
        sel1 = Selection(
            character_for(p1_char),
            Skin.from_palette_dict(p1_palette or p1_char or "", palette_for(p1_palette or p1_char)),
            tuple(p1_cards),
        )
        sel2 = Selection(
            character_for(p2_char),
            Skin.from_palette_dict(p2_palette or p2_char or "", palette_for(p2_palette or p2_char)),
            tuple(p2_cards),
        )
        # #822: two players on the SAME character with no explicit skin cycle would otherwise
        # render identically (both skins come from palette_for(char_key)). De-collide through
        # the #748/#755 domain layer — the same rule #718 shipped for the sim: P2 falls to the
        # next available skin in that character's pool. Different-character pairs and explicit
        # distinct cycles pass through untouched (assign_distinct_skins only touches a
        # same-character skin-key collision), so the render stays byte-identical there.
        sel1, sel2 = assign_distinct_skins((sel1, sel2))
        built1 = build_fighter(sel1)
        built2 = build_fighter(sel2)

        self.player1 = Player(
            PLAYER1_START_X,
            PLAYER1_START_Y,
            self.p1_keys,
            built1.skin.color,
            eye_color=built1.skin.eye_color,
            char_name="P1",
            facing_right=True,
            fighter_data=built1.fighter_data,
            character=sel1.character,
        )
        self.player2 = Player(
            PLAYER2_START_X,
            PLAYER2_START_Y,
            self.p2_keys,
            built2.skin.color,
            eye_color=built2.skin.eye_color,
            char_name="P2",
            facing_right=False,
            fighter_data=built2.fighter_data,
            character=sel2.character,
        )
        self.player1.stripe_color = built1.skin.stripe_color
        self.player2.stripe_color = built2.skin.stripe_color
        # #1202: apply the match-level stocks seam and remember each starting count so
        # reset() re-applies it. No cards → INITIAL_LIVES → byte-identical to today.
        self._p1_start_lives = starting_lives(sel1)
        self._p2_start_lives = starting_lives(sel2)
        self.player1.fighter.lives = self._p1_start_lives
        self.player2.fighter.lives = self._p2_start_lives
        self.players = pygame.sprite.Group(self.player1, self.player2)

    def reset(self):
        """Match-scoped reset (full lives, cleared stats, FSM->idle); per-life/spawn
        state is owned by Player.reset_to_spawn(). Mirrors game.py's reset_game."""
        if self.player1 and self.player2:
            for p, start_lives in (
                (self.player1, self._p1_start_lives),
                (self.player2, self._p2_start_lives),
            ):
                p.reset_to_spawn()  # #286: Player-level authoritative reset (clock/tail too)
                p.fighter.lives = start_lives  # #1202: re-apply the drafted starting count
                p.fighter.attacks_made = 0
                p.fighter.hits_landed = 0
                p.fighter.suicides = 0
                p.engine.force("idle")
        self.attacks.empty()
        self._ledges = None  # rebuilt next step (clears edge occupancy; #14)
        self.p1_history = InputHistory()  # fresh input-history buffers per match (#21)
        self.p2_history = InputHistory()

    def step(self, frame_input, platforms):
        """One frame of battle sim — SAME primitives/order as the old inline block."""
        if self._ledges is None:
            self._ledges = ledges_from_platforms(platforms)  # build once, persist (#14)
        # Input-history capture (#21, #875) — record this frame's pressed + held
        # per keymap before the sim runs; a side buffer that never feeds
        # fighter/attack state. Held is logged too so the grid tells a fresh press
        # from a still-held key (#875).
        pressed = getattr(frame_input, "pressed", ())
        held = getattr(frame_input, "held", ())
        self.p1_history.record(pressed, held, self.p1_keys)
        self.p2_history.record(pressed, held, self.p2_keys)
        for p in self.players:
            p.update(frame_input, platforms, self.attacks, self._ledges)
        resolve_player_push(list(self.players), platforms)
        self.attacks.update(platforms)  # #266: projectiles need platforms to bounce
        hit_resolution.process_hits(self.players, self.attacks)

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
            # Fighter-controls display (#284) is now pause-only (#977) — see
            # render_paused; it no longer draws during live play.
            # Input-history strip (#21), gated on the live toggle (default ON).
            if runtime_settings.show_input_history():
                draw_input_history(surface, self.p1_history, "P1")
                draw_input_history(surface, self.p2_history, "P2", topright=True)

    def render(self, surface, platforms):
        """Render one live battle frame onto `surface` (the playing branch's draw
        block) + the static 'P: Pause Game' battle-HUD hint (#279). The shell chrome
        (FPS/fullscreen/debug text) reads loop globals, not battle state, so it stays
        out of here — game.py calls render_battle.draw_shell_chrome for that."""
        self._draw_battle(surface, platforms)
        draw_pause_hint(surface)

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
            # Fighter-controls display (#284) is pause-only now (#977): draw it on the
            # frozen background here, gated on show_controls (default ON), so the
            # per-fighter key scheme is visible while paused instead of during play.
            if runtime_settings.show_controls():
                draw_controls(background, self.player1, "P1")
                draw_controls(background, self.player2, "P2", topright=True)
        pause_menu.render(surface, background)
