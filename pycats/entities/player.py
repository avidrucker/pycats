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
    MAX_JUMPS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_SIZE,
    INITIAL_LIVES,
    SHIELD_MAX_HP,
    BLAST_PADDING,
    RESPAWN_DELAY_FRAMES,
    STUN_TIME,
    DODGE_TIME,
    DODGE_SPEED,
    KNOCKBACK_LAUNCH_FACTOR,
    KNOCKBACK_DECAY,
)
from .attack import Attack
from .fighter_input import FighterInput
from .fighter_physics import step_physics
from ..combat.data import load_fighter_data
from ..combat.move_clock import MoveClock
from ..combat.knockback import knockback, hitstun_frames, decay_velocity
from ..systems.fsm import FSM, Transition
from ..systems.state_engine import make_state_engine


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
    KO = auto()  # knocked out, waiting to respawn
    HURT = auto()  # hit by an attack, unable to move or attack for a short time


class Player(pygame.sprite.Sprite):
    #### TODO: implement variable player sizes
    SIZE = PLAYER_SIZE

    def __init__(
        self, x, y, controls: dict, color, eye_color, char_name, facing_right=True,
        state_backend: str = "legacy", weight: int = 100,
    ):
        super().__init__()
        self.weight = weight  # fighter weight; feeds the knockback formula (#40)
        # Presentation is a render-time concern (#75): the body tint is computed
        # by render_battle.body_tint(self) from this player's state, so the entity
        # no longer owns a Surface. rect is the authoritative body box.
        self.char_color = color
        self.char_name = char_name
        self.rect = pygame.Rect(0, 0, self.SIZE[0], self.SIZE[1])
        self.rect.midbottom = (x, y)
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
        # attack_timer is now a derived property over self._clock (see below).
        self.invulnerable_timer = 0  # used for invulnerability mid-dodge, post-respawn, or while ledge grabbing
        self.jumps_remaining = MAX_JUMPS
        self.air_dodge_ok = True  # players can only air dodge once per combined sustained jump/fall status, until they land
        self.invulnerable = False  # used for dodging and invulnerability after being hit, respawned, or ledge grabbing
        self.done_attacking = (
            True  # used to determine when the player is done attacking
        )

        # ---------- data-driven move clock (Task 4 / #71) ----------
        # Load the fighter's data once. Phase 0: load_fighter_data returns the
        # same default for any character key, so passing char_name is fine.
        self.fighter_data = load_fighter_data(char_name)
        # MoveClock is the single source of truth for move progress. attack_timer
        # / current_move / move_frame are derived properties over it (#71); the
        # POST-increment frame convention is unchanged (first tick -> frame 1).
        self._clock = MoveClock()

        # Input → action translator (jump/dodge/shield/attack/move); #73.
        self._input = FighterInput(self)

        # shield visual helpers
        self.shield_attempting = False

        # Platform drop-through reference
        self.drop_platform = None

        # Edge-aware dodge state
        self.dodge_blocked_by_edge = False  # Track if current dodge is blocked by edge
        self.spot_dodge_shield_held = (
            False  # Track if shield was held during spot dodge
        )

        # Action-state engine (legacy FSM or statechart; legacy by default)
        self.engine = make_state_engine(self, state_backend)

        # Facing
        self.facing_right = facing_right
        self.original_facing_right = (
            facing_right  # Store original facing direction for respawn
        )

        # Tail (initialize after facing_right is set)
        from .tail import Tail

        self.tail = Tail(self)

    @property
    def state(self) -> str:
        """Current action-state label, via the active state engine."""
        return self.engine.state

    @property
    def defensive_status(self) -> str:
        """Defensive-status label, computed directly from the authoritative
        invulnerability flag (backend-agnostic; the statechart engine mirrors
        this same flag in its orthogonal defensive_status region)."""
        return "intangible" if self.invulnerable else "vulnerable"

    # ---- move-progress, delegated to MoveClock (#71) ----
    # These three are read by the legacy FSM, the statechart (fighter_chart),
    # and the runner snapshot; keeping the legacy names/values means no consumer
    # changes and parity stays byte-identical.
    @property
    def attack_timer(self) -> int:
        """Frames remaining in the current move (0 when idle)."""
        return self._clock.remaining

    @property
    def current_move(self):
        """The MoveData currently executing, or None when idle."""
        return self._clock.move

    @property
    def move_frame(self) -> int:
        """Frames elapsed since the current move started (POST-increment)."""
        return self._clock.frame

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
            # Phase 1 (#40): authentic Brawl/PM knockback + hitstun-from-knockback.
            self.percent += atk.damage
            kb = knockback(self.percent, atk.damage, self.weight,
                           atk.base_knockback, atk.knockback_growth)
            self.hurt_timer = hitstun_frames(kb)
            # (the red hurt-flash is now render-time: render_battle.body_tint #75)
            direction = (
                1 if atk.owner.facing_right else -1
            )  # the direction of the attack
            radians = math.radians(atk.angle)
            # Initial launch velocity (#44): KB * launch factor. It then bleeds
            # off via decay_velocity each hitstun frame in update() — Smash-style
            # ease-out rather than a constant slide (#43). Issue #8: COMBINE the
            # defender's existing horizontal momentum (`+=`) instead of
            # overwriting it; vertical stays an override (`=`) so a launch sets the
            # arc rather than adding to fall speed.
            launch = kb * KNOCKBACK_LAUNCH_FACTOR
            self.vel.x += launch * math.cos(radians) * direction
            self.vel.y = launch * -math.sin(radians)  # up = negative y

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
        if self.state == "shield":
            self.shield_hp = round(max(self.shield_hp - 0.2, 0), 2)
        else:
            self.shield_hp = round(min(self.shield_hp + 0.2, SHIELD_MAX_HP), 2)

        #
        if not self._pressed(held, "shield") and not self._pressed(pressed, "shield"):
            self.shield_attempting = False

        # input / movement / state logic --------------------------------------
        # Issue #8: hits are resolved AFTER this frame's engine.tick (game.py
        # runs process_hits after player.update), so hurt_timer/stun_timer are
        # set one frame before the FSM label flips to "hurt"/"stun". Gate input
        # on the timers too, not just the lagging state label, so the post-hit
        # frame does not run handle_move and clobber the knockback with walk
        # speed when a direction is held.
        in_hitstun = self.hurt_timer > 0 or self.stun_timer > 0
        dodge_initiated = False
        if not in_hitstun and self.state not in ("dodge", "hurt", "stun"):
            dodge_initiated = self.handle_actions(input_frame, attack_group)
            # Don't apply movement if a dodge was just initiated to prevent friction from reducing dodge velocity
            if not dodge_initiated:
                self.handle_move(held)
        elif in_hitstun:
            # #44: bleed off the launch velocity each hitstun frame (Smash-style
            # knockback decay) so a hit eases out instead of sliding at constant
            # speed (#43). handle_move/friction is skipped during hitstun, so this
            # is the only horizontal decel here; normal friction resumes once
            # hitstun ends. (Gravity still acts on vel.y below.)
            self.vel.x = decay_velocity(self.vel.x, KNOCKBACK_DECAY)

        # physics: gravity, edge-aware dodge clamping, movement, drop-through,
        # vertical/horizontal collision, and landing — see fighter_physics (#77).
        step_physics(self, platforms, held)

        # Non-shield timers tick
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.dodge_timer == 0 and self.state == "dodge":
            self.invulnerable = False  # reset invulnerability after dodge ends
            self.vel.x = 0  # stop horizontal movement after dodge ends

            # Handle spot dodge transition
            if self.spot_dodge_shield_held:
                # print(f"SPOT DODGE END: {self.char_name} ending spot dodge, shield_held={self._pressed(held, 'shield')}")
                if self._pressed(held, "shield"):
                    # Force shield attempting to true for smooth transition
                    self.shield_attempting = True
                    # print(f"SPOT DODGE TRANSITION: {self.char_name} shield_attempting set to True")
                self.spot_dodge_shield_held = False  # reset spot dodge flag

        # ---------- data-driven move clock (Task 4 / #71: MoveClock) ----------
        # Advance the move one frame and spawn its hitbox exactly once, when the
        # active window opens. The clock owns move_frame/current_move and clears
        # itself on completion (current_move -> None, attack_timer -> 0). Then
        # latch done_attacking when the move finishes while still in the attack
        # state — verbatim legacy semantics (attack_timer is now
        # self._clock.remaining), so both backends classify/exit on the same
        # frame. The active window is startup < move_frame <= startup + active;
        # the hitbox lives for `active` frames.
        tick = self._clock.tick()
        if tick.spawn is not None:
            # Task 5: pass the full Hitbox so Attack can resolve its circle.
            attack_group.add(
                Attack(self, hitbox=tick.spawn,
                       disappear_on_hit=False, lifetime=tick.lifetime)
            )
        if self.attack_timer == 0 and self.state == "attack":
            self.done_attacking = True

        # Update tail physics
        self.tail.update(platforms)

        # FSM state transitions -----------------------------------
        self.engine.tick(None)

    # ============================================================== helpers
    # Input handling lives in FighterInput (#73 / D1 slice 3); Player delegates
    # so update() and other callers are unchanged.
    def _pressed(self, key_set: set[int], name):
        """key_set is usually input_frame.held or .pressed."""
        return self._input._pressed(key_set, name)

    def handle_move(self, keys):
        return self._input.handle_move(keys)

    def handle_actions(self, input_frame, attack_group):
        return self._input.handle_actions(input_frame, attack_group)

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
        # Clamp at 0 (#54): enforce the lives>=0 invariant at the mutation site
        # rather than relying on callers (the is_alive / respawn gates) never
        # re-KOing a zero-life player.
        self.lives = max(0, self.lives - 1)
        self.is_alive = False
        self.respawn_timer = RESPAWN_DELAY_FRAMES
        # hide sprite off-screen
        self.rect.center = (-1000, -1000)
        self.vel.update(0, 0)
        self.engine.force("ko")

    def reset_to_spawn(self):
        """Authoritative per-life reset to a clean spawn state (#34).

        Both the per-life respawn (`_respawn`) and the new-match reset
        (`game.reset_game`) call this, so the two cannot silently drift. It
        resets only per-life/spawn state; it does NOT touch match-scoped fields
        (`lives`, the `attacks_made`/`hits_landed`/`suicides` stats) or force the
        FSM state — callers own those. Facing is derived from
        `original_facing_right`, not hardcoded, so it stays correct if a player
        is ever constructed facing a non-default direction (e.g. #16 skins).
        """
        self.is_alive = True
        self.rect.midbottom = self.spawn_point
        self.vel.update(0, 0)
        self.on_ground = False
        self.facing_right = self.original_facing_right
        self.jumps_remaining = MAX_JUMPS
        self.air_dodge_ok = True
        self.percent = 0
        self.shield_hp = SHIELD_MAX_HP
        self.shield_attempting = False
        self.was_hit_before_ko = False  # reset hit tracking for the next life
        # Transient hitstun / action timers + flags. _ko early-returns from
        # update(), so these never tick down during death; clearing them here is
        # what keeps a player KO'd mid-hurt/stun (#9) or mid-dodge/attack (#31)
        # from carrying that state into its next life (a frozen dodge_timer, a
        # leaked invulnerable=True, etc.).
        self.respawn_timer = 0
        self.dodge_timer = 0
        self.hurt_timer = 0
        self.stun_timer = 0
        self.invulnerable_timer = 0
        self.invulnerable = False
        self.spot_dodge_shield_held = False
        self.dodge_blocked_by_edge = False
        self._clock.reset()  # attack_timer/current_move/move_frame all derive from this
        self.done_attacking = True
        # (visual reset is render-time now: render_battle.body_tint #75)
        # Re-initialize the tail to its rest layout at the spawn point (#41): the
        # Verlet tail keeps live position/velocity and freezes wherever the cat
        # flew off-screen, so without this the chain whips in from there. facing
        # and rect are set above, so the layout is correct.
        self.tail.reset()

    def _respawn(self):
        #### TODO: implement temporary respawn invulnerability
        #### TODO: implement spawning animation
        #### TODO: implement respawn visible count-down
        self.reset_to_spawn()

    # state starters ----------------------------
    def _start_stun(self) -> None:
        # self.state = "stun"
        self.stun_timer = STUN_TIME
        self.vel.update(0, 0)

    def _start_dodge(self, dir_x: int) -> None:
        self.dodge_timer = DODGE_TIME
        self.invulnerable = True
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
                # Issue #2: a ground roll ends facing OPPOSITE to its travel
                # direction (Project M). Per SmashWiki (Roll), a forward roll
                # turns the character around and a back roll keeps facing — both
                # of which collapse to "face opposite the travel direction". So
                # roll left (dir_x < 0) -> face right; roll right -> face left.
                # (Air directional dodges are out of scope here — see air-dodge
                # research #23 — so only the grounded branch sets facing.)
                self.facing_right = dir_x < 0
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
