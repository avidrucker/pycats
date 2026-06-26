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
from enum import Enum, auto
from ..config import (
    PLAYER_SIZE,
    KNOCKBACK_DECAY,
)
from .attack import Attack
from .fighter import Fighter
from .fighter_input import FighterInput
from .fighter_physics import step_physics
from ..combat.data import load_fighter_data
from ..combat.move_clock import MoveClock
from ..combat.knockback import decay_velocity
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
    SHIELD = auto()
    DODGE = auto()
    #### TODO: implement grabbed state
    #### TODO: implement grabbing state
    #### TODO: implement stunned state
    KO = auto()  # knocked out, waiting to respawn
    HURT = auto()  # hit by an attack, unable to move or attack for a short time


class Player(pygame.sprite.Sprite):
    SIZE = PLAYER_SIZE

    def __init__(
        self, x, y, controls: dict, color, eye_color, char_name, facing_right=True,
        state_backend: str = "legacy", weight: int = 100,
    ):
        super().__init__()

        # ---------- combat domain: the Fighter aggregate ----------
        # Sprite-free domain object that owns ALL of this fighter's simulation
        # state — kinematics, combat stats, timers, flags, facing, weight — and
        # the rules over them (#81/#83/#84/#87; design #69). Player is the thin
        # pygame Sprite adapter: it composes the Fighter, wires the subsystems
        # below, exposes delegating properties so readers are unchanged, and
        # orchestrates them in update(). Created first so those properties resolve
        # during the rest of __init__.
        self.fighter = Fighter(self, x, y, facing_right, weight)

        # Presentation is a render-time concern (#75): the body tint is computed
        # by render_battle.body_tint(self) from this player's state, so the entity
        # no longer owns a Surface. rect (now Fighter-owned) is the body box.
        self.char_color = color
        self.char_name = char_name
        self.eye_color = eye_color

        # Secondary fur color for stripes
        if color == (255, 160, 64):  # Orange player (P1_COLOR)
            self.stripe_color = (204, 102, 0)  # Dark orange
        elif color == (90, 90, 90):  # Gray player (P2_COLOR)
            self.stripe_color = (0, 0, 0)  # Black
        else:
            self.stripe_color = color  # Default to same color if no match

        # Input mapping
        self.controls = controls

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

        # Action-state engine (legacy FSM or statechart; legacy by default)
        self.engine = make_state_engine(self, state_backend)

        # Tail. facing_right/rect are Fighter-owned and set above, so the tail's
        # initial layout is correct.
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

    # ---- kinematics, delegated to Fighter (#84 / D1 slice 6b-3a) ----
    # rect/vel are pygame value types the renderer, physics, tail and collision
    # read as `player.rect`/`player.vel`; get+set so in-place mutation
    # (`p.rect.left = …`) AND wholesale assignment (`p.vel = Vector2(...)`, used
    # in __init__ and tests) both flow to the Fighter.
    @property
    def rect(self):
        return self.fighter.rect

    @rect.setter
    def rect(self, value):
        self.fighter.rect = value

    @property
    def vel(self):
        return self.fighter.vel

    @vel.setter
    def vel(self, value):
        self.fighter.vel = value

    @property
    def on_ground(self):
        return self.fighter.on_ground

    @on_ground.setter
    def on_ground(self, value):
        self.fighter.on_ground = value

    @property
    def spawn_point(self):
        return self.fighter.spawn_point

    @spawn_point.setter
    def spawn_point(self, value):
        self.fighter.spawn_point = value

    # ---- timers / flags / facing / weight, delegated to Fighter (#87 / 6b-3b) ----
    # Plain get+set pass-throughs (no invariants) so update(), fighter_physics,
    # fighter_input, tail, render_battle, game, the runner and the tests keep
    # reading/writing these as `player.<x>` unchanged. Player is now the thin
    # pygame Sprite adapter; the Fighter owns the state.

    @property
    def weight(self):
        return self.fighter.weight

    @weight.setter
    def weight(self, value):
        self.fighter.weight = value

    @property
    def is_alive(self):
        return self.fighter.is_alive

    @is_alive.setter
    def is_alive(self, value):
        self.fighter.is_alive = value

    @property
    def respawn_timer(self):
        return self.fighter.respawn_timer

    @respawn_timer.setter
    def respawn_timer(self, value):
        self.fighter.respawn_timer = value

    @property
    def dodge_timer(self):
        return self.fighter.dodge_timer

    @dodge_timer.setter
    def dodge_timer(self, value):
        self.fighter.dodge_timer = value

    @property
    def hurt_timer(self):
        return self.fighter.hurt_timer

    @hurt_timer.setter
    def hurt_timer(self, value):
        self.fighter.hurt_timer = value

    @property
    def stun_timer(self):
        return self.fighter.stun_timer

    @stun_timer.setter
    def stun_timer(self, value):
        self.fighter.stun_timer = value

    @property
    def invulnerable_timer(self):
        return self.fighter.invulnerable_timer

    @invulnerable_timer.setter
    def invulnerable_timer(self, value):
        self.fighter.invulnerable_timer = value

    @property
    def jumps_remaining(self):
        return self.fighter.jumps_remaining

    @jumps_remaining.setter
    def jumps_remaining(self, value):
        self.fighter.jumps_remaining = value

    @property
    def air_dodge_ok(self):
        return self.fighter.air_dodge_ok

    @air_dodge_ok.setter
    def air_dodge_ok(self, value):
        self.fighter.air_dodge_ok = value

    @property
    def invulnerable(self):
        return self.fighter.invulnerable

    @invulnerable.setter
    def invulnerable(self, value):
        self.fighter.invulnerable = value

    @property
    def done_attacking(self):
        return self.fighter.done_attacking

    @done_attacking.setter
    def done_attacking(self, value):
        self.fighter.done_attacking = value

    @property
    def shield_attempting(self):
        return self.fighter.shield_attempting

    @shield_attempting.setter
    def shield_attempting(self, value):
        self.fighter.shield_attempting = value

    @property
    def drop_platform(self):
        return self.fighter.drop_platform

    @drop_platform.setter
    def drop_platform(self, value):
        self.fighter.drop_platform = value

    @property
    def dodge_blocked_by_edge(self):
        return self.fighter.dodge_blocked_by_edge

    @dodge_blocked_by_edge.setter
    def dodge_blocked_by_edge(self, value):
        self.fighter.dodge_blocked_by_edge = value

    @property
    def spot_dodge_shield_held(self):
        return self.fighter.spot_dodge_shield_held

    @spot_dodge_shield_held.setter
    def spot_dodge_shield_held(self, value):
        self.fighter.spot_dodge_shield_held = value

    @property
    def facing_right(self):
        return self.fighter.facing_right

    @facing_right.setter
    def facing_right(self, value):
        self.fighter.facing_right = value

    @property
    def original_facing_right(self):
        return self.fighter.original_facing_right

    @original_facing_right.setter
    def original_facing_right(self, value):
        self.fighter.original_facing_right = value

    # ---- combat state + stats, delegated to Fighter (#81 / D1 slice 6b-1) ----
    # Thin pass-throughs so every existing reader/writer (render_battle, game.py,
    # stats_print, the runner snapshot, tests) is unchanged. The invariants on
    # percent/shield_hp/lives are enforced once, in Fighter's setters.
    @property
    def percent(self):
        return self.fighter.percent

    @percent.setter
    def percent(self, value):
        self.fighter.percent = value

    @property
    def shield_hp(self):
        return self.fighter.shield_hp

    @shield_hp.setter
    def shield_hp(self, value):
        self.fighter.shield_hp = value

    @property
    def lives(self):
        return self.fighter.lives

    @lives.setter
    def lives(self, value):
        self.fighter.lives = value

    @property
    def attacks_made(self):
        return self.fighter.attacks_made

    @attacks_made.setter
    def attacks_made(self, value):
        self.fighter.attacks_made = value

    @property
    def hits_landed(self):
        return self.fighter.hits_landed

    @hits_landed.setter
    def hits_landed(self, value):
        self.fighter.hits_landed = value

    @property
    def suicides(self):
        return self.fighter.suicides

    @suicides.setter
    def suicides(self, value):
        self.fighter.suicides = value

    @property
    def was_hit_before_ko(self):
        return self.fighter.was_hit_before_ko

    @was_hit_before_ko.setter
    def was_hit_before_ko(self, value):
        self.fighter.was_hit_before_ko = value

    @property
    def damage_given(self):
        return self.fighter.damage_given

    @damage_given.setter
    def damage_given(self, value):
        self.fighter.damage_given = value

    @property
    def damage_taken(self):
        return self.fighter.damage_taken

    @damage_taken.setter
    def damage_taken(self, value):
        self.fighter.damage_taken = value

    # Fighter rules live on the Fighter aggregate (#83 / D1 slice 6b-2); Player
    # delegates each with a thin pass-through so update(), fighter_physics,
    # fighter_input, combat, game, and the tests are unchanged. The simulation
    # state the rules mutate (rect/vel/timers/flags) is still Player's and the
    # rules reach it via Fighter.owner; it relocates in 6b-3.
    def receive_hit(self, atk):
        """Called by combat system when this player is struck."""
        return self.fighter.receive_hit(atk)

    def _handle_landing(self, was_airborne: bool):
        return self.fighter._handle_landing(was_airborne)

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
            self.shield_hp = round(self.shield_hp - 0.2, 2)  # Fighter setter clamps >= 0
        else:
            self.shield_hp = round(self.shield_hp + 0.2, 2)  # Fighter setter clamps <= MAX

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
    # These rules live on Fighter (#83); Player keeps thin delegators so update()
    # (`self._outside_blast_zone`/`self._ko`/`self._respawn`), game.reset_game
    # (`reset_to_spawn`), fighter_input (`_start_dodge`) and the tests are
    # unchanged.
    def _outside_blast_zone(self) -> bool:
        return self.fighter._outside_blast_zone()

    def _ko(self):
        return self.fighter._ko()

    def reset_to_spawn(self):
        return self.fighter.reset_to_spawn()

    def _respawn(self):
        return self.fighter._respawn()

    def _start_stun(self) -> None:
        return self.fighter._start_stun()

    def _start_dodge(self, dir_x: int) -> None:
        return self.fighter._start_dodge(dir_x)

    # Stat counters live on the Fighter aggregate (#81); Player delegates so
    # callers (fighter_input, combat, the test stand-ins) are unchanged.
    def record_attack_made(self):
        """Record that this player initiated an attack"""
        self.fighter.record_attack_made()

    def record_hit_landed(self):
        """Record that this player successfully hit an opponent"""
        self.fighter.record_hit_landed()

    def record_hit_received(self):
        """Record that this player was hit by an opponent"""
        self.fighter.record_hit_received()

    def record_damage_given(self, amount):
        """Record percent damage this player dealt to an opponent (#98)"""
        self.fighter.record_damage_given(amount)
