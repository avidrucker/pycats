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

import pygame  # type: ignore
import math
from enum import Enum, auto
from ..config import (
    JUMP_VEL,
    MAX_JUMPS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_SIZE,
    INITIAL_LIVES,
    SHIELD_MAX_HP,
    BLAST_PADDING,
    RESPAWN_DELAY_FRAMES,
)
from .attack import Attack
from ..core.physics import apply_gravity, move_rect, solve_vertical
from ..systems.movement import step_horizontal
from ..systems.fsm import FSM, Transition


class PState(Enum):
    IDLE = auto()
    #### TODO: implement walk state
    #### TODO: implement crouch state
    #### TODO: implement double-tap LEFT/RIGHT keys to enter run state while on the ground
    RUN = auto()
    #### TODO: implement lunge attacks that start from run state
    JUMP = auto()
    FALL = auto()
    #### TODO: implement squash and stretch when jumping and landing
    SHIELD = auto()
    DODGE = auto()
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
        self.percent = 0
        self.shield_hp = SHIELD_MAX_HP
        self.lives = INITIAL_LIVES

        # ---------- spawn / KO ----------
        self.spawn_point = pygame.Vector2(x, y)
        self.is_alive = True
        self.respawn_timer = 0  # frames until next spawn

        # Input mapping
        self.controls = controls

        # Kinematics
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # Timers / counters
        self.dodge_timer = 0
        self.jumps_remaining = MAX_JUMPS

        # shield visual helpers
        self.shielding = False

        # Platform drop-through reference
        self.drop_platform = None

        # FSM current state
        self.fsm = self._build_fsm()

        # Facing
        self.facing_right = facing_right

    # ----------- hit processing ------------
    def receive_hit(self, atk):
        """Called by combat system when this player is struck."""
        if self.shielding and self.shield_hp > 0:
            self.shield_hp = max(0, self.shield_hp - atk.damage)
        #### TODO: elif dodging
        else:
            self.percent += atk.damage
            kb = atk.base_kb + atk.kb_scale * self.percent  # knockback calculation
            direction = (
                1 if atk.owner.facing_right else -1
            )  # the direction of the attack
            radians = math.radians(atk.angle)
            self.vel.x = kb * math.cos(radians) * direction
            self.vel.y = kb * -math.sin(radians)  # up = negative y

    def _handle_landing(self, was_airborne: bool):
        if self.on_ground and was_airborne:
            self.jumps_remaining = MAX_JUMPS

    # ============================================================== update
    def update(self, input_frame, platforms, attack_group):
        held = input_frame.held
        # note: currently unused, formerly called prev_keys
        #       pressed means freshly pressed this frame
        # pressed = (
        #     input_frame.pressed
        # )

        """Master per-frame update; handles KO/respawn before usual logic."""
        # ---------- dead / waiting to respawn ----------
        if not self.is_alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0 and self.lives > 0:
                self._respawn()
            return  # nothing else while dead

        # ---------- blast-zone KO check ----------
        if self._outside_blast_zone():
            self._ko()
            return

        # ---------- shield tick ----------
        if self._pressed(held, "shield") and self.fsm.state == "shield":
            self.shielding = True
            self.shield_hp = round(max(self.shield_hp - 0.2, 0), 2)
        else:
            self.shielding = False
            self.shield_hp = round(min(self.shield_hp + 0.2, SHIELD_MAX_HP), 2)

        # ---------- airborne check ----------
        # note: this is used to determine whether the player was airborne before landing, so that
        #       the player can reset their jumps when landing
        was_airborne = not self.on_ground

        # input / movement / state logic --------------------------------------
        # if self.fsm.state != "dodge": #### TODO: implement dodge state
        self.handle_actions(input_frame, attack_group)
        self.handle_move(held)

        # physics ---------------------------------------------------
        apply_gravity(self.vel)
        move_rect(self.rect, self.vel)
        self.vel, self.on_ground, self.drop_platform = solve_vertical(
            self.rect,
            self.vel,
            platforms,
            self._pressed(held, "down"),
            self.drop_platform,
        )

        self._handle_landing(was_airborne)

        # FSM state transitions -----------------------------------
        self.fsm.update()

    # ============================================================== helpers
    def _pressed(self, key_set: set[int], name):
        """key_set is usually input_frame.held or .pressed."""
        return self.controls[name] in key_set

    # horizontal input movement
    #### TODO: implement per character friction
    #### TODO: implement platform type friction modifier
    def handle_move(self, keys):
        self.vel, self.facing_right = step_horizontal(
            self.vel,
            self.facing_right,
            self.on_ground,
            self._pressed(keys, "left"),
            self._pressed(keys, "right"),
            locked=self.fsm.state
            == "shield",  # prevents moving while shielding, this may need to change when dodging is implemented
        )

    # actions
    def handle_actions(self, input_frame, attack_group):
        held = input_frame.held
        pressed = (
            input_frame.pressed
        )  # formerly prev_keys, refers to keys just freshly pressed this frame

        # ------- Shield -------------------------------------------
        if self._pressed(held, "shield") and self.fsm.state in ("idle", "shield"):
            #### TODO: prevent entering of shield state when falling/jumping, when in hurt state, etc.
            self.shielding = True
        else:
            self.shielding = False

        # if shielding, then shield HP goes down, otherwise it goes up
        if self.fsm.state == "shield":
            self.shield_hp = round(max(self.shield_hp - 0.2, 0), 2)
        else:
            self.shield_hp = round(min(self.shield_hp + 0.2, SHIELD_MAX_HP), 2)

        # ------- Dodge --------------------------------------------
        #### TODO: implement dodge as a combo press of directional + shield

        # ------- Jump ---------------------------------------------
        jump_pressed = self._pressed(pressed, "up")
        #### TODO: determine whether walking off of a ledge "consumes" a jump
        if (
            jump_pressed
            and self.jumps_remaining
            and self.fsm.state in ("fall", "jump", "idle", "run")
        ):
            self.vel.y = JUMP_VEL
            self.jumps_remaining -= 1

        # ------- Attack -------------------------------------------
        #### TODO: implement attack buffering, that attacks can be chained
        atk_pressed = self._pressed(pressed, "attack")
        if atk_pressed and self.fsm.state not in ("shield", "dodge"):
            attack_group.add(Attack(self, disappear_on_hit=False))
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/run state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

    # ============================================================= KO / respawn
    def _outside_blast_zone(self) -> bool:
        return (
            self.rect.right < -BLAST_PADDING
            or self.rect.left > SCREEN_WIDTH + BLAST_PADDING
            or self.rect.bottom < -BLAST_PADDING
            or self.rect.top > SCREEN_HEIGHT + BLAST_PADDING
        )

    def _ko(self):
        self.lives -= 1
        self.is_alive = False
        self.respawn_timer = RESPAWN_DELAY_FRAMES
        # hide sprite off-screen
        self.rect.center = (-1000, -1000)
        self.vel.update(0, 0)
        self.fsm.state = "ko"

    def _respawn(self):
        #### TODO: implement temporary respawn invulnerability
        #### TODO: implement spawning animation
        #### TODO: ensure that lives don't go negative
        #### TODO: implement respawn visible count-down
        self.is_alive = True
        self.rect.midbottom = self.spawn_point
        self.vel.update(0, 0)
        self.jumps_remaining = MAX_JUMPS
        self.percent = 0
        self.shield_hp = SHIELD_MAX_HP

    # --------------------------------------------------- FSM scaffold (pass-A)
    def _build_fsm(self) -> FSM:
        return FSM(
            state="idle",
            table={
                "idle": [
                    Transition(
                        "run", lambda f, ctx: self.vel.x != 0 and self.on_ground
                    ),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition(
                        "fall", lambda f, ctx: not self.on_ground and self.vel.y > 0
                    ),
                    Transition("shield", lambda f, ctx: self.shielding),
                ],
                "run": [
                    Transition("idle", lambda f, ctx: self.vel.x == 0),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition(
                        "fall", lambda f, ctx: not self.on_ground and self.vel.y > 0
                    ),
                ],
                "jump": [
                    Transition("fall", lambda f, ctx: self.vel.y >= 0),
                    Transition("ko", lambda f, ctx: not self.is_alive),
                ],
                "fall": [
                    Transition(
                        "idle", lambda f, ctx: self.on_ground and self.vel.x == 0
                    ),
                    Transition(
                        "run", lambda f, ctx: self.on_ground and self.vel.x != 0
                    ),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition("ko", lambda f, ctx: not self.is_alive),
                ],
                "shield": [Transition("idle", lambda f, ctx: not self.shielding)],
                "ko": [Transition("idle", lambda f, ctx: self.is_alive)],
            },
        )
