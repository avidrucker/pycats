"""
Character selection screen logic for the cat fighting game.

This module handles:
- Rendering the character selection grid
- Player cursor movement and selection
- Token pickup/drop mechanics
- Character preview rendering
"""

import pygame

from . import runtime_settings, text_utils
from .characters.roster import ARCHETYPE_DEFAULT_SKIN, ARCHETYPE_NAME, ARCHETYPE_ROSTER, palette_for
from .config import (
    BLACK,
    CHAR_SELECT_BG_COLOR,
    CHAR_SELECT_CURSOR_WIDTH,
    CHAR_SELECT_GRID_COLS,
    CHAR_SELECT_INSTRUCTION_SIZE,
    CHAR_SELECT_TILE_SIZE,
    CHAR_SELECT_TILE_SPACING,
    CHAR_SELECT_TITLE_COLOR,
    CHAR_SELECT_TITLE_SIZE,
    OVERLAY_DIM_ALPHA,
    P1_UI_COLOR,
    P2_UI_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from .domain import SKINS, Selection, assign_distinct_skins, available_skins, character_for

# --- char-select layout + behaviour constants (#420: named from inline literals) ---
# Input debounce windows (frames): movement repeats faster than a committing action.
MOVE_COOLDOWN_FRAMES = 10  # cursor-move debounce
ACTION_COOLDOWN_FRAMES = 15  # confirm / cancel / start-back debounce
START_SCREEN_INPUT_DELAY = 5  # frames to ignore input after the start overlay opens

# Player UI accent colours (P1_UI_COLOR/P2_UI_COLOR) now come from config (#450),
# shared with render_battle name labels + win_screen confirmation borders.

# Grid + tiles
GRID_START_Y = 170  # grid top edge, below the title
TILE_BG_COLOR = (50, 50, 60)  # per-tile background fill
TILE_NAME_FONT_SIZE = 18  # archetype name under each tile
CURSOR_LABEL_FONT_SIZE = 16  # "P1"/"P2" tag above a cursor
CONFIRM_FONT_SIZE = 20  # "P1 ✓" confirmation label
CONTROLS_FONT_SIZE = 16  # bottom control-scheme strip

# Preview cat drawn inside each tile
PREVIEW_SCALE_X = 0.6  # preview width as a fraction of the tile
PREVIEW_SCALE_Y = 0.8  # preview height as a fraction of the tile
PREVIEW_STRIPE_COUNT = 3  # simplified stripes on the preview body

# Per-player selected-character display row — a fixed P1..P4 slot strip (#682), separate
# from the per-Character selection grid. P1/P2 slots paint the player's Selection (Character
# in the cycled Skin); P3/P4 are inert stubs (no 4-player support yet).
PLAYER_SLOT_SIZE = 56  # slot tile edge
PLAYER_SLOT_SPACING = 24  # gap between slots
PLAYER_SLOT_ROW_Y = 402  # top edge of the row (below grid + names, above the controls strip)
PLAYER_SLOT_COUNT = 4  # P1..P4
PLAYER_SLOT_TAG_FONT = 14  # "P1" tag above the slot
PLAYER_SLOT_CAPTION_FONT = 13  # "Character · Skin" caption below the slot
SLOT_STUB_BG_COLOR = (34, 34, 40)  # dim fill for empty/stub slots (distinct from any cat body)
SLOT_STUB_BORDER_COLOR = (90, 90, 100)  # gray border + label for P3/P4 stubs
SLOT_EMPTY_BORDER_COLOR = (120, 120, 130)  # unselected P1/P2 placeholder border + label

# Start overlay (dim uses the shared config.OVERLAY_DIM_ALPHA + config.BLACK, #450)
START_BOX_WIDTH = 400
START_BOX_HEIGHT = 150
START_BOX_BG_COLOR = (40, 40, 50)
START_ACCENT_COLOR = (100, 255, 100)  # green — box border + "START" title
START_TITLE_FONT_SIZE = 48
START_HINT_FONT_SIZE = 24


class CharacterSelector:
    """Handles character selection screen logic for both players."""

    def __init__(self, p1_controls, p2_controls):
        # The roster is the real PM-archetype fighters (#268, #127 Part 1), not the
        # OG colour-skins; each archetype's cosmetic comes from its default palette.
        self.characters = list(ARCHETYPE_ROSTER)

        # Grid tile → the skin-key currently shown on it (#676). A tile paints in the
        # most-recently-active player's Skin when a player is confirmed on that Character;
        # absent → the Character's default. Keyed by Character, not player.
        self._active_skin_by_char = {}

        # Player cursors (grid positions)
        self.p1_cursor = 0  # grid index
        self.p2_cursor = 1  # grid index

        # Player character selection (which character they've selected, None if not selected)
        self.p1_selected = None
        self.p2_selected = None

        # Chosen OG-skin key per player (None until confirmed → then the archetype default,
        # cycled with left/right; #650). None also means "use the archetype's own palette".
        self.p1_palette = None
        self.p2_palette = None

        # Player confirmation status
        self.p1_confirmed = False
        self.p2_confirmed = False

        # Game ready to start (after both confirmed)
        self.show_start_screen = False
        self.start_screen_delay = 0  # Frames to wait before allowing start input

        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Input debouncing
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0

        # Grid layout
        self.grid_start_x = (
            SCREEN_WIDTH
            - (CHAR_SELECT_GRID_COLS * CHAR_SELECT_TILE_SIZE + (CHAR_SELECT_GRID_COLS - 1) * CHAR_SELECT_TILE_SPACING)
        ) // 2
        self.grid_start_y = GRID_START_Y  # Below title

    def reset(self):
        """Reset the character selector to initial state."""
        # Reset cursors
        self.p1_cursor = 0
        self.p2_cursor = 1

        # Reset selections
        self.p1_selected = None
        self.p2_selected = None

        # Reset chosen skins (#650)
        self.p1_palette = None
        self.p2_palette = None

        # Reset grid tile skins (#676)
        self._active_skin_by_char = {}

        # Reset confirmations
        self.p1_confirmed = False
        self.p2_confirmed = False

        # Reset start screen
        self.show_start_screen = False
        self.start_screen_delay = 0

        # Reset input cooldowns
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0

    def update(self, held_keys, pressed_keys=None):
        """Update character selection based on player input."""
        # If pressed_keys is not provided, fall back to held_keys for backward compatibility
        if pressed_keys is None:
            pressed_keys = held_keys

        # Decrease input cooldowns
        if self.p1_input_cooldown > 0:
            self.p1_input_cooldown -= 1
        if self.p2_input_cooldown > 0:
            self.p2_input_cooldown -= 1

        # Check if we should show start screen
        if self.both_confirmed() and not self.show_start_screen:
            self.show_start_screen = True
            self.start_screen_delay = START_SCREEN_INPUT_DELAY
            # Reset input cooldowns when showing start screen to allow immediate input
            self.p1_input_cooldown = 0
            self.p2_input_cooldown = 0

        # Decrease start screen delay
        if self.start_screen_delay > 0:
            self.start_screen_delay -= 1

        # Handle start screen input
        if self.show_start_screen:
            if self.p1_input_cooldown == 0:
                if self.p1_controls["special"] in pressed_keys:
                    # Go back - unconfirm this player but keep selection
                    self.p1_confirmed = False
                    self._release_tile(self.p1_selected)  # tile reverts if P1 no longer holds it (#676)
                    self.show_start_screen = False
                    self.start_screen_delay = 0
                    self.p1_input_cooldown = ACTION_COOLDOWN_FRAMES

            if self.p2_input_cooldown == 0:
                if self.p2_controls["special"] in pressed_keys:
                    # Go back - unconfirm this player but keep selection
                    self.p2_confirmed = False
                    self._release_tile(self.p2_selected)  # tile reverts if P2 no longer holds it (#676)
                    self.show_start_screen = False
                    self.start_screen_delay = 0
                    self.p2_input_cooldown = ACTION_COOLDOWN_FRAMES
            # Don't return here - let the main game loop handle A presses for starting
            return

        # Handle P1 input (character selection)
        if self.p1_input_cooldown == 0:
            # Movement (only if not confirmed)
            if not self.p1_confirmed:
                if self.p1_controls["left"] in pressed_keys:
                    self.p1_cursor = max(0, self.p1_cursor - 1)
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p1_controls["right"] in pressed_keys:
                    self.p1_cursor = min(len(self.characters) - 1, self.p1_cursor + 1)
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p1_controls["up"] in pressed_keys:
                    new_cursor = self.p1_cursor - CHAR_SELECT_GRID_COLS
                    if new_cursor >= 0:
                        self.p1_cursor = new_cursor
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p1_controls["down"] in pressed_keys:
                    new_cursor = self.p1_cursor + CHAR_SELECT_GRID_COLS
                    if new_cursor < len(self.characters):
                        self.p1_cursor = new_cursor
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p1_controls["attack"] in pressed_keys:
                    # Confirm selection — skin starts at the Character's default, bumped if
                    # the other player already holds it on the same Character (#676/#755).
                    self.p1_selected = self.characters[self.p1_cursor]
                    self.p1_palette = self._default_skin(1, self.p1_selected)
                    self.p1_confirmed = True
                    self._active_skin_by_char[self.p1_selected] = self.p1_palette
                    self.p1_input_cooldown = ACTION_COOLDOWN_FRAMES
            else:
                # If confirmed, B (special) cancels selection; left/right cycles the skin
                # within this Character's pool, skipping the other player's locked skin (#676).
                if self.p1_controls["special"] in pressed_keys:
                    self.p1_confirmed = False
                    released = self.p1_selected
                    self.p1_selected = None
                    self.p1_palette = None
                    self._release_tile(released)
                    self.p1_input_cooldown = ACTION_COOLDOWN_FRAMES
                elif self.p1_controls["left"] in pressed_keys:
                    self.p1_palette = self._cycle_palette(
                        self.p1_selected, self.p1_palette, -1, self._skins_locked_against(1)
                    )
                    self._active_skin_by_char[self.p1_selected] = self.p1_palette
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p1_controls["right"] in pressed_keys:
                    self.p1_palette = self._cycle_palette(
                        self.p1_selected, self.p1_palette, +1, self._skins_locked_against(1)
                    )
                    self._active_skin_by_char[self.p1_selected] = self.p1_palette
                    self.p1_input_cooldown = MOVE_COOLDOWN_FRAMES

        # Handle P2 input (character selection)
        if self.p2_input_cooldown == 0:
            # Movement (only if not confirmed)
            if not self.p2_confirmed:
                if self.p2_controls["left"] in pressed_keys:
                    self.p2_cursor = max(0, self.p2_cursor - 1)
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p2_controls["right"] in pressed_keys:
                    self.p2_cursor = min(len(self.characters) - 1, self.p2_cursor + 1)
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p2_controls["up"] in pressed_keys:
                    new_cursor = self.p2_cursor - CHAR_SELECT_GRID_COLS
                    if new_cursor >= 0:
                        self.p2_cursor = new_cursor
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p2_controls["down"] in pressed_keys:
                    new_cursor = self.p2_cursor + CHAR_SELECT_GRID_COLS
                    if new_cursor < len(self.characters):
                        self.p2_cursor = new_cursor
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p2_controls["attack"] in pressed_keys:
                    # Confirm selection — skin starts at the Character's default, bumped if
                    # the other player already holds it on the same Character (#676/#755).
                    self.p2_selected = self.characters[self.p2_cursor]
                    self.p2_palette = self._default_skin(2, self.p2_selected)
                    self.p2_confirmed = True
                    self._active_skin_by_char[self.p2_selected] = self.p2_palette
                    self.p2_input_cooldown = ACTION_COOLDOWN_FRAMES
            else:
                # If confirmed, B (special) cancels selection; left/right cycles the skin
                # within this Character's pool, skipping the other player's locked skin (#676).
                if self.p2_controls["special"] in pressed_keys:
                    self.p2_confirmed = False
                    released = self.p2_selected
                    self.p2_selected = None
                    self.p2_palette = None
                    self._release_tile(released)
                    self.p2_input_cooldown = ACTION_COOLDOWN_FRAMES
                elif self.p2_controls["left"] in pressed_keys:
                    self.p2_palette = self._cycle_palette(
                        self.p2_selected, self.p2_palette, -1, self._skins_locked_against(2)
                    )
                    self._active_skin_by_char[self.p2_selected] = self.p2_palette
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES
                elif self.p2_controls["right"] in pressed_keys:
                    self.p2_palette = self._cycle_palette(
                        self.p2_selected, self.p2_palette, +1, self._skins_locked_against(2)
                    )
                    self._active_skin_by_char[self.p2_selected] = self.p2_palette
                    self.p2_input_cooldown = MOVE_COOLDOWN_FRAMES

    def both_confirmed(self):
        """Check if both players have confirmed their character selection."""
        return self.p1_confirmed and self.p2_confirmed

    def get_selected_characters(self):
        """Get the selected characters for both players."""
        return self.p1_selected, self.p2_selected

    def _skin_pool(self, char_key):
        """Ordered skin-keys ``char_key`` may cycle: the shared OG six + that Character's
        own theme(s), from the #755 domain layer (`available_skins`). Never another
        Character's theme — this is what makes the cycle pool per-Character (#676)."""
        return [skin.key for skin in available_skins(character_for(char_key))]

    def _skins_locked_against(self, player_num):
        """Skins the OTHER confirmed player holds on the SAME Character as ``player_num``
        (FCFS lock, #676/#755): those keys are removed from this player's cycle options, so
        two players on one Character can never wear the same Skin."""
        if player_num == 1:
            my_char = self.p1_selected
            other_char, other_pal, other_conf = self.p2_selected, self.p2_palette, self.p2_confirmed
        else:
            my_char = self.p2_selected
            other_char, other_pal, other_conf = self.p1_selected, self.p1_palette, self.p1_confirmed
        if other_conf and other_char == my_char and other_pal is not None:
            return {other_pal}
        return set()

    def _default_skin(self, player_num, char_key):
        """The Skin a newly-confirming player starts on: the Character's default, bumped to
        the next available if the other player already holds it (FCFS lock via the domain
        `assign_distinct_skins`, #755 — the already-confirmed holder keeps their Skin)."""
        default = ARCHETYPE_DEFAULT_SKIN.get(char_key)
        locked = self._skins_locked_against(player_num)
        if default not in locked:
            return default
        holder = Selection(character_for(char_key), SKINS[next(iter(locked))])
        mine = Selection(character_for(char_key), SKINS[default])
        _held, resolved = assign_distinct_skins([holder, mine])
        return resolved.skin.key

    def _cycle_palette(self, char_key, current, step, locked=frozenset()):
        """Advance ``current`` by ``step`` (±1) through ``char_key``'s available skins (#755),
        wrapping and skipping any skin ``locked`` by another player on the same Character
        (FCFS, #676). ``current`` absent from the pool starts from the first skin."""
        pool = [key for key in self._skin_pool(char_key) if key not in locked]
        if not pool:  # everything locked (can't happen with 2 players) — fall back to full
            pool = self._skin_pool(char_key)
        idx = pool.index(current) if current in pool else 0
        return pool[(idx + step) % len(pool)]

    def _tile_owner_skin(self, char_key):
        """The Skin the grid tile for ``char_key`` should paint after a change: whichever
        player is still confirmed on it (#676). None → no one; tile shows the default."""
        if self.p1_confirmed and self.p1_selected == char_key:
            return self.p1_palette
        if self.p2_confirmed and self.p2_selected == char_key:
            return self.p2_palette
        return None

    def _release_tile(self, char_key):
        """Recompute a tile's shown Skin after a player leaves ``char_key`` (#676): hand it
        to whoever remains confirmed there, else clear it back to the Character default."""
        if char_key is None:
            return
        owner = self._tile_owner_skin(char_key)
        if owner is not None:
            self._active_skin_by_char[char_key] = owner
        else:
            self._active_skin_by_char.pop(char_key, None)

    def get_selected_palettes(self):
        """Get the chosen OG-skin key per player (None → the archetype's own palette)."""
        return self.p1_palette, self.p2_palette

    def can_start_game(self):
        """Check if the game can start (both players confirmed)."""
        return self.both_confirmed()

    def ready_to_start(self, pressed_keys):
        """Check if either player pressed A to start the game (only when start screen is shown)."""
        if not self.show_start_screen or self.start_screen_delay > 0:
            return False

        # Only start if attack key is pressed (fresh press) AND input cooldown is 0
        can_start = False
        if self.p1_input_cooldown == 0 and self.p1_controls["attack"] in pressed_keys:
            can_start = True
            self.p1_input_cooldown = ACTION_COOLDOWN_FRAMES  # Prevent multiple presses
        elif self.p2_input_cooldown == 0 and self.p2_controls["attack"] in pressed_keys:
            can_start = True
            self.p2_input_cooldown = ACTION_COOLDOWN_FRAMES  # Prevent multiple presses

        return can_start

    def _grid_pos_to_screen_pos(self, grid_index):
        """Convert grid index to screen position."""
        col = grid_index % CHAR_SELECT_GRID_COLS
        row = grid_index // CHAR_SELECT_GRID_COLS

        x = self.grid_start_x + col * (CHAR_SELECT_TILE_SIZE + CHAR_SELECT_TILE_SPACING)
        y = self.grid_start_y + row * (CHAR_SELECT_TILE_SIZE + CHAR_SELECT_TILE_SPACING)

        return x, y

    def _draw_cat_preview(self, screen, char_key, x, y, size, palette_key=None):
        """Draw a small cat preview in the given tile. ``palette_key`` overrides the
        archetype default with a chosen OG skin (live skin preview, #650)."""
        char_data = palette_for(palette_key or char_key)  # chosen skin → archetype default

        # Scale down for preview
        preview_size = (size * PREVIEW_SCALE_X, size * PREVIEW_SCALE_Y)
        cat_rect = pygame.Rect(
            x + (size - preview_size[0]) // 2,
            y + (size - preview_size[1]) // 2,
            preview_size[0],
            preview_size[1],
        )

        # Draw body
        pygame.draw.rect(screen, char_data["color"], cat_rect)

        # Draw stripes (simplified)
        if char_data["stripe_color"] != char_data["color"]:
            stripe_height = preview_size[1] // 6
            for i in range(PREVIEW_STRIPE_COUNT):
                stripe_y = cat_rect.y + i * stripe_height * 2
                stripe_rect = pygame.Rect(cat_rect.x, stripe_y, preview_size[0], stripe_height)
                pygame.draw.rect(screen, char_data["stripe_color"], stripe_rect)

        # Draw ears
        ear_width = preview_size[0] // 6
        ear_height = preview_size[1] // 4
        left_ear = pygame.Rect(
            cat_rect.x + ear_width // 2,
            cat_rect.y - ear_height // 2,
            ear_width,
            ear_height,
        )
        right_ear = pygame.Rect(
            cat_rect.x + preview_size[0] - ear_width * 1.5,
            cat_rect.y - ear_height // 2,
            ear_width,
            ear_height,
        )
        pygame.draw.rect(screen, char_data["color"], left_ear)
        pygame.draw.rect(screen, char_data["color"], right_ear)

        # Draw eyes
        eye_size = max(2, int(preview_size[0] // 12))
        left_eye_pos = (
            cat_rect.x + preview_size[0] // 3,
            cat_rect.y + preview_size[1] // 4,
        )
        right_eye_pos = (
            cat_rect.x + 2 * preview_size[0] // 3,
            cat_rect.y + preview_size[1] // 4,
        )

        pygame.draw.circle(screen, char_data["eye_color"], left_eye_pos, eye_size)
        pygame.draw.circle(screen, char_data["eye_color"], right_eye_pos, eye_size)

        # Draw eye glints
        glint_size = max(1, eye_size // 2)
        pygame.draw.circle(screen, WHITE, (left_eye_pos[0] + 1, left_eye_pos[1] - 1), glint_size)
        pygame.draw.circle(screen, WHITE, (right_eye_pos[0] + 1, right_eye_pos[1] - 1), glint_size)

    def render(self, screen):
        """Render the character selection screen."""
        # Clear screen
        screen.fill(CHAR_SELECT_BG_COLOR)

        # Title
        text_utils.render_text(
            screen,
            "Choose Your Cat!",
            (SCREEN_WIDTH // 2, 50),
            CHAR_SELECT_TITLE_SIZE,
            CHAR_SELECT_TITLE_COLOR,
            center=True,
        )

        # Instructions — gated by the non-battle show_screen_hints toggle (#681).
        if runtime_settings.show_screen_hints():
            instructions = [
                "Use arrow keys to move cursor",
                "Press A to confirm, B to cancel — after confirming, ←/→ changes your cat's skin",
                "When both players are ready, either can press A to start",
            ]

            for i, instruction in enumerate(instructions):
                text_utils.render_text(
                    screen,
                    instruction,
                    (SCREEN_WIDTH // 2, 90 + i * 20),
                    CHAR_SELECT_INSTRUCTION_SIZE,
                    CHAR_SELECT_TITLE_COLOR,
                    center=True,
                )

        # Character grid
        for i, char_key in enumerate(self.characters):
            x, y = self._grid_pos_to_screen_pos(i)

            # Draw tile background
            tile_rect = pygame.Rect(x, y, CHAR_SELECT_TILE_SIZE, CHAR_SELECT_TILE_SIZE)
            pygame.draw.rect(screen, TILE_BG_COLOR, tile_rect)
            pygame.draw.rect(screen, WHITE, tile_rect, 1)

            # Draw cat preview — the tile itself paints in the confirmed player's cycled
            # Skin (most-recently-active on a shared Character), else the Character default (#676).
            self._draw_cat_preview(
                screen, char_key, x, y, CHAR_SELECT_TILE_SIZE, palette_key=self._active_skin_by_char.get(char_key)
            )

            # Draw character name
            text_utils.render_text(
                screen,
                ARCHETYPE_NAME[char_key],
                (x + CHAR_SELECT_TILE_SIZE // 2, y + CHAR_SELECT_TILE_SIZE + 10),
                TILE_NAME_FONT_SIZE,
                WHITE,
                center=True,
            )

        # Draw cursors (only if not confirmed)
        if not self.p1_confirmed:
            self._draw_cursor(screen, self.p1_cursor, P1_UI_COLOR, "P1", large=True)  # Red, large
        if not self.p2_confirmed:
            self._draw_cursor(screen, self.p2_cursor, P2_UI_COLOR, "P2", large=False)  # Blue, small

        # Draw selection confirmations
        if self.p1_confirmed and self.p1_selected:
            selected_idx = self.characters.index(self.p1_selected)
            self._draw_confirmation(screen, selected_idx, P1_UI_COLOR, "P1", True, self.p1_palette)

        if self.p2_confirmed and self.p2_selected:
            selected_idx = self.characters.index(self.p2_selected)
            self._draw_confirmation(screen, selected_idx, P2_UI_COLOR, "P2", False, self.p2_palette)

        # Per-player selected-character display row (P1..P4 slots, #682)
        self._draw_player_slots(screen)

        # Control instructions at bottom
        self._draw_control_instructions(screen)

        # Start overlay (if both players are confirmed)
        if self.show_start_screen:
            self._draw_start_overlay(screen)

    def _draw_cursor(self, screen, cursor_pos, color, label, large=True):
        """Draw a player's cursor around a tile."""
        x, y = self._grid_pos_to_screen_pos(cursor_pos)

        # Different cursor widths based on player
        cursor_width = CHAR_SELECT_CURSOR_WIDTH if large else CHAR_SELECT_CURSOR_WIDTH - 1

        # Draw cursor border
        cursor_rect = pygame.Rect(
            x - cursor_width,
            y - cursor_width,
            CHAR_SELECT_TILE_SIZE + 2 * cursor_width,
            CHAR_SELECT_TILE_SIZE + 2 * cursor_width,
        )
        pygame.draw.rect(screen, color, cursor_rect, cursor_width)

        # Draw player label
        text_utils.render_text(
            screen,
            label,
            (x + CHAR_SELECT_TILE_SIZE // 2, y - 15),
            CURSOR_LABEL_FONT_SIZE,
            color,
            center=True,
        )

    def _draw_confirmation(self, screen, char_pos, color, player_name, use_unicode=True, palette_key=None):
        """Draw a confirmation border + label on a selected Character's grid tile. The tile
        itself now paints in the cycled Skin (see the grid loop), so #662's separate external
        preview cat is retired (#676); the Skin **name** label stays for live cycle feedback."""
        x, y = self._grid_pos_to_screen_pos(char_pos)

        # Draw thick border to show selection
        confirm_rect = pygame.Rect(x - 2, y - 2, CHAR_SELECT_TILE_SIZE + 4, CHAR_SELECT_TILE_SIZE + 4)
        pygame.draw.rect(screen, color, confirm_rect, 4)

        # Confirmation label carries the chosen skin name so cycling gives live feedback (#650).
        skin_name = palette_for(palette_key)["name"] if palette_key else ""
        cx = x + CHAR_SELECT_TILE_SIZE // 2
        cy = y + CHAR_SELECT_TILE_SIZE + 30
        if use_unicode:
            label = f"{player_name} ✓ {skin_name}".rstrip()
            text_utils.text_renderer.render_text_mixed(label, CONFIRM_FONT_SIZE, color, screen, (cx, cy), center=True)
        else:
            label = f"{player_name} OK {skin_name}".rstrip()
            text_utils.render_text(screen, label, (cx, cy), CONFIRM_FONT_SIZE, color, center=True)

    def _player_slot_rect(self, slot_index):
        """Top-left ``(x, y)`` + ``size`` of player slot ``slot_index`` (0=P1 .. 3=P4) in the
        centered P1..P4 display row (#682)."""
        total_w = PLAYER_SLOT_COUNT * PLAYER_SLOT_SIZE + (PLAYER_SLOT_COUNT - 1) * PLAYER_SLOT_SPACING
        start_x = (SCREEN_WIDTH - total_w) // 2
        x = start_x + slot_index * (PLAYER_SLOT_SIZE + PLAYER_SLOT_SPACING)
        return x, PLAYER_SLOT_ROW_Y, PLAYER_SLOT_SIZE

    def _draw_player_slots(self, screen):
        """Render the fixed P1..P4 selected-character display row (#682): each active player's
        slot paints their selected Character in the currently-cycled Skin (via
        `_draw_cat_preview`'s ``palette_key``), live; P3/P4 are inert stubs since 4-player
        support does not exist yet. Separate from the selection grid and from the #662
        confirmation preview."""
        # (selected, palette_key, confirmed, accent, tag) per real player; None-padded to P4.
        players = [
            (self.p1_selected, self.p1_palette, self.p1_confirmed, P1_UI_COLOR),
            (self.p2_selected, self.p2_palette, self.p2_confirmed, P2_UI_COLOR),
        ]
        for slot in range(PLAYER_SLOT_COUNT):
            x, y, size = self._player_slot_rect(slot)
            rect = pygame.Rect(x, y, size, size)
            tag = f"P{slot + 1}"
            active = slot < len(players)

            if active and players[slot][2] and players[slot][0]:
                # confirmed on a Character → paint the cat in the chosen Skin
                selected, palette, _confirmed, accent = players[slot]
                pygame.draw.rect(screen, TILE_BG_COLOR, rect)
                self._draw_cat_preview(screen, selected, x, y, size, palette_key=palette)
                pygame.draw.rect(screen, accent, rect, 3)
                skin = palette_for(palette or selected)["name"]
                caption, cap_color, tag_color = f"{ARCHETYPE_NAME[selected]} - {skin}", WHITE, accent
            elif active:
                # real player, not yet locked in
                accent = players[slot][3]
                pygame.draw.rect(screen, SLOT_STUB_BG_COLOR, rect)
                pygame.draw.rect(screen, SLOT_EMPTY_BORDER_COLOR, rect, 2)
                caption, cap_color, tag_color = "picking", SLOT_EMPTY_BORDER_COLOR, accent
            else:
                # P3/P4 stub — 4-player not available yet
                pygame.draw.rect(screen, SLOT_STUB_BG_COLOR, rect)
                pygame.draw.rect(screen, SLOT_STUB_BORDER_COLOR, rect, 2)
                caption, cap_color, tag_color = "N/A", SLOT_STUB_BORDER_COLOR, SLOT_STUB_BORDER_COLOR

            text_utils.render_text(screen, tag, (x + size // 2, y - 12), PLAYER_SLOT_TAG_FONT, tag_color, center=True)
            text_utils.render_text(
                screen, caption, (x + size // 2, y + size + 10), PLAYER_SLOT_CAPTION_FONT, cap_color, center=True
            )

    def _draw_control_instructions(self, screen):
        """Draw control instructions at the bottom of the screen."""
        # Convert key constants to readable strings with Unicode arrows
        key_names = {
            pygame.K_a: "A",
            pygame.K_d: "D",
            pygame.K_w: "W",
            pygame.K_s: "S",
            pygame.K_v: "V",
            pygame.K_c: "C",
            pygame.K_x: "X",
            pygame.K_LEFT: "←",
            pygame.K_RIGHT: "→",
            pygame.K_UP: "↑",
            pygame.K_DOWN: "↓",
            pygame.K_SLASH: "/",
            pygame.K_PERIOD: ".",
            pygame.K_COMMA: ",",
        }

        # P1 controls
        p1_move_keys = (
            f"{key_names.get(self.p1_controls['left'], '?')}"
            f"{key_names.get(self.p1_controls['right'], '?')}"
            f"{key_names.get(self.p1_controls['up'], '?')}"
            f"{key_names.get(self.p1_controls['down'], '?')}"
        )
        p1_attack_key = key_names.get(self.p1_controls["attack"], "?")
        p1_special_key = key_names.get(self.p1_controls["special"], "?")

        p1_text = f"P1: Move({p1_move_keys}) Confirm({p1_attack_key}) Cancel({p1_special_key})"
        text_utils.text_renderer.render_text_mixed(
            p1_text,
            CONTROLS_FONT_SIZE,
            P1_UI_COLOR,
            screen,
            (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 40),
            center=True,
        )

        # P2 controls
        p2_move_keys = (
            f"{key_names.get(self.p2_controls['left'], '?')}"
            f"{key_names.get(self.p2_controls['right'], '?')}"
            f"{key_names.get(self.p2_controls['up'], '?')}"
            f"{key_names.get(self.p2_controls['down'], '?')}"
        )
        p2_attack_key = key_names.get(self.p2_controls["attack"], "?")
        p2_special_key = key_names.get(self.p2_controls["special"], "?")

        p2_text = f"P2: Move({p2_move_keys}) Confirm({p2_attack_key}) Cancel({p2_special_key})"
        text_utils.text_renderer.render_text_mixed(
            p2_text,
            CONTROLS_FONT_SIZE,
            P2_UI_COLOR,
            screen,
            (3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 40),
            center=True,
        )

    def _draw_start_overlay(self, screen):
        """Draw the start overlay that partially obscures the grid when both players are confirmed."""
        # Create a semi-transparent overlay
        overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay_surface.set_alpha(OVERLAY_DIM_ALPHA)
        overlay_surface.fill(BLACK)
        screen.blit(overlay_surface, (0, 0))

        # Calculate center position for the start box
        box_width = START_BOX_WIDTH
        box_height = START_BOX_HEIGHT
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2

        # Draw the start box background
        start_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, START_BOX_BG_COLOR, start_box)
        pygame.draw.rect(screen, START_ACCENT_COLOR, start_box, 3)

        # Draw "START" text
        text_utils.render_text(
            screen,
            "START",
            (SCREEN_WIDTH // 2, box_y + 40),
            START_TITLE_FONT_SIZE,
            START_ACCENT_COLOR,
            center=True,
        )

        # Draw instruction text
        text_utils.render_text(
            screen,
            "Press A to start the match",
            (SCREEN_WIDTH // 2, box_y + 80),
            START_HINT_FONT_SIZE,
            WHITE,
            center=True,
        )

        # Draw cancel instruction
        text_utils.render_text(
            screen,
            "Press B to go back",
            (SCREEN_WIDTH // 2, box_y + 110),
            START_HINT_FONT_SIZE,
            WHITE,
            center=True,
        )
