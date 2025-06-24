"""Super-simple first draft of a 2‑player Smash‑style prototype in Pygame (rev 2).

★ UPDATES IN THIS REVISION ★
• Proper "drop‑through" behaviour on thin platforms:
    – When the player holds the down key while grounded on a THIN platform,
      collisions are disabled with THAT platform until the player’s bounding
      box has fully cleared below it.  This fixes the sticky “bounce back up”
      you observed.
• Replaced the old `drop_timer` with a more robust `drop_platform` reference.
• Minor tidy‑ups in comments.

Controls (unchanged)
====================
Player 1 (orange cat) —    Move A/D · Jump W · Drop hold S · Atk F · Spc G · Shield R · Dodge E
Player 2 (grey cat)   — Left/Right  · Jump ↑ · Drop hold ↓ · Atk , · Spc . · Shield / · Dodge ;
"""

import sys
import pygame

pygame.init()
pygame.display.set_caption("Smash‑Draft Rev 2")

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

# ---------------------------------------------------------------------------
# Stage geometry helpers
# ---------------------------------------------------------------------------
class Platform(pygame.sprite.Sprite):
    """Simple axis‑aligned rectangular platform.

    *thin* platforms are pass‑through from below and drop‑through via ↓.
    *thick* platforms are solid on all sides (think Final Destination’s base).
    """

    def __init__(self, rect: pygame.Rect, thin: bool = False):
        super().__init__()
        self.thin = thin
        color = (164, 113, 73) if not thin else (193, 153, 112)
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = rect


# ---------------------------------------------------------------------------
# Player entity
# ---------------------------------------------------------------------------
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
        self.shielding = False
        self.shield_radius = 30  # starting radius of the shield
        self.shield_tick = 0     # number of frames holding shield

        # NEW: platform we’re currently ignoring for drop‑through
        self.drop_platform = None

    # -------------------------------------- input helpers
    def _pressed(self, keys, name):
        return keys[self.controls[name]]

    # -------------------------------------- main update
    def update(self, keys, platforms):
        # timers
        if self.dodge_timer > 0:
            self.dodge_timer -= 1

        # player‑controlled movement only when not dodging
        if self.dodge_timer == 0:
            self.handle_move(keys)
            self.handle_actions(keys)

        # physics
        self.apply_gravity()
        self.horizontal_bounds()
        self.vertical_collision(platforms)

    # -------------------------------------- movement / actions
    def handle_move(self, keys):
        self.vel.x = 0
        if self._pressed(keys, "left"):
            self.vel.x = -MOVE_SPEED
        if self._pressed(keys, "right"):
            self.vel.x = MOVE_SPEED

        # jump (grounded only)
        if self._pressed(keys, "up") and self.on_ground:
            self.vel.y = JUMP_VEL
            self.on_ground = False

        # initiate drop‑through on thin platform
        if self._pressed(keys, "down") and self.on_ground and isinstance(self.drop_platform, Platform):
            # will be set in vertical_collision when we confirm which platform we stand on
            pass  # marker handled below

    def handle_actions(self, keys):
        # shield hold
        if self._pressed(keys, "shield"):
            self.shielding = True
            self.shield_tick += 1
        else:
            self.shielding = False
            self.shield_tick = 0

        # dodge (tap)
        if keys[self.controls["dodge"]] and self.dodge_timer == 0:
            self.dodge_timer = DODGE_FRAMES
            direction = 1 if self.vel.x >= 0 else -1
            self.vel.x = direction * MOVE_SPEED * 2
            self.vel.y = JUMP_VEL / 2

        # attack / special stubs (extend later)
        # if keys[self.controls["attack"]]: ...
        # if keys[self.controls["special"]]: ...

    # -------------------------------------- physics helpers
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

    def vertical_collision(self, platforms):
        self.on_ground = False

        # If we’re currently dropping through a platform, ignore it until clear
        if self.drop_platform and self.rect.top > self.drop_platform.rect.bottom:
            self.drop_platform = None

        landing_platform = None

        for p in platforms:
            # Skip platform we’re purposely dropping through
            if p is self.drop_platform:
                continue

            if not self.rect.colliderect(p.rect):
                continue

            # THIN PLATFORM LOGIC ------------------------------------
            if p.thin:
                # Only land if coming from above and feet are above top surface
                coming_from_above = self.vel.y >= 0 and self.rect.bottom - self.vel.y <= p.rect.top
                if coming_from_above and not self._pressed(pygame.key.get_pressed(), "down"):
                    landing_platform = p
            # THICK PLATFORM LOGIC -----------------------------------
            else:
                if self.vel.y > 0 and self.rect.bottom - self.vel.y <= p.rect.top:
                    landing_platform = p
                elif self.vel.y < 0 and self.rect.top - self.vel.y >= p.rect.bottom:
                    # hit underside — bonk
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0

        # finalise landing
        if landing_platform:
            self.rect.bottom = landing_platform.rect.top
            self.vel.y = 0
            self.on_ground = True

            # If player is *holding* down on a thin platform, mark it for drop‑through
            keys = pygame.key.get_pressed()
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
    Platform(pygame.Rect(WIDTH // 2 - 250, HEIGHT - 130, 120, 20), thin=True),  # left
    Platform(pygame.Rect(WIDTH // 2 + 130, HEIGHT - 130, 120, 20), thin=True),  # right
]

# Controls -----------------------------------------------------------
P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_f, special=pygame.K_g, shield=pygame.K_r, dodge=pygame.K_e)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
               attack=pygame.K_COMMA, special=pygame.K_PERIOD, shield=pygame.K_SLASH, dodge=pygame.K_SEMICOLON)

player1 = Player(WIDTH // 2 - 100, HEIGHT - 200, P1_KEYS, (255, 160, 64))
player2 = Player(WIDTH // 2 + 100, HEIGHT - 200, P2_KEYS, (90, 90, 90))
players = pygame.sprite.Group(player1, player2)

BG_COLOR = (60, 60, 70)
SHIELD_COLOR = (80, 180, 255)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # Update world
    for p in players:
        p.update(keys, platforms)

    # Render
    screen.fill(BG_COLOR)
    for pl in platforms:
        screen.blit(pl.image, pl.rect)
    for p in players:
        screen.blit(p.image, p.rect)
        if p.shielding:
            # Shrink shield radius over time but keep a minimum
            radius = max(10, p.shield_radius - int(p.shield_tick * 0.4))
    
            shield_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (*SHIELD_COLOR, 100), (radius, radius), radius)
    
            shield_pos = p.rect.centerx - radius, p.rect.centery - radius
            screen.blit(shield_surf, shield_pos)


    pygame.display.flip()

