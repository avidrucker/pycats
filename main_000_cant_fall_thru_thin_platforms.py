"""Super‑simple first draft of a 2‑player Smash‑style prototype in Pygame.

Controls
=========
Player 1 (orange cat)
  Move      A / D
  Jump      W
  Drop      hold S while on a thin platform
  Attack    F  ("A" attack)
  Special   G  ("B" attack)
  Shield    R
  Dodge     E

Player 2 (grey cat)
  Move      ← / →
  Jump      ↑
  Drop      hold ↓ while on a thin platform
  Attack    ,
  Special   .
  Shield    /
  Dodge     ;

The game has:
- One stage with 3 brick platforms (2 thin, 1 thick)
- Axis‑aligned rectangle hit/hurt boxes only
- Basic gravity, jumping, shielding and dodging (no damage yet)
- Ability to fall through thin platforms by holding the down key

This is intentionally minimal so you can iterate quickly.
"""

import sys
import pygame

pygame.init()
pygame.display.set_caption("Smash‑Draft")

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
DROP_FRAMES = 8

# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
class Platform(pygame.sprite.Sprite):
    """A simple rectangular platform. If *thin* is True, players can jump up
    through it and choose to fall through by holding their down key."""

    def __init__(self, rect: pygame.Rect, thin: bool = False):
        super().__init__()
        color = (164, 113, 73) if not thin else (193, 153, 112)
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = rect
        self.thin = thin


class Player(pygame.sprite.Sprite):
    SIZE = (40, 60)

    def __init__(self, x, y, controls: dict, color):
        super().__init__()
        self.image = pygame.Surface(self.SIZE)
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.controls = controls
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # State flags / timers
        self.dodge_timer = 0
        self.drop_timer = 0
        self.shielding = False

    # ------------------------------------------------------------------
    # Input helpers
    # ------------------------------------------------------------------
    def _pressed(self, keys, name):
        return keys[self.controls[name]]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, keys, platforms):
        # ------------------------------------------------------------------
        # Process timers
        # ------------------------------------------------------------------
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.drop_timer > 0:
            self.drop_timer -= 1

        # ------------------------------------------------------------------
        # Skip normal control while dodging (invincible, no friction etc.)
        # ------------------------------------------------------------------
        if self.dodge_timer == 0:
            self.handle_move(keys)
            self.handle_actions(keys)

        # ------------------------------------------------------------------
        # Physics & collision
        # ------------------------------------------------------------------
        self.apply_gravity()
        self.horizontal_collision(platforms)  # only keep inside screen
        self.vertical_collision(platforms)

    # ------------------------------------------------------------------
    # Movement / actions
    # ------------------------------------------------------------------
    def handle_move(self, keys):
        self.vel.x = 0  # simple; feels arcade‑ish
        if self._pressed(keys, "left"):
            self.vel.x = -MOVE_SPEED
        if self._pressed(keys, "right"):
            self.vel.x = MOVE_SPEED

        # Jump
        if self._pressed(keys, "up") and self.on_ground:
            self.vel.y = JUMP_VEL
            self.on_ground = False

        # Fall‑through request
        if self._pressed(keys, "down") and self.on_ground:
            self.drop_timer = DROP_FRAMES

    def handle_actions(self, keys):
        # Shield (hold)
        self.shielding = self._pressed(keys, "shield")

        # Dodge (tap)
        if keys[self.controls["dodge"]]:
            # Only start a new dodge on key‑down event. Simplified:
            if self.dodge_timer == 0:
                self.dodge_timer = DODGE_FRAMES
                # A tiny hop + horizontal burst away from facing direction
                direction = 1 if self.vel.x >= 0 else -1
                self.vel.x = direction * MOVE_SPEED * 2
                self.vel.y = JUMP_VEL / 2

        # Stub for attacks (to be fleshed out later)
        # Attack
        if keys[self.controls["attack"]]:
            pass  # TODO: spawn hitbox / animation
        # Special
        if keys[self.controls["special"]]:
            pass  # TODO

    # ------------------------------------------------------------------
    # Physics helpers
    # ------------------------------------------------------------------
    def apply_gravity(self):
        if self.vel.y < MAX_FALL_SPEED:
            self.vel.y += GRAVITY
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

        # Keep inside the arena horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def horizontal_collision(self, platforms):
        # No horizontal obstruction for now (keeps code short)
        pass

    def vertical_collision(self, platforms):
        self.on_ground = False
        landed_platform = None

        for platform in platforms:
            if not self.rect.colliderect(platform.rect):
                continue

            # Thin‑platform logic – can only land from above and only if not dropping
            if platform.thin:
                coming_from_above = self.vel.y >= 0 and self.rect.bottom <= platform.rect.bottom
                if coming_from_above and self.drop_timer == 0:
                    landed_platform = platform
            else:  # thick platforms are solid
                if self.vel.y > 0 and self.rect.bottom - self.vel.y <= platform.rect.top:
                    landed_platform = platform
                elif self.vel.y < 0 and self.rect.top - self.vel.y >= platform.rect.bottom:
                    # Hit the underside – bump head and stop upward motion
                    self.rect.top = platform.rect.bottom
                    self.vel.y = 0

            # Ignore side collisions to keep things simple

        if landed_platform:
            self.rect.bottom = landed_platform.rect.top
            self.vel.y = 0
            self.on_ground = True


# ---------------------------------------------------------------------------
# Game setup
# ---------------------------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Platforms --------------------------------------------------------------
platforms = [
    Platform(pygame.Rect(WIDTH // 2 - 150, HEIGHT - 40, 300, 40), thin=False),  # main stage (thick)
    Platform(pygame.Rect(WIDTH // 2 - 250, HEIGHT - 120, 120, 20), thin=True),  # left thin
    Platform(pygame.Rect(WIDTH // 2 + 130, HEIGHT - 120, 120, 20), thin=True),  # right thin
]
platform_group = pygame.sprite.Group(platforms)

# Players ---------------------------------------------------------------
P1_KEYS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "up": pygame.K_w,
    "down": pygame.K_s,
    "attack": pygame.K_f,
    "special": pygame.K_g,
    "shield": pygame.K_r,
    "dodge": pygame.K_e,
}

P2_KEYS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "attack": pygame.K_COMMA,   # ,
    "special": pygame.K_PERIOD,  # .
    "shield": pygame.K_SLASH,    # /
    "dodge": pygame.K_SEMICOLON, # ;
}

player1 = Player(WIDTH // 2 - 100, HEIGHT - 200, P1_KEYS, (255, 160, 64))
player2 = Player(WIDTH // 2 + 100, HEIGHT - 200, P2_KEYS, (80, 80, 80))
players = pygame.sprite.Group(player1, player2)

# Colors ----------------------------------------------------------------
BG_COLOR = (60, 60, 70)
SHIELD_COLOR = (80, 180, 255)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    dt = clock.tick(FPS)

    # Input -------------------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # Update ------------------------------------------------------------
    for player in players:
        player.update(keys, platforms)

    # Draw --------------------------------------------------------------
    screen.fill(BG_COLOR)

    # Draw platforms
    for p in platforms:
        screen.blit(p.image, p.rect)

    # Draw players (shield overlay if shielding)
    for player in players:
        screen.blit(player.image, player.rect)
        if player.shielding:
            s = pygame.Surface(player.rect.size, pygame.SRCALPHA)
            s.fill((*SHIELD_COLOR, 120))
            screen.blit(s, player.rect.topleft)

    pygame.display.flip()

