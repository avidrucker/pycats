"""
Purpose: Main game loop and top-level orchestration.

Contents:
- Initializes Pygame and window.
- Creates players, platforms, and attack sprite groups.
- Runs the game loop (handling input, updating, rendering).
- Renders eye, shield bubble, HUD.

Use: This is the entry point for running the game.
"""

import sys, pygame
from .config    import *
from .entities  import Platform, Player
from .entities  import Attack   # only for draw order

pygame.init()
pygame.display.set_caption("PyCats – Smash-Draft Rev 4")

# ------------------------------------------------ stage & sprites
platforms = [
    Platform(pygame.Rect(WIDTH//2-150, HEIGHT-40, 300, 40), thin=False),
    Platform(pygame.Rect(WIDTH//2-250, HEIGHT-130, 120, 20), thin=True),
    Platform(pygame.Rect(WIDTH//2+130, HEIGHT-130, 120, 20), thin=True),
]

P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
               attack=pygame.K_SLASH, special=pygame.K_PERIOD, shield=pygame.K_COMMA)

player1 = Player(WIDTH//2-100, HEIGHT-200, P1_KEYS, (255,160,64), True)
player2 = Player(WIDTH//2+100, HEIGHT-200, P2_KEYS, (90,90,90),  False)
players  = pygame.sprite.Group(player1, player2)
attacks  = pygame.sprite.Group()

# ------------------------------------------------ pygame set-up
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont(None, 24)

# ------------------------------------------------ helpers
def draw_eye(p: Player):
    x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
    y = p.rect.top   + EYE_OFFSET_Y
    pygame.draw.circle(screen, (0,0,0), (x,y), EYE_RADIUS)

def draw_hud(p: Player, label, topright=False):
    state = p.state.name.capitalize()
    jumps = f"{p.jumps_remaining} jump{'s' if p.jumps_remaining!=1 else ''} left"
    for i, txt in enumerate((label, state, jumps)):
        surf = font.render(txt, True, (255,255,255))
        pos  = (WIDTH - surf.get_width() - 10, 10 + i*22) if topright else (10, 10 + i*22)
        screen.blit(surf, pos)

# ------------------------------------------------ main loop
prev_keys = pygame.key.get_pressed()
running   = True
while running:
    dt = clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # ---- update
    for p in players:
        p.update(keys, prev_keys, platforms, attacks)
    attacks.update()
    prev_keys = keys

    # ---- render
    screen.fill(BG_COLOR)
    for pl in platforms: screen.blit(pl.image, pl.rect)
    
    for p  in players:
        screen.blit(p.image, p.rect)
        draw_eye(p)
        if p.shielding:
            r  = max(10, p.shield_radius - int(p.shield_tick * 0.4))
            s  = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*SHIELD_COLOR,100), (r,r), r)
            screen.blit(s, (p.rect.centerx - r, p.rect.centery - r))
    
    for a  in attacks:   screen.blit(a.image, a.rect)
    
    draw_hud(player1, "P1")
    draw_hud(player2, "P2", topright=True)

    pygame.display.flip()

pygame.quit(); sys.exit()
