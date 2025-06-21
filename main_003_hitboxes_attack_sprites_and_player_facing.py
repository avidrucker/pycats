"""Smash‑Draft • rev 3
================================
Adds three core gameplay systems without breaking existing mechanics:

A. **Finite state machine (FSM)** for each player
   • States: `idle`, `run`, `jump`, `fall`, `shield`, `dodge`
   • Blocking (`shield`) disables horizontal movement & jumping until the 
     shield button is released.

B. **Edge‑triggered input for jumping** (one‑jump‑per‑press)
   • Holding the up key no longer performs repeat jumps when landing; the
     player must release and press again.

C. **Double‑jump**
   • Each airtime grants a second jump.  `jumps_remaining` resets when the
     character lands on any platform.

The update preserves:
1.  Drop‑through thin‑platform logic (hold ↓ while grounded).
2.  Shield overlay rendering & timer increment.
3.  All previously working physics and dodge behaviour.

Controls (unchanged)
====================
P1 (orange) A/D move · W jump · hold S drop · F attack · G special · R shield · E dodge
P2 (grey)   ←/→ move · ↑ jump · hold ↓ drop · , attack · . special · / shield · ; dodge
"""
#### TODO: determine whether walking off of a ledge "consumes" a jump
#### TODO: implement grabs which are combo regular-attack + shield, and can be initiated from idle or shielding
#### TODO: implement dodges which are combo move + shield, and can be iniated from idle or walking
#### TODO: research and implement move/input buffering
#### TODO: implement friction and horizontal movement acceleration

import sys
import pygame
from enum import Enum, auto

pygame.init()
pygame.display.set_caption("Smash‑Draft Rev 3")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
GRAVITY = 0.5
MAX_FALL_SPEED = 12
MOVE_SPEED = 5
JUMP_VEL = -10
DODGE_FRAMES = 15
MAX_JUMPS = 2            # ← single + double‑jump
ATTACK_LIFETIME = 12          # frames the hit-box stays active
ATTACK_SIZE     = (30, 18)    # (w, h) of the rectangle
EYE_OFFSET_X    = 10           # distance from body edge
EYE_OFFSET_Y    = 12           # distance from body top
EYE_RADIUS = 6

# ---------------------------------------------------------------------------
# Stage geometry helpers
# ---------------------------------------------------------------------------
class Platform(pygame.sprite.Sprite):
    """Axis‑aligned rectangular platform.

    *thin*  – pass‑through from below, drop‑through via ↓ while grounded.
    *thick* – solid on all sides (e.g. main stage).
    """

    def __init__(self, rect: pygame.Rect, thin: bool = False):
        super().__init__()
        self.thin = thin
        color = (164, 113, 73) if not thin else (193, 153, 112)
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = rect


class Attack(pygame.sprite.Sprite):
    """Simple rectangular hit-box that disappears after N frames."""

    COLOR = (255, 60, 60, 180)   # semi-transparent red

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.frames_left = ATTACK_LIFETIME

        # Position the hit-box on the side the owner is facing
        offset_x = owner.rect.width // 2 + 4
        x = owner.rect.centerx + (offset_x if owner.facing_right else -offset_x)
        y = owner.rect.centery - ATTACK_SIZE[1] // 2

        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()


# ---------------------------------------------------------------------------
# Finite‑state machine for Players
# ---------------------------------------------------------------------------
class PState(Enum):
    IDLE   = auto()
    RUN    = auto()
    JUMP   = auto()
    FALL   = auto()
    SHIELD = auto()
    DODGE  = auto()


