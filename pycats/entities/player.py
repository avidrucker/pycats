import pygame
from enum        import Enum, auto
from ..config    import (GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, JUMP_VEL,
                         DODGE_FRAMES, MAX_JUMPS, WIDTH, HEIGHT)
from .attack     import Attack

#### TODO: implement grabs which are combo regular-attack + shield, and can be initiated from idle or shielding
#### TODO: implement dodges which are combo move + shield, and can be iniated from idle or walking
#### TODO: research and implement move/input buffering
#### TODO: implement friction and horizontal movement acceleration

class PState(Enum):
    IDLE   = auto()
    RUN    = auto()
    JUMP   = auto()
    FALL   = auto()
    SHIELD = auto()
    DODGE  = auto()

class Player(pygame.sprite.Sprite):
    SIZE = (40, 60)

    def __init__(self, x, y, controls: dict, color, facing_right=True):
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
        self.dodge_timer   = 0
        self.jumps_remaining = MAX_JUMPS
        self.shielding     = False
        self.shield_radius = 30
        self.shield_tick   = 0

        # Platform drop-through reference
        self.drop_platform = None

        # FSM current state
        self.state = PState.IDLE

        # Facing
        self.facing_right = facing_right

    # ============================================================== update
    def update(self, keys, prev_keys, platforms, attack_group):
        if self._pressed(keys, "shield") and self.state == PState.SHIELD:
            self.shielding = True
            self.shield_tick += 1
        else:
            self.shielding = False
            self.shield_tick = 0
            #### TODO: implement slow replenishing of shield when not in shielded state

        # timers ----------------------------------------------------
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
            if self.dodge_timer == 0 and self.state == PState.DODGE:
                self.state = PState.FALL if not self.on_ground else PState.IDLE

        # input & state logic --------------------------------------
        if self.state != PState.DODGE:
            self.handle_actions(keys, prev_keys, attack_group)
            self.handle_move(keys)

        # physics ---------------------------------------------------
        self.apply_gravity()
        self.horizontal_bounds()
        self.vertical_collision(platforms, keys)

        # automatic state transitions ------------------------------
        if self.state not in (PState.SHIELD, PState.DODGE):
            if not self.on_ground:
                self.state = PState.JUMP if self.vel.y < 0 else PState.FALL
            else:
                self.state = PState.RUN if self.vel.x else PState.IDLE

    # ============================================================== helpers
    def _pressed(self, snapshot, name):
        return snapshot[self.controls[name]]

    def handle_move(self, keys):
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

    def handle_actions(self, keys, prev_keys, attack_group):
        # ------- Shield -------------------------------------------
        if self._pressed(keys, "shield"):
            if self.state != PState.SHIELD:
                self.state = PState.SHIELD
            self.shielding = True
            self.shield_tick += 1
        elif self.state == PState.SHIELD:
            self.state = PState.IDLE

        # ------- Dodge --------------------------------------------
        #### TODO: implement dodge as a combo press of directional + shield
        # if (self._pressed(keys, "dodge") and not self._pressed(prev_keys, "dodge")
        #         and self.dodge_timer == 0 and self.state != PState.SHIELD):
        #     self.state = PState.DODGE
        #     self.dodge_timer = DODGE_FRAMES
        #     direction = 1 if self.vel.x >= 0 else -1
        #     self.vel.x = direction * MOVE_SPEED * 2
        #     self.vel.y = JUMP_VEL / 2
        #     return

        # ------- Jump ---------------------------------------------
        jump_pressed = (self._pressed(keys, "up")
                        and not self._pressed(prev_keys, "up")
                        and self.state != PState.SHIELD)
        #### TODO: determine whether walking off of a ledge "consumes" a jump
        if jump_pressed and self.jumps_remaining:
            self.vel.y = JUMP_VEL
            self.jumps_remaining -= 1
            self.state = PState.JUMP

        # ------- Attack -------------------------------------------
        atk_pressed = self._pressed(keys, "attack") and not self._pressed(prev_keys, "attack")
        if atk_pressed and self.state not in (PState.SHIELD, PState.DODGE):
            attack_group.add(Attack(self))

    # ============================================================== physics
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
        self.on_ground = False

        def x_overlap(a: pygame.Rect, b: pygame.Rect):
            return a.right > b.left and a.left < b.right

        if self.drop_platform and self.rect.top > self.drop_platform.rect.bottom:
            self.drop_platform = None

        landing = None
        for p in platforms:
            if p is self.drop_platform:
                continue

            overlap = self.rect.colliderect(p.rect)
            flush   = (self.rect.bottom == p.rect.top and self.vel.y >= 0
                       and x_overlap(self.rect, p.rect))

            if not (overlap or flush):
                continue

            if p.thin:
                from_above = self.vel.y >= 0 and self.rect.bottom - self.vel.y <= p.rect.top
                if from_above and not self._pressed(keys, "down"):
                    landing = p
            else:
                if self.vel.y >= 0 and self.rect.bottom - self.vel.y <= p.rect.top:
                    landing = p
                elif self.vel.y < 0 and self.rect.top - self.vel.y >= p.rect.bottom:
                    self.rect.top = p.rect.bottom
                    self.vel.y = 0

        if landing:
            self.rect.bottom = landing.rect.top
            self.vel.y = 0
            self.on_ground = True
            self.jumps_remaining = MAX_JUMPS
            if landing.thin and self._pressed(keys, "down"):
                self.drop_platform = landing
