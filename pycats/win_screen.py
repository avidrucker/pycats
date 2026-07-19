"""
Win screen logic for the cat fighting game.

This module handles:
- Displaying match statistics
- Player confirmation system for viewing stats
- Visual feedback for player confirmations
- Handling input for stats screen progression
"""

import pygame  # type: ignore

from . import render_battle, runtime_settings, stats_print, text_utils
from .config import (
    FPS,
    P1_UI_COLOR,
    P2_UI_COLOR,
    SCREEN_WIDTH,
    TAIL_SEGMENT_LENGTH,
    TAIL_SEGMENTS,
    WIN_SCREEN_BG_COLOR,
    WIN_SCREEN_INSTRUCTION_SIZE,
    WIN_SCREEN_LINE_SPACING,
    WIN_SCREEN_PADDING,
    WIN_SCREEN_STATS_SIZE,
    WIN_SCREEN_TEXT_COLOR,
    WIN_SCREEN_TITLE_SIZE,
    YELLOW,
)

# Win-screen input timing (frames) — #446: named from inline literals.
WIN_INPUT_COOLDOWN = 15  # ignore repeat confirm/cancel presses for this long
WIN_RETURN_DELAY = 30  # after both players confirm, wait this long, then return

# --- fighter portraits (#728, design ruled in #738; research #736) -----------
# Both fighters are drawn on the win screen: seat-fixed (P1 left / P2 right by
# identity.number, NOT winner/loser), the winner raised, crowned in yellow; the
# loser dimmed. The body reuses render_battle's position-independent composite
# (_cat_body_surface via _cat_body_layers); the live tail is composed with the
# body on a 1x scratch surface, then the whole surface is scaled — so body and
# tail scale together (render_tail has no scale of its own).
#
# These are VISUAL as-of values — the #738 ruling flagged scale / raise / dim as
# adjustable ("see how we like it"); tune freely.
_PORTRAIT_SCALE = 2  # #738 Q4
_WINNER_RAISE = 50  # px the winner's body-top is drawn above the loser's (#738 Q3)
# #746: the loser's WHOLE half is scrimmed in the background colour (not a black
# body box) so the entire loser cat — body + ears + tail — fades toward the bg,
# under the stats. ~50% alpha.
_LOSER_SCRIM_ALPHA = 128
_CROWN_SCALE = 1.5  # #746: crown ~1.5x the original #728 size
_LOSER_BODY_TOP_Y = 200  # #746: both cats lowered 50px (was 150); winner sits _WINNER_RAISE above
# Seat body-center x: P1 in the left margin, P2 in the right margin of the ~420px
# centered stats table (SCREEN_WIDTH 960 -> ~270px margins). Keyed off the seat,
# never winner/loser — this is the #728 invariant the render test guards.
_SEAT_CENTER_X = {1: 135, 2: SCREEN_WIDTH - 135}


