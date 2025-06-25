"""
Purpose: Main game loop and top-level orchestration.

Contents:
- Initializes Pygame and window.
- Creates players, platforms, and attack sprite groups.
- Runs the game loop (handling input, updating, rendering).
- Renders eye, shield bubble, HUD.

Use: This is the entry point for running the game.
"""

#### TODO: implement game pause w/ P key press (READY)
#### TODO: implement win screen when one player runs out of stocks
#### TODO: implement menu options for pause screen such as restart, quit, etc.

# ------------------------------------------------ stage & sprites
#### TODO: implement stage selection w/ various platform layouts (NOT YET)
#### TODO: implement player pushing & sliding where players can push each other left/right (if both players are pushing on each other, there is no horizontal movement, else, there is slowed movement in the pushed direction) and when one lands on the other they also get pushed apart and the bottom character gets their vertical velocity downward increased if they are both in the air and the top character gets their vertical velocity upward increased with a short hop/bounce up

import sys, pygame
from .config    import *
from .entities  import Platform, Player

pygame.init()
pygame.display.set_caption("PyCats - Smash-Draft Rev 5 (stocks)")

# Rect: (x, y, width, height)
platforms = [
    Platform(pygame.Rect(THICK_PLAT_DICT["x"], THICK_PLAT_DICT["y"], THICK_PLAT_DICT["w"], THICK_PLAT_DICT["h"]), thin=False),
    Platform(pygame.Rect(THIN_PLAT_DICT_L["x"], THIN_PLAT_DICT_L["y"], THIN_PLAT_DICT_L["w"], THIN_PLAT_DICT_L["h"]), thin=True),
    Platform(pygame.Rect(THIN_PLAT_DICT_R["x"], THIN_PLAT_DICT_R["y"], THIN_PLAT_DICT_R["w"], THIN_PLAT_DICT_R["h"]), thin=True),
]

P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN, attack=pygame.K_SLASH, special=pygame.K_PERIOD, shield=pygame.K_COMMA)

#### TODO: convert player start positions to config constants (READY)
player1 = Player(PLAYER1_START_X, PLAYER1_START_Y, P1_KEYS, P1_COLOR, eye_color=BLACK, facing_right=True)
player2 = Player(PLAYER2_START_X, PLAYER2_START_Y, P2_KEYS, P2_COLOR, eye_color=WHITE, facing_right=False)
players  = pygame.sprite.Group(player1, player2)
attacks  = pygame.sprite.Group()

# ------------------------------------------------ pygame set-up
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont(None, 24)

# ------------------------------------------------ helpers
def draw_eye(p: Player):
    x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
    y = p.rect.top + EYE_OFFSET_Y
    pygame.draw.circle(screen, p.eye_color, (x,y), EYE_RADIUS)

#### TODO: implement dev info bool flag that, when True, shows all infos, and when False, only shows what should be shown to players normally
def draw_hud(p: Player, label, topright=False):
    # state = p.state.name.capitalize() # TODO: restore this after implementing KO state
    state = "KO" if not p.is_alive else p.state.name.capitalize() # TODO: remove this after implementing KO state
    jumps = f"{p.jumps_remaining} jump{'s' if p.jumps_remaining!=1 else ''} left"
    stocks = f"Lives: {p.lives}"
    for i, txt in enumerate((label, state, jumps, stocks)):
        surf = font.render(txt, True, WHITE) # TODO: replace magic vals w/ named vars
        pos  = (SCREEN_WIDTH - surf.get_width() - HUD_PADDING, HUD_PADDING + i*HUD_SPACING) if topright else (HUD_PADDING, HUD_PADDING + i*HUD_SPACING)
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
    
    # Draw alive players
    for p  in players:
        if not p.is_alive: # TODO: replace this w/ KO state check after implementing KO state
            continue
        screen.blit(p.image, p.rect)
        draw_eye(p)
        if p.shielding:
            #### TODO: convert shield radius magic nums to config constants (READY)
            r  = max(10, p.shield_radius - int(p.shield_tick * 0.4))
            s  = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            # s = surface, r = radius, (r,r) is for centering the circle on the player character
            pygame.draw.circle(s, (*SHIELD_COLOR,100), (r,r), r) #*SHIELD_COLOR is a tuple unpacking technique to get the RGB values, 100 is the alpha value for transparency
            # Draw shield bubble centered on player
            screen.blit(s, (p.rect.centerx - r, p.rect.centery - r))
    
    for a  in attacks:   screen.blit(a.image, a.rect)
    
    draw_hud(player1, "P1") # drawn by default in upper-left corner
    draw_hud(player2, "P2", topright=True)

    pygame.display.flip()

pygame.quit(); sys.exit()