# ---------------------------------------------------------------------------
# Player entity
# ---------------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    SIZE = (40, 60)

    def __init__(self, x, y, controls: dict, color, facing_right):
        super().__init__()
        self.image = pygame.Surface(self.SIZE)
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))

        # Input mapping
        self.controls = controls

        # Kinematics
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # Timers / counters
        self.dodge_timer = 0
        self.jumps_remaining = MAX_JUMPS
        self.shielding = False
        self.shield_radius = 30  # starting radius of the shield
        self.shield_tick = 0     # number of frames holding shield

        # Platform drop‑through reference
        self.drop_platform = None

        # FSM current state
        self.state = PState.IDLE

        # Facing
        self.facing_right = facing_right

    # ---------------------------------------------------- input helpers
    def _pressed(self, key_state, name):
        """Utility to check a mapped key in an arbitrary key snapshot."""
        return key_state[self.controls[name]]

    # ---------------------------------------------------- top‑level update
    def update(self, keys, prev_keys, platforms, attack_group):
        """Advance one frame: handle timers, input, physics, collisions, state."""

        # shield hold
        if self._pressed(keys, "shield") and self.state == PState.SHIELD:
            self.shielding = True
            self.shield_tick += 1
        else:
            self.shielding = False
            self.shield_tick = 0
            #### TODO: replenish shield when not in shielded state

        # ---------------- timers ---------------------------------------
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
            if self.dodge_timer == 0 and self.state == PState.DODGE:
                # End of dodge → fall if mid‑air, else idle
                self.state = PState.FALL if not self.on_ground else PState.IDLE

        # ---------------- input & state logic --------------------------
        if self.state != PState.DODGE:  # during dodge, ignore fresh input
            self.handle_actions(keys, prev_keys, attack_group)
            self.handle_move(keys)

        # ---------------- physics & collisions ------------------------
        self.apply_gravity()
        self.horizontal_bounds()
        self.vertical_collision(platforms, keys)

        # ---------------- simple auto state transitions ---------------
        if self.state not in (PState.SHIELD, PState.DODGE):
            if not self.on_ground:
                if self.vel.y < 0:
                    self.state = PState.JUMP
                elif self.vel.y > 0:
                    self.state = PState.FALL
            elif self.on_ground:
                if self.vel.x != 0:
                    self.state = PState.RUN
                else:
                    self.state = PState.IDLE

    # ---------------------------------------------------- movement
    def handle_move(self, keys):
        """Apply horizontal inputs unless shielding."""
        if self.state == PState.SHIELD:
            self.vel.x = 0
            return

        self.vel.x = 0
        if self._pressed(keys, "left"):
            self.vel.x = -MOVE_SPEED
            self.facing_right = False
        if self._pressed(keys, "right"):
            self.vel.x = MOVE_SPEED
            self.facing_right = True

    # ---------------------------------------------------- actions (jump / shield / dodge)
    def handle_actions(self, keys, prev_keys, attack_group):
        # ---------- Shield toggle (hold) ----------------------------
        if self._pressed(keys, "shield"):
            if self.state != PState.SHIELD:
                self.state = PState.SHIELD
            self.shielding = True
            self.shield_tick += 1
        else:
            if self.state == PState.SHIELD:
                self.state = PState.IDLE
            self.shielding = False
            self.shield_tick = 0

        # ---------- Dodge (tap, ignore if shielding) ----------------
        if (self._pressed(keys, "dodge") and not self._pressed(prev_keys, "dodge")
                and self.dodge_timer == 0 and self.state != PState.SHIELD):
            self.state = PState.DODGE
            self.dodge_timer = DODGE_FRAMES
            direction = 1 if self.vel.x >= 0 else -1
            self.vel.x = direction * MOVE_SPEED * 2
            self.vel.y = JUMP_VEL / 2
            return  # skip other actions this frame

        # ---------- Jump logic (edge‑triggered) ---------------------
        jump_pressed = self._pressed(keys, "up") and not self._pressed(prev_keys, "up") and self.state != PState.SHIELD
        if jump_pressed and self.jumps_remaining > 0:
            self.vel.y = JUMP_VEL
            self.jumps_remaining -= 1
            self.state = PState.JUMP

        # ----------- Normal attack ----------------------------------
        atk_pressed = self._pressed(keys, "attack") and not self._pressed(prev_keys, "attack")
        if atk_pressed and self.state not in (PState.SHIELD, PState.DODGE):
            attack_group.add(Attack(self))

    # ---------------------------------------------------- physics helpers
    def apply_gravity(self):
        if self.vel.y < MAX_FALL_SPEED:
            self.vel.y += GRAVITY
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

    def horizontal_bounds(self):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def vertical_collision(self, platforms, keys):
        """Ground detection + drop-through thin platforms (with proper edge test)."""
        self.on_ground = False

        # Helper: horizontal overlap test
        def x_overlap(a: pygame.Rect, b: pygame.Rect):
            return a.right > b.left and a.left < b.right

        # Clear drop-through once fully below the platform we fell through
        if self.drop_platform and self.rect.top > self.drop_platform.rect.bottom:
            self.drop_platform = None

        landing_platform = None

        for p in platforms:
            if p is self.drop_platform:
                continue  # intangible after a drop-through

            overlap      = self.rect.colliderect(p.rect)
            flush_on_top = (self.rect.bottom == p.rect.top
                            and self.vel.y >= 0
                            and x_overlap(self.rect, p.rect))

            if not (overlap or flush_on_top):
                continue

            if p.thin:
                coming_from_above = self.vel.y >= 0 and self.rect.bottom - self.vel.y <= p.rect.top
                if coming_from_above and not self._pressed(keys, "down"):
                    landing_platform = p
            else:  # thick
                if self.vel.y >= 0 and self.rect.bottom - self.vel.y <= p.rect.top:
                    landing_platform = p
                elif self.vel.y < 0 and self.rect.top - self.vel.y >= p.rect.bottom:
                    # Head-bonk
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0

        if landing_platform:
            self.rect.bottom = landing_platform.rect.top
            self.vel.y = 0
            self.on_ground = True
            self.jumps_remaining = MAX_JUMPS

            # Drop-through thin platform if ↓ held
            if landing_platform.thin and self._pressed(keys, "down"):
                self.drop_platform = landing_platform



