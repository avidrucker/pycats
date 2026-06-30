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
from ..combat.data import load_fighter_data, GETUP_ATTACK
from ..combat.move_clock import MoveClock
from ..combat.knockback import decay_velocity
from ..core.physics import apply_horizontal_friction
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
        fighter_data=None,
    ):
        super().__init__()

        # ---------- data-driven fighter definition (#71/#123/#126) ----------
        # Load the per-character FighterData first so the Fighter can take its
        # weight + movement constants from it. `fighter_data` may be injected
        # (tests / future archetype selection); otherwise it's loaded by key.
        # Phase 1: load_fighter_data branches per archetype ("nalio", …) and
        # returns the default cat for the "P1"/"P2" sim path.
        self.fighter_data = fighter_data or load_fighter_data(char_name)

        # ---------- combat domain: the Fighter aggregate ----------
        # Sprite-free domain object that owns ALL of this fighter's simulation
        # state — kinematics, combat stats, timers, flags, facing, weight — and
        # the rules over them (#81/#83/#84/#87; design #69). Player is the thin
        # pygame Sprite adapter: it composes the Fighter, wires the subsystems
        # below, exposes delegating properties so readers are unchanged, and
        # orchestrates them in update(). Created early so those properties resolve
        # during the rest of __init__.
        self.fighter = Fighter(self, x, y, facing_right, self.fighter_data)

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
        # fighter_data was loaded above (before the Fighter). MoveClock is the
        # single source of truth for move progress. attack_timer / current_move /
        # move_frame are derived properties over it (#71); the POST-increment
        # frame convention is unchanged (first tick -> frame 1).
        self._clock = MoveClock()

        # Input → action translator (jump/dodge/shield/attack/move); #73.
        self._input = FighterInput(self)

        # Action-state engine (statechart; the sole backend per ADR-0002).
        self.engine = make_state_engine(self)

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
        invulnerability flag (computed without the engine; the statechart engine
        mirrors this same flag in its orthogonal defensive_status region)."""
        return "intangible" if self.fighter.invulnerable else "vulnerable"

    def force_prone(self, frames: int) -> None:
        """Force the fighter into the prone/knockdown state for `frames` getup
        frames (#13). Force-entry only for now (the landing-velocity trigger is
        #145); the only self-initiated action out of prone is standing up, which
        happens when prone_timer counts to 0. Drives the engine via the same
        force() seam as force_ko / force_idle."""
        self.fighter.prone_timer = max(0, int(frames))
        self.engine.force("prone")

    # ---- move-progress, delegated to MoveClock (#71) ----
    # These three are read by the statechart (fighter_chart) and the runner
    # snapshot; keeping the historical names/values means no consumer changes and
    # the golden stays byte-identical.
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

    # rect is kept on Player (NOT collapsed in #90): pygame's Sprite machinery
    # reads `sprite.rect` directly, so it must stay a real attribute. get+set so
    # both in-place mutation (`p.rect.left = …`) and wholesale assignment flow
    # through to the Fighter, which owns it.
    @property
    def rect(self):
        return self.fighter.rect

    @rect.setter
    def rect(self, value):
        self.fighter.rect = value

    # #90: the ~30 thin get/set delegating properties + the receive_hit/_ko/
    # reset_to_spawn/_start_*/record_* method delegators that used to live here
    # are gone. All other fighter state and rules are reached explicitly via
    # `player.fighter.<x>`; Player is purely the pygame Sprite adapter and the
    # Fighter aggregate owns the simulation. (state/defensive_status/attack_timer/
    # current_move/move_frame above are computed from the Player-owned engine /
    # move clock, not from Fighter, so they stay.)

    # ============================================================== update
    def update(self, input_frame, platforms, attack_group):
        held = input_frame.held
        # note: currently unused, formerly called prev_keys
        #       pressed means freshly pressed this frame
        pressed = input_frame.pressed

        """Master per-frame update; handles KO/respawn before usual logic."""
        # ---------- dead / waiting to respawn ----------
        if not self.fighter.is_alive:
            self.fighter.respawn_timer -= 1
            if self.fighter.respawn_timer <= 0 and self.fighter.lives > 0:
                self.fighter._respawn()
            return  # nothing else while dead

        # ---------- hitlag / freeze frames (#138) ----------
        # On a clean hit both fighters freeze for hitlag_timer frames. Returning
        # early here holds everything — position (no step_physics), velocity (no
        # decay), the move clock, the hitstun timer, and the FSM — so the impact
        # pause precedes the knockback slide, which then resumes intact. Placed
        # after the dead check (a KO'd fighter is never frozen) and before the
        # blast-zone check (a frozen fighter can't drift out).
        if self.fighter.hitlag_timer > 0:
            self.fighter.hitlag_timer -= 1
            return

        # ---------- blast-zone KO check ----------
        if self.fighter._outside_blast_zone():
            self.fighter._ko()
            return

        # ---------- shield tick ----------
        # if shielding, then shield HP goes down, otherwise it goes up
        if self.state == "shield":
            self.fighter.shield_hp = round(self.fighter.shield_hp - 0.2, 2)  # Fighter setter clamps >= 0
        else:
            self.fighter.shield_hp = round(self.fighter.shield_hp + 0.2, 2)  # Fighter setter clamps <= MAX

        # Shieldstun (#140): a blocked hit locks the defender in shield for
        # shieldstun_timer frames — no drop, jump, dodge, grab, or move. Force
        # shield_attempting True (so the chart stays in "shield") and skip the
        # "shield released -> attempting False" reset below; the input gate and
        # the timer tick are handled further down. Runs only after any hitlag
        # freeze (the early-return above precedes this).
        in_shieldstun = self.fighter.shieldstun_timer > 0
        if in_shieldstun:
            self.fighter.shield_attempting = True
        elif not self._pressed(held, "shield") and not self._pressed(pressed, "shield"):
            self.fighter.shield_attempting = False

        # crouch intent (#124): hold down on solid ground, no shield (shield+down
        # is a spot dodge), for a cat that can crouch. Read raw held input (not
        # the shield_attempting flag, which is set later this frame) so the
        # shield/crouch split is order-independent. The state machine reacts to
        # this flag; _apply_posture_geometry resizes the body from the resulting
        # state label (so the geometry stays byte-identical to the golden).
        self.fighter.crouch_attempting = (
            self._pressed(held, "down")
            and not self._pressed(held, "shield")
            and self.fighter.on_ground
            and self.fighter.crouch_size is not None
        )

        # input / movement / state logic --------------------------------------
        # Issue #8: hits are resolved AFTER this frame's engine.tick (game.py
        # runs process_hits after player.update), so hurt_timer/stun_timer are
        # set one frame before the FSM label flips to "hurt"/"stun". Gate input
        # on the timers too, not just the lagging state label, so the post-hit
        # frame does not run handle_move and clobber the knockback with walk
        # speed when a direction is held.
        in_hitstun = self.fighter.hurt_timer > 0 or self.fighter.stun_timer > 0
        in_landing_lag = self.fighter.landing_lag_timer > 0  # waveland lock (#202)
        dodge_initiated = False
        if (not in_hitstun and not in_shieldstun and not in_landing_lag
                and self.state not in ("dodge", "hurt", "stun", "prone",
                                       "getup_roll", "getup_attack")):
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
            self.fighter.vel.x = decay_velocity(self.fighter.vel.x, KNOCKBACK_DECAY)
        elif in_landing_lag:
            # Waveland (#202): actions are locked, but the grounded slide keeps
            # bleeding off under ground friction (handle_move is skipped here, so
            # apply it directly — same job step_horizontal would do, minus walking).
            self.fighter.vel = apply_horizontal_friction(
                self.fighter.vel, self.fighter.on_ground)

        # physics: gravity, edge-aware dodge clamping, movement, drop-through,
        # vertical/horizontal collision, and landing — see fighter_physics (#77).
        step_physics(self, platforms, held)

        # Non-shield timers tick
        if self.fighter.hurt_timer > 0:
            self.fighter.hurt_timer -= 1
        if self.fighter.stun_timer > 0:
            self.fighter.stun_timer -= 1
        if self.fighter.prone_timer > 0:
            self.fighter.prone_timer -= 1  # getup window (#13)
            # Getup-roll (#146): the frame the window closes, a held left/right
            # rolls that way (intangible) instead of a neutral stand. Started here
            # — before engine.tick below — so the chart routes prone -> getup_roll
            # this same frame.
            if self.fighter.prone_timer == 0 and self.fighter.on_ground:
                dir_x = self._held_dir_x(input_frame)
                if dir_x != 0:
                    self.fighter.start_getup_roll(dir_x)
                elif self.controls["attack"] in input_frame.held:
                    # Getup-attack (#225): swing a wake-up attack instead of standing.
                    # Run the move clock directly so the hitbox spawns via the normal
                    # path below; the chart routes prone -> getup_attack this frame.
                    # getup_attack_timer mirrors the move duration and drives the
                    # state exit + intangibility (decremented below like getup_roll).
                    self._clock.start(GETUP_ATTACK)
                    self.fighter.getup_attack_timer = (
                        GETUP_ATTACK.startup + GETUP_ATTACK.active + GETUP_ATTACK.recovery
                    )
                    self.fighter.invulnerable = True  # getup intangibility (⚠ playtest:
                    # held for the whole swing for v1; tighten to startup+active later)
        if self.fighter.getup_roll_timer > 0:
            self.fighter.getup_roll_timer -= 1  # roll + intangibility window (#146)
            if self.fighter.getup_roll_timer == 0 and self.state == "getup_roll":
                self.fighter.invulnerable = False  # intangibility ends with the roll
        if self.fighter.getup_attack_timer > 0:
            self.fighter.getup_attack_timer -= 1  # wake-up attack duration (#225)
            if self.fighter.getup_attack_timer == 0 and self.state == "getup_attack":
                self.fighter.invulnerable = False  # intangibility ends with the swing
        if self.fighter.landing_lag_timer > 0:
            self.fighter.landing_lag_timer -= 1  # waveland lock window (#202)
        if self.fighter.shieldstun_timer > 0:
            self.fighter.shieldstun_timer -= 1
        if self.fighter.dodge_timer > 0:
            self.fighter.dodge_timer -= 1
        if self.fighter.dodge_timer == 0 and self.state == "dodge":
            self.fighter.invulnerable = False  # reset invulnerability after dodge ends
            # A waveland (#202) ends the dodge with a live slide — the landing-lag
            # window owns that momentum, so DON'T zero it here; a normal dodge end
            # still stops dead.
            if self.fighter.landing_lag_timer == 0:
                self.fighter.vel.x = 0  # stop horizontal movement after dodge ends

            # Handle spot dodge transition
            if self.fighter.spot_dodge_shield_held:
                # print(f"SPOT DODGE END: {self.char_name} ending spot dodge, shield_held={self._pressed(held, 'shield')}")
                if self._pressed(held, "shield"):
                    # Force shield attempting to true for smooth transition
                    self.fighter.shield_attempting = True
                    # print(f"SPOT DODGE TRANSITION: {self.char_name} shield_attempting set to True")
                self.fighter.spot_dodge_shield_held = False  # reset spot dodge flag

        # ---------- data-driven move clock (Task 4 / #71: MoveClock) ----------
        # Advance the move one frame and spawn its hitbox exactly once, when the
        # active window opens. The clock owns move_frame/current_move and clears
        # itself on completion (current_move -> None, attack_timer -> 0). Then
        # latch done_attacking when the move finishes while still in the attack
        # state — verbatim historical semantics (attack_timer is now
        # self._clock.remaining), so the move classifies/exits on the same frame
        # (golden-stable). The active window is startup < move_frame <= startup + active;
        # the hitbox lives for `active` frames.
        tick = self._clock.tick()
        if tick.spawn is not None:
            # Task 5 / #130: pass the move's full hitbox tuple so Attack resolves
            # every circle (multi-hitbox moves activate all boxes at once).
            attack_group.add(
                Attack(self, hitboxes=tick.spawn, in_air=tick.in_air,
                       disappear_on_hit=False, lifetime=tick.lifetime,
                       rehit_rate=self.current_move.rehit_rate)  # #213 looping
            )
        if self.attack_timer == 0 and self.state == "attack":
            self.fighter.done_attacking = True

        # Update tail physics
        self.tail.update(platforms)

        # FSM state transitions -----------------------------------
        self.engine.tick(None)

        # Posture body resize (#124 crouch / #173 prone): derived from the final
        # state label so the geometry stays byte-identical (golden-stable).
        self._apply_posture_geometry()

    def _apply_posture_geometry(self):
        """Resize the body Rect to match a lowered posture, feet planted.

        Crouching (#124) shrinks the box to the per-cat ``crouch_size``; prone
        (#173) shrinks it further to ``prone_size`` (a downed fighter lies flat);
        any other state restores ``stand_size``. Anchored at midbottom so the feet
        stay put, and a missing per-cat size for the active posture is a no-op (the
        box stays as-is). Keyed off ``self.state`` (not the input) so the resize
        follows the engine's computed label — preserving the golden."""
        f = self.fighter
        target = f.stand_size
        if self.state == "crouch" and f.crouch_size is not None:
            target = f.crouch_size
        elif self.state == "prone" and f.prone_size is not None:
            target = f.prone_size
        if (self.rect.width, self.rect.height) != tuple(target):
            midbottom = self.rect.midbottom
            self.rect.size = target
            self.rect.midbottom = midbottom

    # ============================================================== helpers
    # Input handling lives in FighterInput (#73 / D1 slice 3); Player delegates
    # so update() and other callers are unchanged.
    def _pressed(self, key_set: set[int], name):
        """key_set is usually input_frame.held or .pressed."""
        return self._input._pressed(key_set, name)

    def handle_move(self, keys):
        return self._input.handle_move(keys)

    def _held_dir_x(self, input_frame):
        """+1 if right is held, -1 if left is held, 0 if neither/both (#146 getup)."""
        right = self.controls["right"] in input_frame.held
        left = self.controls["left"] in input_frame.held
        return (1 if right else 0) - (1 if left else 0)

    def handle_actions(self, input_frame, attack_group):
        return self._input.handle_actions(input_frame, attack_group)

    # ============================================================= KO / respawn
    # These rules live on Fighter (#83); Player keeps thin delegators so update()
    # (`self.fighter._outside_blast_zone`/`self.fighter._ko`/`self.fighter._respawn`), game.reset_game
    # (`reset_to_spawn`), fighter_input (`_start_dodge`) and the tests are
    # unchanged.


    # Stat counters live on the Fighter aggregate (#81); Player delegates so
    # callers (fighter_input, combat, the test stand-ins) are unchanged.