class WinScreenManager:
    """Handles win screen display and confirmation logic for both players."""

    # Ignore confirm/cancel input for this many frames after the win screen
    # first appears. The attack key that landed the killing blow is often still
    # being mashed; without this grace window it confirms instantly and bounces
    # players back to character select before they can read the stats (#10).
    INITIAL_INPUT_GRACE_FRAMES = 2 * FPS  # ~2 seconds at 60 FPS

    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Confirmation status
        self.p1_confirmed = False
        self.p2_confirmed = False

        # Input debouncing
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0

        # Delay before returning to character selection
        self.return_delay = 0

        # Match data
        self.winner = None
        self.loser = None
        self.from_pause = False  # Track if we came from pause menu

    def set_match_data(self, winner, loser, from_pause=False):
        """Set the match data for display."""
        self.winner = winner
        self.loser = loser
        self.from_pause = from_pause  # Track if we came from pause menu
        # Fighter-portrait state (#728): on-screen body rects per seat (the render
        # test's seam) and which seats have had their live tail laid out at the
        # win-screen anchor (reset once, then animated per frame — see _draw_fighter).
        self.cat_portraits = {}
        self._tail_laid_out = set()
        # Reset confirmation status for new match
        self.p1_confirmed = False
        self.p2_confirmed = False
        # Seed the cooldowns with the initial grace window so the screen ignores
        # input it just inherited from gameplay (the killing-blow attack key) for
        # ~2s before it will accept a confirmation (#10). The cooldown is consumed
        # on the same tick it reaches zero (decrement-then-check in update()), so
        # seed one extra frame to cover the full grace window.
        self.p1_input_cooldown = self.INITIAL_INPUT_GRACE_FRAMES + 1
        self.p2_input_cooldown = self.INITIAL_INPUT_GRACE_FRAMES + 1
        self.return_delay = 0

    def update(self, pressed_keys):
        """Update win screen based on player input."""
        # Decrease input cooldowns
        if self.p1_input_cooldown > 0:
            self.p1_input_cooldown -= 1
        if self.p2_input_cooldown > 0:
            self.p2_input_cooldown -= 1

        # If delay is active, count it down and don't process input
        if self.return_delay > 0:
            self.return_delay -= 1
            return  # Don't process input during delay

        # Handle P1 input
        if self.p1_input_cooldown == 0:
            if self.p1_controls["attack"] in pressed_keys:
                # Confirm viewing stats
                self.p1_confirmed = True
                self.p1_input_cooldown = WIN_INPUT_COOLDOWN
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = WIN_RETURN_DELAY
            elif self.p1_controls["special"] in pressed_keys:
                # Cancel confirmation
                self.p1_confirmed = False
                self.p1_input_cooldown = WIN_INPUT_COOLDOWN

        # Handle P2 input
        if self.p2_input_cooldown == 0:
            if self.p2_controls["attack"] in pressed_keys:
                # Confirm viewing stats
                self.p2_confirmed = True
                self.p2_input_cooldown = WIN_INPUT_COOLDOWN
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = WIN_RETURN_DELAY
            elif self.p2_controls["special"] in pressed_keys:
                # Cancel confirmation
                self.p2_confirmed = False
                self.p2_input_cooldown = WIN_INPUT_COOLDOWN

    def both_confirmed(self):
        """Check if both players have confirmed viewing the stats."""
        return self.p1_confirmed and self.p2_confirmed

    def ready_to_return(self):
        """Check if both players confirmed and the delay has passed."""
        return self.both_confirmed() and self.return_delay == 0

    def render(self, screen):
        """Render the win screen with confirmation indicators."""
        # Clear screen
        screen.fill(WIN_SCREEN_BG_COLOR)

        # Both fighters as portraits (#728) — behind the centered stats overlay;
        # they live in the left/right margins so they never collide with the text.
        self._render_fighters(screen)

        # Get formatted statistics
        match_summary = stats_print.get_match_summary(self.winner, self.loser, self.from_pause)

        y_offset = WIN_SCREEN_PADDING

        # Winner announcement — painted in the winning player's slot color (#726). The
        # winner's seat is the identity number seam (1 == P1 seat), matching stats_print.
        winner_color = P1_UI_COLOR if self.winner.identity.number == 1 else P2_UI_COLOR
        text_utils.render_text(
            screen,
            match_summary["winner_announcement"],
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_TITLE_SIZE,
            winner_color,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING  # title → final stocks

        # Final stock count
        text_utils.render_text(
            screen,
            match_summary["final_stocks"],
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING  # final-stocks → stats header

        # Game statistics header
        text_utils.render_text(
            screen,
            "Game Statistics",
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING

        # Render the stats table with pixel-perfect positioning
        stats_table_start_y = y_offset
        y_offset = self._render_stats_table(screen, match_summary["stats_table"], y_offset)

        # Draw confirmation boxes around player columns
        self._draw_confirmation_boxes(screen, stats_table_start_y, y_offset)

        # Instructions
        y_offset += WIN_SCREEN_LINE_SPACING

        # Show different instructions based on confirmation status
        if not self.both_confirmed():
            # Action hint gated by the non-battle show_screen_hints toggle (#681); the
            # P1/P2 confirmation status below is state, not a key hint, so it stays.
            if runtime_settings.show_screen_hints():
                text_utils.render_text(
                    screen,
                    "Press A to confirm viewing stats, B to cancel",
                    (SCREEN_WIDTH // 2, y_offset),
                    WIN_SCREEN_INSTRUCTION_SIZE,
                    WIN_SCREEN_TEXT_COLOR,
                    center=True,
                )
                y_offset += WIN_SCREEN_LINE_SPACING * 0.8

            # Show individual player confirmation status with Unicode/ASCII fallback
            p1_status = "✓" if self.p1_confirmed else "..."
            p2_status = "✓" if self.p2_confirmed else "..."

            # Use text_utils with Unicode support and ASCII fallback
            status_text = f"P1: [{p1_status}]    P2: [{p2_status}]"
            text_utils.text_renderer.render_text_mixed(
                status_text,
                WIN_SCREEN_INSTRUCTION_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                screen,
                (SCREEN_WIDTH // 2, y_offset),
                center=True,
            )
        else:
            # Both confirmed, show return instruction
            text_utils.render_text(
                screen,
                "Both players ready - returning to character selection...",
                (SCREEN_WIDTH // 2, y_offset),
                WIN_SCREEN_INSTRUCTION_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                center=True,
            )

    @staticmethod
    def _has_render_surface(p):
        """True when `p` exposes the appearance surface the portrait needs. The
        minimal fakes in older win-screen tests (colors/layout/stats) don't, so
        those keep rendering text-only instead of crashing on missing state."""
        f = getattr(p, "fighter", None)
        return (
            p is not None
            and hasattr(p, "tail")
            and hasattr(p, "char_color")
            and getattr(f, "stand_size", None) is not None
        )

    def _render_fighters(self, screen):
        """Draw both fighters as 2x portraits with live tails (#728).

        Seat-fixed: P1 left, P2 right by `identity.number` (never winner/loser).
        The winner is raised `_WINNER_RAISE`, crowned yellow; the loser's whole
        half is then scrimmed in the background colour so its cat fades out.
        Records each seat's on-screen body rect in `self.cat_portraits` (the test
        seam). No-op for players lacking the appearance surface (see above)."""
        self.cat_portraits = {}
        if self.winner is None or self.loser is None:
            return
        for p in (self.winner, self.loser):
            if not self._has_render_surface(p):
                continue
            seat = int(p.identity.number)
            is_winner = p is self.winner
            rect = self._draw_fighter(screen, p, seat, is_winner)
            self.cat_portraits[seat] = {"rect": rect, "is_winner": is_winner}
        # Fade the whole loser side (body + ears + tail) into the background (#746).
        # Drawn after both cats but before the stats (render() paints stats next),
        # so the stats stay fully legible on top. Keyed off the loser's SEAT: P1
        # loses -> left half, P2 loses -> right half.
        if self._has_render_surface(self.loser):
            self._draw_loser_scrim(screen, int(self.loser.identity.number))

    @staticmethod
    def _draw_loser_scrim(screen, loser_seat):
        """A background-coloured, ~50%-alpha scrim over the loser's entire half of
        the screen — fades the loser cat toward the bg. P1 (seat 1) is the left
        half, P2 (seat 2) the right."""
        half_w = SCREEN_WIDTH // 2
        x = 0 if loser_seat == 1 else half_w
        scrim = pygame.Surface((half_w, screen.get_height()), pygame.SRCALPHA)
        scrim.fill((*WIN_SCREEN_BG_COLOR, _LOSER_SCRIM_ALPHA))
        screen.blit(scrim, (x, 0))

    def _draw_fighter(self, screen, p, seat, is_winner):
        """Compose one fighter's calm body + live tail on a 1x scratch surface,
        scale it `_PORTRAIT_SCALE`x, and blit it at its seat. Returns the visible
        body's on-screen Rect. Mutated fighter state (facing / tint timers / rect)
        is saved and restored so the live battle players aren't corrupted (the
        from-pause path reuses them); the tail segments persist so it animates."""
        rb = render_battle
        fighter = p.fighter
        w, h = fighter.stand_size
        comp_w = w + 2 * rb._BODY_PAD_X
        comp_h = rb._BODY_PAD_TOP + h + rb._BODY_PAD_BOT
        tail_reach = TAIL_SEGMENTS * TAIL_SEGMENT_LENGTH  # room for the tail's swing
        scratch = pygame.Surface((comp_w + 2 * tail_reach, comp_h + tail_reach), pygame.SRCALPHA)
        comp_x = (scratch.get_width() - comp_w) // 2
        comp_y = 0
        # The body's visible sub-rect inside the padded composite → also the tail's
        # scratch-local hip anchor.
        body_local_x = comp_x + rb._BODY_PAD_X
        body_local_y = comp_y + rb._BODY_PAD_TOP

        facing_right = seat == 1  # inward: P1 (left) faces right, P2 (right) faces left
        saved = (p.rect, fighter.facing_right, fighter.hurt_timer, fighter.stun_timer, fighter.dodge_timer)
        try:
            # Force a calm, inward-facing render anchored inside the scratch surface.
            fighter.facing_right = facing_right
            fighter.hurt_timer = fighter.stun_timer = fighter.dodge_timer = 0
            p.rect = pygame.Rect(body_local_x, body_local_y, w, h)
            # Lay the tail out at the win-screen anchor once (avoids a first-frame
            # whip from the frozen battle position), then step it live each frame.
            if seat not in self._tail_laid_out:
                p.tail.reset()
                self._tail_laid_out.add(seat)
            p.tail.update(None)
            ring, body = rb._cat_body_layers(p)
            pos = (comp_x, comp_y)
            scratch.blit(ring, pos)  # silhouette ring behind
            rb.render_tail(scratch, p.tail, rb.tinted(p.char_color, p), rb.slot_accent_color(p))
            scratch.blit(body, pos)  # body + features + name in front
        finally:
            p.rect, fighter.facing_right, fighter.hurt_timer, fighter.stun_timer, fighter.dodge_timer = saved

        scaled = pygame.transform.scale(
            scratch, (scratch.get_width() * _PORTRAIT_SCALE, scratch.get_height() * _PORTRAIT_SCALE)
        )
        body_w, body_h = w * _PORTRAIT_SCALE, h * _PORTRAIT_SCALE
        body_top = _LOSER_BODY_TOP_Y - (_WINNER_RAISE if is_winner else 0)
        body_left = _SEAT_CENTER_X[seat] - body_w // 2
        # Position the scaled scratch so its (scaled) body sub-rect lands at the seat.
        screen.blit(scaled, (body_left - body_local_x * _PORTRAIT_SCALE, body_top - body_local_y * _PORTRAIT_SCALE))

        body_rect = pygame.Rect(body_left, body_top, body_w, body_h)
        if is_winner:
            self._draw_crown(screen, body_rect)
        # The loser is faded by a half-screen background scrim drawn in
        # _render_fighters after both cats — so its ears + tail fade too (#746),
        # not just a body box.
        return body_rect

    @staticmethod
    def _draw_crown(screen, body_rect):
        """A yellow crown (three triangle points on a rectangular band) above the
        winner's head — #728's win marker, scaled `_CROWN_SCALE` (#746)."""
        band_h, crown_h, gap = int(8 * _CROWN_SCALE), int(22 * _CROWN_SCALE), 8
        cw = int(body_rect.width * 0.7 * _CROWN_SCALE)
        left = body_rect.centerx - cw // 2
        band_top = body_rect.top - gap - band_h
        pygame.draw.rect(screen, YELLOW, (left, band_top, cw, band_h))
        points_top = band_top - (crown_h - band_h)
        n = 3
        for i in range(n):
            x0 = left + cw * i // n
            x1 = left + cw * (i + 1) // n
            pygame.draw.polygon(screen, YELLOW, [(x0, band_top), ((x0 + x1) // 2, points_top), (x1, band_top)])

    def _render_stats_table(self, screen, stats_table, start_y):
        """Render the stats table with pixel-perfect column alignment."""
        # Column widths in pixels
        stat_col_width = 180  # Width for stat names
        player_col_width = 100  # Width for player columns
        col_spacing = 20  # Space between columns

        # Calculate column positions
        center_x = SCREEN_WIDTH // 2
        total_width = stat_col_width + (2 * player_col_width) + (2 * col_spacing)
        table_start_x = center_x - (total_width // 2)

        # Column X positions
        stat_col_x = table_start_x
        p1_col_x = stat_col_x + stat_col_width + col_spacing
        p2_col_x = p1_col_x + player_col_width + col_spacing

        # Store column positions for confirmation boxes
        self.table_columns = {
            "stat_col_x": stat_col_x,
            "stat_col_width": stat_col_width,
            "p1_col_x": p1_col_x,
            "p1_col_width": player_col_width,
            "p2_col_x": p2_col_x,
            "p2_col_width": player_col_width,
        }

        current_y = start_y

        # Render header
        header = stats_table["header"]

        # Stat label (right-aligned)
        text_utils.render_text(
            screen,
            header["stat_label"],
            (stat_col_x + stat_col_width, current_y),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            right_align=True,
        )

        # P1 label (center-aligned) — P1's slot color (#726).
        text_utils.render_text(
            screen,
            header["p1_label"],
            (p1_col_x + player_col_width // 2, current_y),
            WIN_SCREEN_STATS_SIZE,
            P1_UI_COLOR,
            center=True,
        )

        # P2 label (center-aligned) — P2's slot color (#726).
        text_utils.render_text(
            screen,
            header["p2_label"],
            (p2_col_x + player_col_width // 2, current_y),
            WIN_SCREEN_STATS_SIZE,
            P2_UI_COLOR,
            center=True,
        )

        current_y += WIN_SCREEN_LINE_SPACING

        # Render separator line
        line_color = WIN_SCREEN_TEXT_COLOR
        pygame.draw.line(
            screen,
            line_color,
            (stat_col_x, current_y),
            (stat_col_x + stat_col_width, current_y),
            2,
        )
        pygame.draw.line(
            screen,
            line_color,
            (p1_col_x, current_y),
            (p1_col_x + player_col_width, current_y),
            2,
        )
        pygame.draw.line(
            screen,
            line_color,
            (p2_col_x, current_y),
            (p2_col_x + player_col_width, current_y),
            2,
        )

        current_y += WIN_SCREEN_LINE_SPACING * 0.5

        # Render data rows
        for row in stats_table["rows"]:
            # Stat name (right-aligned)
            text_utils.render_text(
                screen,
                row["stat_name"],
                (stat_col_x + stat_col_width, current_y),
                WIN_SCREEN_STATS_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                right_align=True,
            )

            # P1 value (center-aligned) — P1's slot color (#726).
            text_utils.render_text(
                screen,
                row["p1_value"],
                (p1_col_x + player_col_width // 2, current_y),
                WIN_SCREEN_STATS_SIZE,
                P1_UI_COLOR,
                center=True,
            )

            # P2 value (center-aligned) — P2's slot color (#726).
            text_utils.render_text(
                screen,
                row["p2_value"],
                (p2_col_x + player_col_width // 2, current_y),
                WIN_SCREEN_STATS_SIZE,
                P2_UI_COLOR,
                center=True,
            )

            current_y += WIN_SCREEN_LINE_SPACING * 0.75

        return current_y

    def _draw_confirmation_boxes(self, screen, table_start_y, table_end_y):
        """Draw colored boxes around player columns to show confirmation status."""
        # Use the stored column positions from _render_stats_table
        if not hasattr(self, "table_columns"):
            return  # Table hasn't been rendered yet

        columns = self.table_columns

        # Box dimensions
        box_padding = 10
        box_height = table_end_y - table_start_y + box_padding * 2

        # Draw P1 confirmation box (red)
        if self.p1_confirmed:
            p1_rect = pygame.Rect(
                columns["p1_col_x"] - box_padding,
                table_start_y - box_padding,
                columns["p1_col_width"] + box_padding * 2,
                box_height,
            )
            pygame.draw.rect(screen, P1_UI_COLOR, p1_rect, 4)  # Red border

        # Draw P2 confirmation box (blue)
        if self.p2_confirmed:
            p2_rect = pygame.Rect(
                columns["p2_col_x"] - box_padding,
                table_start_y - box_padding,
                columns["p2_col_width"] + box_padding * 2,
                box_height,
            )
            pygame.draw.rect(screen, P2_UI_COLOR, p2_rect, 4)  # Blue border
