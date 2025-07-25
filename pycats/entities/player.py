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
#### TODO: change private method func signatures to start with underscore, make sure to update all calls
#### DONE: implement ground dodging will not take players off the ledge
#### DONE: implement spot dodge where player can dodge in place without moving, and this does not move them below a thin ledge if they are holding shield and down
#### TODO: fix bug where consecutive quick hits will quickly cause the defender to be projected off the stage
#### TODO: fix bug where player stays red sometimes after being hit while moving or attacking
#### TODO: implement prone status where player is knocked down and cannot move or attack for a short time, and then can get up by pressing a button

#### LESS READY/LOW PRIORITY TODOS
#### TODO: make player shielding ineffective against grabs
#### TODO: implement grabs which are combo regular-attack + shield, and can be initiated from idle or shielding, and can be used against an opponent who is in idle, walking, running, or shielding state, and the grab will put the opponent into a grabbed state where they cannot move or attack, and the grabber can then throw them off the stage or do a follow-up attack
#### TODO: research and implement move/input buffering
#### TODO: implement fast fall by holding down which will cause the player to fall faster
#### TODO: implement ledge grabbing mechanics where the player can grab the ledge when falling off of a platform, and then can press up to get back on the platform, or down to drop down from the ledge, they get limited time invulnerability while hanging on the ledge, and eventually fall off the ledge if they don't get back on the platform (Q: can thin platforms be grabbed as well as thick platforms?)

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
    HURT_TIME,
    STUN_TIME,
    DODGE_TIME,
    DODGE_SPEED,
    WHITE,
    RED,
    YELLOW,
    PLAYER_ATTACK_DURATION,
)
from .attack import Attack
from ..core.physics import (
    apply_gravity,
    move_rect,
    solve_vertical,
    apply_horizontal_friction,
    find_current_platform,
    would_dodge_off_platform,
)
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
    KO = auto()  # knocked out, waiting to respawn
    HURT = auto()  # hit by an attack, unable to move or attack for a short time