# ---------------------------------------------------------------------------
# Init Pygame objects
# ---------------------------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Stage platforms -----------------------------------------------------------
platforms = [
    Platform(pygame.Rect(WIDTH // 2 - 150, HEIGHT - 40, 300, 40), thin=False),  # main
    Platform(pygame.Rect(WIDTH // 2 - 250, HEIGHT - 130, 120, 20), thin=True),  # left thin
    Platform(pygame.Rect(WIDTH // 2 + 130, HEIGHT - 130, 120, 20), thin=True),  # right thin
]

# Controls -----------------------------------------------------------
P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_f, special=pygame.K_g, shield=pygame.K_r, dodge=pygame.K_e)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
               attack=pygame.K_COMMA, special=pygame.K_PERIOD, shield=pygame.K_SLASH, dodge=pygame.K_SEMICOLON)

player1 = Player(WIDTH // 2 - 100, HEIGHT - 200, P1_KEYS, (255, 160, 64), True)
player2 = Player(WIDTH // 2 + 100, HEIGHT - 200, P2_KEYS, (90, 90, 90), False)
players = pygame.sprite.Group(player1, player2)

BG_COLOR = (60, 60, 70)
SHIELD_COLOR = (80, 180, 255)

# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
prev_keys = pygame.key.get_pressed()  # snapshot for edge detection
attacks = pygame.sprite.Group()
while True:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # Update
    for p in players:
        p.update(keys, prev_keys, platforms, attacks)

    attacks.update()

    prev_keys = keys  # store for next frame edge detection

    # Render
    screen.fill(BG_COLOR)

    # Setup font for HUD display (must come before it's used)
    font = pygame.font.SysFont(None, 24)

    for pl in platforms:
        screen.blit(pl.image, pl.rect)

    for p in players:        
        screen.blit(p.image, p.rect)
        # --- draw the eye --------------------------------------------------
        eye_x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
        eye_y = p.rect.top + EYE_OFFSET_Y
        pygame.draw.circle(screen, (0, 0, 0), (eye_x, eye_y), EYE_RADIUS)

        if p.shielding:
            # Shrink shield radius over time but keep a minimum
            radius = max(10, p.shield_radius - int(p.shield_tick * 0.4))
    
            shield_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (*SHIELD_COLOR, 100), (radius, radius), radius)
    
            shield_pos = p.rect.centerx - radius, p.rect.centery - radius
            screen.blit(shield_surf, shield_pos)

    for a in attacks:
        screen.blit(a.image, a.rect)

    # HUD Info (Player 1 top-left, Player 2 top-right)
    def draw_player_status(p, label, topright=False):
        state_str = p.state.name.capitalize()
        jump_str = f"{p.jumps_remaining} jump{'s' if p.jumps_remaining != 1 else ''} left"
        lines = [label, state_str, jump_str]
        for i, text in enumerate(lines):
            surf = font.render(text, True, (255, 255, 255))
            pos = (WIDTH - surf.get_width() - 10, 10 + i * 22) if topright else (10, 10 + i * 22)
            screen.blit(surf, pos)

    draw_player_status(player1, "P1", topright=False)
    draw_player_status(player2, "P2", topright=True)

    pygame.display.flip()

