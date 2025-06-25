"""
Purpose: Defines the Player class and PState enum.

Contents:
- FSM states: IDLE, RUN, JUMP, FALL, SHIELD, DODGE
- Movement, shield logic, dodge, jump, attack
- Ground/platform collision detection
- Shield visuals and eye facing direction

Use: Core gameplay logic for player control and interaction.
"""

#### MOST READY/PRIORITY TODOS
#### TODO: add thorough docstrings to all methods and classes
#### TODO: implement friction and horizontal movement acceleration
#### TODO: change private method func signatures to start with underscore, make sure to update all calls
#### TODO: consider writing a helper that checks for fresh input vs. held input, for example for different attacks and jumping (e.g. holding down up should not repeatedly jump, and to do a double jump requires the player to press up, let go of up, and then press it again)
#### TODO: make shielding / entering shield state only possible when on the ground
#### TODO: fix bug where shield hp of 0 prevents knock-back, but it shouldn't

#### LESS READY/LOW PRIORITY TODOS
#### TODO: make shield bubble go down by X amount when the player is hit
#### TODO: make player invunerable to attacks unless they break the shield bubble
#### TODO: make player shielding ineffective against attacks when shield bubble reaches smallest size
#### TODO: make player shielding ineffective against grabs
#### TODO: implement grabs which are combo regular-attack + shield, and can be initiated from idle or shielding, and can be used against an opponent who is in idle, walking, running, or shielding state, and the grab will put the opponent into a grabbed state where they cannot move or attack, and the grabber can then throw them off the stage or do a follow-up attack
#### TODO: implement dodges which are combo move + shield, and can be iniated from idle or walking
#### TODO: research and implement move/input buffering
#### TODO: implement fast fall by holding down which will cause the player to fall faster
#### TODO: make shield bubble shrink grow back over time when not shielding
#### TODO: make shielding in the air do an air dodge instead of a shield bubble, and max sure to cap air dodges to once per jump/fall status entering (i.e. until the player lands (Q: or is hit?) they don't get another air dodge)
#### TODO: implement ledge grabbing mechanics where the player can grab the ledge when falling off of a platform, and then can press up to get back on the platform, or down to drop down from the ledge, they get limited time invunerability while hanging on the ledge, and eventually fall off the ledge if they don't get back on the platform (Q: can thin platforms be grabbed as well as thick platforms?)

import pygame, math
from enum        import Enum, auto
from ..config import (GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, JUMP_VEL, DODGE_FRAMES, MAX_JUMPS, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_SIZE, INITIAL_LIVES, MAX_SHIELD_RADIUS, SHIELD_MAX_HP, BLAST_PADDING, RESPAWN_DELAY_FRAMES)
from .attack     import Attack

class PState(Enum):
    IDLE   = auto()
    #### TODO: implement walk state
    #### TODO: implement crouch state
    #### TODO: implement double-tap LEFT/RIGHT keys to enter run state while on the ground
    RUN    = auto()
    #### TODO: implement lunge attacks that start from run state
    JUMP   = auto()
    FALL   = auto()
    #### TODO: implement squash and stretch when jumping and landing
    SHIELD = auto()
    DODGE  = auto()
    #### TODO: implement grabbed state
    #### TODO: implement grabbing state
    #### TODO: implement stunned state
    #### TODO: implement hurt state
    #### TODO: implement KO state