class Player(pygame.sprite.Sprite):
    #### TODO: implement variable player sizes
    SIZE = PLAYER_SIZE

    def __init__(
        self, x, y, controls: dict, color, eye_color, char_name, facing_right=True
    ):
        super().__init__()
        self.image = pygame.Surface(self.SIZE)
        self.char_color = color
        self.char_name = char_name
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.eye_color = eye_color

        # Secondary fur color for stripes
        if color == (255, 160, 64):  # Orange player (P1_COLOR)
            self.stripe_color = (204, 102, 0)  # Dark orange
        elif color == (90, 90, 90):  # Gray player (P2_COLOR)
            self.stripe_color = (0, 0, 0)  # Black
        else:
            self.stripe_color = color  # Default to same color if no match

        # ---------- combat stats ----------
        self.percent = 0
        self.shield_hp = SHIELD_MAX_HP
        self.lives = INITIAL_LIVES

        # ---------- game statistics ----------
        self.attacks_made = 0  # Total attacks initiated
        self.hits_landed = 0  # Successful hits on opponent
        self.suicides = 0  # Deaths without being hit (self-inflicted)
        self.was_hit_before_ko = False  # Track if last KO was from being hit

        # ---------- spawn / KO ----------
        self.spawn_point = pygame.Vector2(x, y)
        self.is_alive = True

        # Input mapping
        self.controls = controls

        # Kinematics
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # Timers / counters
        self.respawn_timer = 0  # frames until next spawn
        self.dodge_timer = 0
        self.hurt_timer = 0
        self.stun_timer = 0
        self.attack_timer = 0  # for a given attack, how long until the player character is done activating/initiating an attack (this is distinct from the attack's lifetime, which is handled by the Attack class)
        self.invulnerable_timer = 0  # used for invulnerability mid-dodge, post-respawn, or while ledge grabbing
        self.jumps_remaining = MAX_JUMPS
        self.air_dodge_ok = True  # players can only air dodge once per combined sustained jump/fall status, until they land
        self.invulnerable = False  # used for dodging and invulnerability after being hit, respawned, or ledge grabbing
        self.done_attacking = (
            True  # used to determine when the player is done attacking
        )

        # shield visual helpers
        self.shield_attempting = False

        # Platform drop-through reference
        self.drop_platform = None

        # Edge-aware dodge state
        self.dodge_blocked_by_edge = False  # Track if current dodge is blocked by edge
        self.spot_dodge_shield_held = (
            False  # Track if shield was held during spot dodge
        )

        # FSM current state
        self.fsm = self._build_fsm()

        # Facing
        self.facing_right = facing_right
        self.original_facing_right = (
            facing_right  # Store original facing direction for respawn
        )

        # Tail (initialize after facing_right is set)
        from .tail import Tail

        self.tail = Tail(self)

    # ----------- hit processing ------------
    def receive_hit(self, atk):
        """Called by combat system when this player is struck."""
        self.record_hit_received()  # Track that this player was hit
        if self.shield_attempting and self.shield_hp > 0:
            self.shield_hp = max(0, self.shield_hp - atk.damage)
            if self.shield_hp == 0:
                self._start_stun()
        #### TODO: elif dodging
        else:
            self._start_hurt()
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
            self.jumps_remaining = MAX_JUMPS  # reset jumps when landing
            self.air_dodge_ok = True  # reset air dodge availability

    # ============================================================== update
    def update(self, input_frame, platforms, attack_group):
        held = input_frame.held
        # note: currently unused, formerly called prev_keys
        #       pressed means freshly pressed this frame
        pressed = input_frame.pressed

        # Store platforms for edge detection during dodge
        self.platforms = platforms

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
        # if shielding, then shield HP goes down, otherwise it goes up
        if self.fsm.state == "shield":
            self.shield_hp = round(max(self.shield_hp - 0.2, 0), 2)
        else:
            self.shield_hp = round(min(self.shield_hp + 0.2, SHIELD_MAX_HP), 2)

        #
        if not self._pressed(held, "shield") and not self._pressed(pressed, "shield"):
            self.shield_attempting = False

        # ---------- airborne check ----------
        # note: this is used to determine whether the player was airborne before landing, so that
        #       the player can reset their jumps when landing
        was_airborne = not self.on_ground

        # input / movement / state logic --------------------------------------
        dodge_initiated = False
        if self.fsm.state not in ("dodge", "hurt", "stun"):
            dodge_initiated = self.handle_actions(input_frame, attack_group)
            # Don't apply movement if a dodge was just initiated to prevent friction from reducing dodge velocity
            if not dodge_initiated:
                self.handle_move(held)

        # physics ---------------------------------------------------
        # Apply gravity - but not for ground-based spot dodges to prevent falling through thin platforms
        # Air dodges should still have normal gravity
        is_ground_spot_dodge = (
            self.fsm.state == "dodge" and self.spot_dodge_shield_held and self.on_ground
        )

        if not is_ground_spot_dodge:
            apply_gravity(self.vel)
        else:
            # For ground spot dodges, keep velocity minimal to prevent any fall-through
            self.vel.y = 0
            # debugging
            # print(f"GROUND SPOT DODGE GRAVITY PREVENTION: {self.char_name} gravity blocked during ground spot dodge")

        # Edge-aware dodge: prevent horizontal movement if it would take player off platform
        # This happens AFTER any friction is applied and immediately before movement
        if self.fsm.state == "dodge" and self.on_ground and hasattr(self, "platforms"):
            current_platform = find_current_platform(self.rect, self.platforms)
            if current_platform is not None:
                # First, check if velocity would take us off edge
                if self.vel.x != 0 and would_dodge_off_platform(
                    self.rect, self.vel.x, current_platform
                ):
                    # Stop horizontal movement to prevent falling off
                    # debugging
                    # print(f"EDGE BLOCKED: {self.char_name} dodge movement stopped (vel was {self.vel.x}) at pos ({self.rect.centerx}, {self.rect.centery})")
                    self.vel.x = 0
                    self.dodge_blocked_by_edge = True

                # Second, clamp position to ensure player never goes past platform edges
                # This is a safety net in case any movement still occurs
                platform_rect = current_platform.rect

                # Prevent left edge of player from going past left edge of platform
                if self.rect.left < platform_rect.left:
                    old_pos = self.rect.left
                    self.rect.left = platform_rect.left
                    self.vel.x = 0  # Stop any leftward movement
                    # debugging
                    # print(f"CLAMPED LEFT: {self.char_name} from {old_pos} to {self.rect.left}")

                # Prevent right edge of player from going past right edge of platform
                if self.rect.right > platform_rect.right:
                    old_pos = self.rect.right
                    self.rect.right = platform_rect.right
                    self.vel.x = 0  # Stop any rightward movement
                    # debugging
                    # print(f"CLAMPED RIGHT: {self.char_name} from {old_pos} to {self.rect.right}")
        # No else clause needed - edge detection is correctly conditional

        # Apply movement - this must happen immediately after edge check
        move_rect(self.rect, self.vel)

        # Post-movement clamping: ensure dodge didn't move player off platform
        if self.fsm.state == "dodge" and self.on_ground and hasattr(self, "platforms"):
            current_platform = find_current_platform(self.rect, self.platforms)
            if current_platform is not None:
                platform_rect = current_platform.rect

                # Clamp position if player went off platform edges
                if self.rect.left < platform_rect.left:
                    # print(f"POST-MOVE CLAMP LEFT: {self.char_name} moved to {self.rect.left}, clamping to {platform_rect.left}")
                    self.rect.left = platform_rect.left
                    self.vel.x = 0

                if self.rect.right > platform_rect.right:
                    # print(f"POST-MOVE CLAMP RIGHT: {self.char_name} moved to {self.rect.right}, clamping to {platform_rect.right}")
                    self.rect.right = platform_rect.right
                    self.vel.x = 0

        # Special handling for preventing drop-through of thin platforms
        # when shield is held with down (both during ground spot dodge and shield state)
        is_shield_down_held = self._pressed(held, "shield") and self._pressed(
            held, "down"
        )
        should_prevent_drop_through = (
            # During ground spot dodge (only, not air dodge)
            (self.fsm.state == "dodge" and self.spot_dodge_shield_held)
            or
            # In shield state with down held (after spot dodge or manual shielding)
            (self.fsm.state == "shield" and is_shield_down_held)
        )

        # debugging
        # if should_prevent_drop_through:
        #     print(f"DROP THROUGH BLOCKED: {self.char_name} prevented from dropping through thin platform (state: {self.fsm.state})")

        self.vel, self.on_ground, self.drop_platform = solve_vertical(
            self.rect,
            self.vel,
            platforms,
            self._pressed(held, "down")
            and not should_prevent_drop_through,  # Don't drop through if conditions met
            self.drop_platform,
        )

        # Special case: maintain on_ground status during ground spot dodge to prevent unwanted fall transitions
        if self.fsm.state == "dodge" and self.spot_dodge_shield_held:
            # Force on_ground to remain True during ground spot dodge to prevent falling
            if not self.on_ground:
                # debugging
                # print(f"GROUND SPOT DODGE GROUND FIX: {self.char_name} forced back to ground during spot dodge")
                self.on_ground = True
                # Also ensure the player stays at the exact platform level
                current_platform = find_current_platform(self.rect, platforms)
                if current_platform:
                    self.rect.bottom = current_platform.rect.top
                    # debugging
                    # print(f"GROUND SPOT DODGE POSITION FIX: {self.char_name} position corrected to platform top")

        self._handle_landing(was_airborne)

        # Non-shield timers tick
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        if self.hurt_timer == 0 and self.fsm.state == "hurt":
            self.image.fill(self.char_color)  # reset image color to normal
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if self.stun_timer == 0 and self.fsm.state == "stun":
            self.image.fill(self.char_color)  # reset image color to normal
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.dodge_timer == 0 and self.fsm.state == "dodge":
            self.invulnerable = False  # reset invulnerability after dodge ends
            self.image.fill(self.char_color)  # reset image color to normal
            self.vel.x = 0  # stop horizontal movement after dodge ends

            # Handle spot dodge transition
            if self.spot_dodge_shield_held:
                # print(f"SPOT DODGE END: {self.char_name} ending spot dodge, shield_held={self._pressed(held, 'shield')}")
                if self._pressed(held, "shield"):
                    # Force shield attempting to true for smooth transition
                    self.shield_attempting = True
                    # print(f"SPOT DODGE TRANSITION: {self.char_name} shield_attempting set to True")
                self.spot_dodge_shield_held = False  # reset spot dodge flag
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.attack_timer == 0 and self.fsm.state == "attack":
            self.done_attacking = True

        # Update tail physics
        self.tail.update()

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

        # ------- Jump ---------------------------------------------
        jump_pressed = self._pressed(pressed, "up")
        #### TODO: determine whether walking off of a ledge "consumes" a jump
        if (
            jump_pressed
            and self.jumps_remaining
            and self.fsm.state not in ("dodge", "hurt", "stun")
        ):
            self.vel.y = JUMP_VEL
            self.jumps_remaining -= 1
            self.shield_attempting = False
            return False  # No dodge initiated

        # ------- Dodge Logic (check first to prevent shield conflicts) -------
        #### DONE: implement dodge as a combo press of directional + shield
        #### DONE: reset air_dodge_ok when landing
        #### TODO: implement directional flipping when ground dodging/rolling
        #### TODO: prevent repeated dodges by holding down shield and a directional, what happens instead is that the player will enter a shield state, and then can press a direction to dodge again
        #### DONE: make player rect flash semi-transparent white while in dodge state
        # Shield-plus-direction = dodge
        can_dodge_state = self.fsm.state in ("idle", "jump", "fall", "shield")
        # Special case: allow adding direction to neutral air dodges
        can_modify_air_dodge = (
            self.fsm.state == "dodge"
            and not self.on_ground
            and abs(self.vel.x) < 0.1  # Currently has no horizontal velocity
            and self.dodge_timer > 0  # Still dodging
        )

        if self.fsm.state == "dodge" and not self.on_ground:
            print(
                f"DEBUG: Air dodge check for {self.char_name}: state={self.fsm.state}, on_ground={self.on_ground}, vel.x={self.vel.x}, abs(vel.x)={abs(self.vel.x)}, dodge_timer={self.dodge_timer}, can_modify={can_modify_air_dodge}"
            )

        if can_modify_air_dodge:
            print(f"DEBUG: can_modify_air_dodge=True for {self.char_name}")

        shield_down = self._pressed(held, "shield")
        shield_pressed = self._pressed(pressed, "shield")
        dodge_initiated = False

        if (can_dodge_state and self.dodge_timer == 0) or can_modify_air_dodge:
            dir_x = None

            # Priority 1: Check for simultaneous shield + direction press (including spot dodge)
            if shield_pressed and self._pressed(pressed, "down"):
                dir_x = 0  # spot dodge
            elif shield_pressed and self._pressed(pressed, "left"):
                dir_x = -1  # left dodge
            elif shield_pressed and self._pressed(pressed, "right"):
                dir_x = 1  # right dodge
            # Priority 2: Check if shield is *just* pressed for air dodge or momentum dodge
            elif (
                shield_pressed and not can_modify_air_dodge
            ):  # Don't allow shield-only during air dodge modification
                if not self.on_ground:
                    dir_x = 0  # air dodge without direction pressed
                elif abs(self.vel.x) > 0.1:
                    dir_x = 1 if self.vel.x > 0 else -1
            # Priority 3: Check if a direction is freshly pressed while shield is held (ground dodge)
            # OR if direction is pressed during neutral air dodge
            elif shield_down or can_modify_air_dodge:
                if self._pressed(pressed, "down"):
                    dir_x = 0
                elif self._pressed(pressed, "left"):
                    dir_x = -1
                elif self._pressed(pressed, "right"):
                    dir_x = 1

            if dir_x is not None:
                if can_modify_air_dodge:
                    # Special case: modifying existing air dodge
                    if dir_x != 0:  # Only allow directional modification, not neutral
                        print(
                            f"DEBUG: Modifying air dodge velocity from {self.vel.x} to {dir_x * DODGE_SPEED}"
                        )
                        self.vel.x = (dir_x * DODGE_SPEED) + self.vel.x
                        dodge_initiated = True
                elif self.on_ground or self.air_dodge_ok:
                    self._start_dodge(dir_x)
                    dodge_initiated = True
                    if not self.on_ground:
                        self.air_dodge_ok = False
                # debugging
                # print("dodge handled")
                return True  # Dodge initiated, no further actions needed

        # ------- Shield -------------------------------------------
        # 2.  Shield can **only** be (re)started while on ground and not airborne
        # Don't enter shield state if we just initiated a dodge
        grounded_can_shield = (
            self.on_ground
            and self.fsm.state in ("idle", "shield", "dodge", "run")
            and self.dodge_timer == 0
            and not dodge_initiated  # Don't shield if we just started dodging
        )

        if self._pressed(held, "shield") and grounded_can_shield:
            #### TODO: prevent entering of shield state when falling/jumping, when in hurt state, etc.
            self.shield_attempting = True
        else:
            # Don't reset shield_attempting if we just initiated a dodge or are currently dodging
            if not dodge_initiated and self.fsm.state != "dodge":
                self.shield_attempting = False

        # ------- Attack -------------------------------------------
        #### TODO: implement attack buffering, that attacks can be chained
        atk_pressed = self._pressed(pressed, "attack")
        if atk_pressed and self.fsm.state not in ("shield", "dodge"):
            attack_group.add(Attack(self, disappear_on_hit=False))
            self.record_attack_made()  # Track attack statistics
            self.done_attacking = False  # set to false when attack starts, will be set to true when attack is done
            self.attack_timer = PLAYER_ATTACK_DURATION
            #### TODO: implement unique custom attacks for each player w/ variable damage, knockback, and angle, attack activation time, attack duration, etc.
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/run state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

        return False  # No dodge initiated

    # ============================================================= KO / respawn
    def _outside_blast_zone(self) -> bool:
        return (
            self.rect.right < -BLAST_PADDING
            or self.rect.left > SCREEN_WIDTH + BLAST_PADDING
            or self.rect.bottom < -BLAST_PADDING
            or self.rect.top > SCREEN_HEIGHT + BLAST_PADDING
        )

    def _ko(self):
        # Track if this was a suicide (no hit received before KO)
        if not self.was_hit_before_ko:
            self.suicides += 1

        # debugging
        # print(f"PLAYER KO: {self.char_name} fell off and lost a life! (lives: {self.lives-1})")
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
        self.was_hit_before_ko = False  # Reset hit tracking for next life
        self.facing_right = (
            self.original_facing_right
        )  # Restore original facing direction
        self.reset_visual_state()  # Reset visual appearance to original color

    # state starters ----------------------------
    def _start_hurt(self) -> None:  # knockback: pygame.Vector2
        # self.fsm.state = "hurt"
        self.hurt_timer = HURT_TIME
        # self.vel.update(knockback) # this already handled in receive_hit
        self.image.fill(RED)  # red-flash tint

    def _start_stun(self) -> None:
        # self.fsm.state = "stun"
        self.stun_timer = STUN_TIME
        self.image.fill(YELLOW)  # yellow-flash tint
        self.vel.update(0, 0)

    def _start_dodge(self, dir_x: int) -> None:
        self.dodge_timer = DODGE_TIME
        self.invulnerable = True
        self.image.fill(WHITE)  # flash white
        self.dodge_blocked_by_edge = False  # Reset edge blocking flag

        # Only set spot_dodge_shield_held for ground-based spot dodges (not air dodges)
        if dir_x == 0 and self.on_ground:
            # Ground spot dodge - no movement, special thin platform protection
            self.vel.update(0, 0)  # No movement for ground spot dodge
            self.spot_dodge_shield_held = True
            # debugging
            # print(f"GROUND SPOT DODGE START: {self.char_name} ground spot dodge initiated")
        elif dir_x == 0 and not self.on_ground:
            # Air dodge - preserve Y velocity, no horizontal movement
            # self.vel.x = 0  # Only reset horizontal velocity for air dodge
            self.spot_dodge_shield_held = False
            # debugging
            # print(f"AIR DODGE START: {self.char_name} air dodge initiated (preserving Y velocity)")
        else:
            # Directional dodge (ground roll) - set horizontal velocity, preserve or reset Y
            if self.on_ground:
                self.vel.update(dir_x * DODGE_SPEED, 0)  # Ground roll
            else:
                self.vel.x = (
                    dir_x * DODGE_SPEED + self.vel.x
                )  # Air directional dodge - preserve Y velocity
            self.spot_dodge_shield_held = False

    # --------------------------------------------------- FSM scaffold (pass-A)
    def _build_fsm(self) -> FSM:
        return FSM(
            state="idle",
            table={
                "idle": [
                    Transition("attack", lambda f, ctx: self.attack_timer > 0),
                    Transition(
                        "dodge", lambda f, ctx: self.dodge_timer > 0
                    ),  # Dodge should take priority
                    Transition(
                        "run", lambda f, ctx: self.vel.x != 0 and self.on_ground
                    ),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition(
                        "fall", lambda f, ctx: not self.on_ground and self.vel.y > 0
                    ),
                    Transition("shield", lambda f, ctx: self.shield_attempting),
                    Transition("hurt", lambda f, ctx: self.hurt_timer > 0),
                ],
                "run": [
                    Transition("attack", lambda f, ctx: self.attack_timer > 0),
                    Transition(
                        "dodge", lambda f, ctx: self.dodge_timer > 0
                    ),  # Dodge should take priority
                    Transition("idle", lambda f, ctx: self.vel.x == 0),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition(
                        "fall", lambda f, ctx: not self.on_ground and self.vel.y > 0
                    ),
                    Transition("hurt", lambda f, ctx: self.hurt_timer > 0),
                    Transition(
                        "shield",
                        lambda f, ctx: self.shield_attempting and self.on_ground,
                    ),  # can enter shield state while running on the ground
                ],
                "jump": [
                    Transition("attack", lambda f, ctx: self.attack_timer > 0),
                    Transition("fall", lambda f, ctx: self.vel.y >= 0),
                    Transition("ko", lambda f, ctx: not self.is_alive),
                    Transition("dodge", lambda f, ctx: self.dodge_timer > 0),
                    Transition("hurt", lambda f, ctx: self.hurt_timer > 0),
                ],
                "fall": [
                    Transition("attack", lambda f, ctx: self.attack_timer > 0),
                    Transition(
                        "idle", lambda f, ctx: self.on_ground and self.vel.x == 0
                    ),
                    Transition(
                        "run", lambda f, ctx: self.on_ground and self.vel.x != 0
                    ),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    Transition("ko", lambda f, ctx: not self.is_alive),
                    Transition("dodge", lambda f, ctx: self.dodge_timer > 0),
                    Transition("hurt", lambda f, ctx: self.hurt_timer > 0),
                ],
                "shield": [
                    Transition("idle", lambda f, ctx: not self.shield_attempting),
                    Transition("dodge", lambda f, ctx: self.dodge_timer > 0),
                    Transition("jump", lambda f, ctx: self.vel.y < 0),
                    #### TODO: stun: shield break leads to stunned state
                    #### TODO: grab: attacking while shielding leads to grabbing state
                    #### TODO: held: being grabbed by an opponent leads to held state
                ],
                "ko": [Transition("idle", lambda f, ctx: self.is_alive)],
                "dodge": [
                    Transition(
                        "shield",
                        lambda f, ctx: self.shield_attempting
                        and self.dodge_timer <= 0
                        and self.on_ground,
                    ),  # can re-enter shield state after dodging on the ground
                    Transition(
                        "idle",
                        lambda f, ctx: not self.shield_attempting
                        and self.dodge_timer <= 0
                        and self.on_ground
                        and not self.spot_dodge_shield_held,  # Don't go to idle if spot dodge shield is held
                    ),  #  and self.vel.x == 0
                    Transition(
                        "fall",
                        lambda f, ctx: self.dodge_timer <= 0 and not self.on_ground,
                    ),  # and self.vel.y > 0
                ],
                #### hurt: hit by an attack, unable to move or attack for a short time
                "hurt": [
                    Transition(
                        "idle", lambda f, ctx: self.hurt_timer <= 0 and self.on_ground
                    ),
                    Transition(
                        "fall",
                        lambda f, ctx: self.hurt_timer <= 0 and not self.on_ground,
                    ),
                    #### TODO: implement shield holding to transition from hurt to shield state
                ],
                "stun": [
                    Transition(
                        "idle", lambda f, ctx: self.stun_timer <= 0 and self.on_ground
                    ),
                    Transition(
                        "fall",
                        lambda f, ctx: self.stun_timer <= 0 and not self.on_ground,
                    ),
                ],
                "attack": [
                    Transition(
                        "idle", lambda f, ctx: self.done_attacking and self.on_ground
                    ),
                    Transition(
                        "fall",
                        lambda f, ctx: self.done_attacking and not self.on_ground,
                    ),
                ],
                #### TODO: hang: hanging on the ledge
            },
        )

    def record_attack_made(self):
        """Record that this player initiated an attack"""
        self.attacks_made += 1

    def record_hit_landed(self):
        """Record that this player successfully hit an opponent"""
        self.hits_landed += 1

    def record_hit_received(self):
        """Record that this player was hit by an opponent"""
        self.was_hit_before_ko = True

    def reset_visual_state(self):
        """Reset player visual appearance to original color"""
        self.image.fill(self.char_color)