class Player(pygame.sprite.Sprite):
    #### TODO: implement variable player sizes
    SIZE = PLAYER_SIZE

    def __init__(self, x, y, controls: dict, color, eye_color, facing_right=True):
        super().__init__()
        self.image = pygame.Surface(self.SIZE)
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.eye_color = eye_color

        # ---------- combat stats ----------
        self.percent   = 0
        self.shield_hp = SHIELD_MAX_HP
        self.lives     = INITIAL_LIVES

        # ---------- spawn / KO ----------        
        self.spawn_point = pygame.Vector2(x, y)
        self.is_alive    = True
        self.respawn_timer = 0     # frames until next spawn

        # Input mapping
        self.controls = controls

        # Kinematics
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # Timers / counters
        self.dodge_timer   = 0
        self.jumps_remaining = MAX_JUMPS
        
        # shield visual helpers
        self.shielding     = False

        # Platform drop-through reference
        self.drop_platform = None

        # FSM current state
        self.state = PState.IDLE

        # Facing
        self.facing_right = facing_right


    # ----------- hit processing ------------
    def receive_hit(self, atk):
        """Called by combat system when this player is struck."""
        if self.shielding and self.shield_hp > 0:
            self.shield_hp = max(0, self.shield_hp - atk.damage)
        else:
            self.percent += atk.damage
            kb = atk.base_kb + atk.kb_scale * self.percent
            direction = 1 if atk.owner.facing_right else -1
            radians   = math.radians(atk.angle)
            self.vel.x = kb * math.cos(radians) * direction
            self.vel.y = kb * -math.sin(radians)  # up = negative y
            self.state = PState.FALL

    # ============================================================== update
    def update(self, keys, prev_keys, platforms, attack_group):
        """Master per-frame update; handles KO/respawn before usual logic."""
        # ---------- dead / waiting to respawn ----------
        if not self.is_alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0 and self.lives > 0:
                self._respawn()
            return                              # nothing else while dead

        # ---------- blast-zone KO check ----------
        if self._outside_blast_zone():
            self._ko()
            return
        
        # ---------- shield tick ----------
        if self._pressed(keys, "shield") and self.state == PState.SHIELD:
            self.shielding = True
            self.shield_hp = round(max(self.shield_hp - 0.2, 0), 2)
        else:
            self.shielding = False
            self.shield_hp = round(min(self.shield_hp + 0.2, SHIELD_MAX_HP), 2)

        # timers ----------------------------------------------------
        if self.dodge_timer > 0: #### Q: is `if self.dodge_timer:` better or more performant?
            self.dodge_timer -= 1
            if self.dodge_timer == 0 and self.state == PState.DODGE:
                self.state = PState.FALL if not self.on_ground else PState.IDLE

        # input / movement / state logic --------------------------------------
        if self.state != PState.DODGE:
            self.handle_actions(keys, prev_keys, attack_group)
            self.handle_move(keys)

        # physics ---------------------------------------------------
        self.apply_gravity()
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

    # input movement
    def handle_move(self, keys):
        if self.state == PState.SHIELD:
            self.vel.x = 0
            return

        self.vel.x = int(self.vel.x*0.75)  # apply friction
        if self._pressed(keys, "left"):
            self.vel.x = -MOVE_SPEED
            self.facing_right = False
        if self._pressed(keys, "right"):
            self.vel.x = MOVE_SPEED
            self.facing_right = True

    # actions
    def handle_actions(self, keys, prev_keys, attack_group):
        # ------- Shield -------------------------------------------
        if self._pressed(keys, "shield"):
            #### TODO: prevent entering of shield state when falling/jumping, when in hurt state, etc.
            if self.state != PState.SHIELD:
                self.state = PState.SHIELD
            self.shielding = True
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
            attack_group.add(Attack(self, disappear_on_hit=False))
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/run state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

    # ============================================================== physics
    def apply_gravity(self):
        if self.vel.y < MAX_FALL_SPEED:
            self.vel.y += GRAVITY
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

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

    # ============================================================= KO / respawn
    def _outside_blast_zone(self) -> bool:
        return (self.rect.right  < -BLAST_PADDING or
                self.rect.left   > SCREEN_WIDTH + BLAST_PADDING or
                self.rect.bottom < -BLAST_PADDING or
                self.rect.top    > SCREEN_HEIGHT + BLAST_PADDING)

    def _ko(self):
        self.lives -= 1
        self.is_alive = False
        self.respawn_timer = RESPAWN_DELAY_FRAMES
        # hide sprite off-screen
        self.rect.center = (-1000, -1000)
        self.vel.update(0, 0)

    def _respawn(self):
        #### TODO: implement temporary respawn invulnerability
        #### TODO: implement spawning animation
        #### TODO: ensure that lives don't go negative
        #### TODO: implement respawn visible count-down
        self.is_alive         = True
        self.rect.midbottom   = self.spawn_point
        self.vel.update(0, 0)
        self.state            = PState.FALL   # will auto-snap to IDLE on landing
        self.jumps_remaining  = MAX_JUMPS
        self.percent          = 0
        self.shield_hp        = SHIELD_MAX_HP