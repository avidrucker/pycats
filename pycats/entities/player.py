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
#### DONE: implement spot dodge where player can dodge in place without moving, and this
# does not move them below a thin ledge if they are holding shield and down
#### TODO: fix bug where consecutive quick hits will quickly cause the defender to be projected off the stage
#### TODO: fix bug where player stays red sometimes after being hit while moving or attacking
#### TODO: implement prone status where player is knocked down and cannot move or attack
# for a short time, and then can get up by pressing a button

#### LESS READY/LOW PRIORITY TODOS
#### TODO: make player shielding ineffective against grabs
#### TODO: implement grabs which are combo regular-attack + shield, and can be initiated
# from idle or shielding, and can be used against an opponent who is in idle, walking,
# running, or shielding state, and the grab will put the opponent into a grabbed state
# where they cannot move or attack, and the grabber can then throw them off the stage or
# do a follow-up attack
#### TODO: research and implement move/input buffering
#### TODO: implement fast fall by holding down which will cause the player to fall faster
#### DONE (#14 v1): ledge grab/hang/getup(up)/drop(down or away)/timeout + ledge
# intangibility; thin platforms are NOT grabbable (only solid edges). See update()
# ledge-grab + ledge-hang blocks. Deferred follow-ups (roll/attack/jump getups,
# intangibility decay, trump, 2-frame, tech): #267.

from enum import Enum, auto

import pygame  # type: ignore

from ..combat.charge import angle_smash_hitboxes, scale_hitboxes
from ..combat.data import GETUP_ATTACK, load_fighter_data
from ..config import (
    BLACK,
    FSMASH_ANGLE_DOWN,
    FSMASH_ANGLE_UP,
    KNOCKBACK_DECAY,
    KNOCKDOWN_PRONE_FRAMES,
    LEDGE_GETUP_FRAMES,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    P1_COLOR,
    P1_STRIPE_COLOR,
    P2_COLOR,
    PLAYER_SIZE,
    PROJECTILE_GRAVITY,
    PROJECTILE_MAX_BOUNCES,
    PROJECTILE_RESTITUTION,
)
from ..domain import PlayerIdentity, PlayerName, PlayerNumberSlot, PlayerTeamColor
from .attack import Attack, Projectile
from .fighter import Fighter
from .fighter_input import FighterInput
from .fighter_physics import step_physics
from .ledge import ledge_invuln_frames

# Angled f-smash (#327/4): map the captured direction to a launch angle.
_FSMASH_ANGLE = {"up": FSMASH_ANGLE_UP, "down": FSMASH_ANGLE_DOWN}
from ..combat.knockback import decay_velocity
from ..combat.move_clock import MoveClock
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
        self,
        x,
        y,
        controls: dict,
        color,
        eye_color,
        char_name,
        facing_right=True,
        fighter_data=None,
        character=None,
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
        self.fighter = Fighter(x, y, facing_right, self.fighter_data)

        # Presentation is a render-time concern (#75): the body tint is computed
        # by render_battle.body_tint(self) from this player's state, so the entity
        # no longer owns a Surface. rect (now Fighter-owned) is the body box.
        self.char_color = color
        # #672 Phase 1c: the P1/P2 seat splits into 3 independent seams — `number` is
        # the win-attribution identity (stats_print), `team_color` the HUD accent, and
        # `name` the label. Built from the legacy char_name arg (number = 1 iff "P1")
        # so every seat is byte-identical; `char_name` is now a read-only alias of
        # identity.name (retired in Phase 3).
        _number = 1 if char_name == "P1" else 2
        self.identity = PlayerIdentity(
            PlayerNumberSlot(_number),
            PlayerTeamColor.RED if _number == 1 else PlayerTeamColor.BLUE,
            PlayerName(char_name),
        )
        # #672 Phase 2a (DP2): the domain Character this seat is playing (from the
        # Selection the constructors build). Recorded in the golden snapshot so the
        # digest names the fighter. None when a Player is built without a Selection
        # (some unit tests); snapshot() falls back to "" then.
        self.character = character
        self.eye_color = eye_color
        # Optional display name (#478): shown above the fighter in place of the
        # "P1"/"P2" label when set. Separate from the identity seams; None → the label
        # falls back to identity.name (byte-identical default; the render-parity oracle
        # stays green). Set by the profile create/select UI (slice 2, #479).
        self.nickname = None

        # Secondary fur color for stripes
        if color == P1_COLOR:
            self.stripe_color = P1_STRIPE_COLOR
        elif color == P2_COLOR:
            self.stripe_color = BLACK
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
    def char_name(self) -> str:
        """The P1/P2 label — now a read-only alias of ``identity.name`` (#672 Phase 1c).

        Kept so residual readers (the render label + slot accent, still routed through
        the ``_CatShim`` render cache) keep working until a render slice repoints them
        to ``identity.name`` and this alias is deleted (Phase 3)."""
        return self.identity.name

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

    def _evict_from_ledge(self, occupant) -> None:
        """Knock a mistimed edge-hog occupant off the ledge (#311). Its intangibility
        burst has lapsed and an opponent grabbed the edge, so it loses the hang and
        drops into fall (regrab briefly locked out). The occupant's statechart routes
        ledge_hang -> fall on its next tick (grabbed_ledge is None while airborne)."""
        f = occupant.fighter
        f.invulnerable = False
        f.ledge_invuln_timer = 0
        f.ledge_getup_timer = 0
        f.ledge_regrab_lockout_timer = LEDGE_REGRAB_LOCKOUT_FRAMES
        f.grabbed_ledge = None
        f.vel.y = 1  # nudge airborne so the next frame falls
        # The occupant's ledge_hang state routes to `fall` on its next engine tick
        # (grabbed_ledge is None while airborne) — no force event needed.

    def force_prone(self, frames: int) -> None:
        """Force the fighter into the prone/knockdown state for `frames` getup
        frames (#13). Force-entry only for now (the landing-velocity trigger is
        #145); the only self-initiated action out of prone is standing up, which
        happens when prone_timer counts to 0. Drives the engine via the same
        force() seam as force_ko / force_idle."""
        self.fighter.prone_timer = max(0, int(frames))
        self.engine.force("prone")

    def reset_to_spawn(self) -> None:
        """Authoritative per-life reset (#34): the domain reset plus the
        Player-owned wiring the Fighter used to reach for (#286/S3) — the move
        clock and the Verlet tail. Used by the per-life respawn (update) and the
        new-match reset (battle_screen)."""
        self.fighter.reset_to_spawn()
        self._clock.reset()  # attack_timer/current_move/move_frame derive from this
        self.tail.reset()  # re-lay the tail at the spawn point (#41)

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

    @property
    def done_attacking(self) -> bool:
        """True when the current move has finished (the move clock has drained).

        Derived off `MoveClock` (#321/F3) — replaces the old hand-latched
        `Fighter.done_attacking` shim that was set False on move start and latched
        True on drain (`move_clock.py:8`). The statechart's attack-exit guards read
        this; it's only meaningful in the `attacking` state, where it equals the
        old flag exactly."""
        return self.attack_timer == 0

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
    def update(self, input_frame, platforms, attack_group, ledges=()):
        held = input_frame.held
        # note: currently unused, formerly called prev_keys
        #       pressed means freshly pressed this frame
        pressed = input_frame.pressed

        """Master per-frame update; handles KO/respawn before usual logic."""
        # ---------- dead / waiting to respawn ----------
        if not self.fighter.is_alive:
            self.fighter.tick_respawn()  # #293/S4b: aggregate owns the decrement
            if self.fighter.respawn_timer <= 0 and self.fighter.lives > 0:
                self.reset_to_spawn()  # #286: Player owns the clock/tail reset
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
            self.engine.force("ko")  # #298/S5: adapter applies the FSM transition
            return

        # ---------- shield tick ----------
        # Shield HP drains while shielding (breaking into `stun` if it empties,
        # #341) and regenerates otherwise — the domain owns both the drain rate
        # (SHIELD_DRAIN_PER_FRAME) and the drain-to-0 break rule (Fighter setter
        # clamps [0, MAX]).
        self.fighter.tick_shield(self.state == "shield")

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
        if (
            not in_hitstun
            and not in_shieldstun
            and not in_landing_lag
            and self.state not in ("dodge", "hurt", "stun", "prone", "getup_roll", "getup_attack", "ledge_hang")
        ):
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
            self.fighter.vel = apply_horizontal_friction(self.fighter.vel, self.fighter.on_ground)

        # ---------- ledge-hang driving (#14 + #311 edge-hog) ----------
        # While on the edge (hang or getup climb): pin position (skip gravity).
        #  - Hanging: tick the percent-scaled intangibility burst (#311). There is
        #    NO hang timeout (#475: PM has no hang timer) — the fighter hangs until
        #    it acts. Intangibility is `ledge_invuln_timer > 0` (a short burst), NOT
        #    the whole hang. Up = neutral getup, down/away = drop.
        #  - Getup climb (#311): a LEDGE_GETUP_FRAMES action-lock on the stage; the
        #    edge frees to others at the halfway frame (half-animation regrab), and
        #    the climb completes to idle when the window closes.
        if self.fighter.grabbed_ledge is not None:
            ledge = self.fighter.grabbed_ledge
            self.fighter.vel.x = 0
            self.fighter.vel.y = 0
            if self.fighter.ledge_getup_timer > 0:
                self.fighter.ledge_getup_timer -= 1
                if self.fighter.ledge_getup_timer <= LEDGE_GETUP_FRAMES // 2:
                    ledge.occupied_by = None  # edge re-grabbable mid-getup
                if self.fighter.ledge_getup_timer == 0:  # climb done -> on the stage
                    ledge.occupied_by = None
                    self.fighter.grabbed_ledge = None
            else:
                if self.fighter.ledge_invuln_timer > 0:
                    self.fighter.ledge_invuln_timer -= 1
                self.fighter.invulnerable = self.fighter.ledge_invuln_timer > 0
                up = self._pressed(held, "up")
                down = self._pressed(held, "down")
                away = ledge.away_held(self._pressed(held, "left"), self._pressed(held, "right"))
                if up:  # neutral getup -> climb window
                    self.rect.topleft = ledge.getup_topleft(self.rect.size)
                    self.fighter.invulnerable = False
                    self.fighter.ledge_invuln_timer = 0
                    self.fighter.ledge_getup_timer = LEDGE_GETUP_FRAMES
                elif down or away:  # drop (no timeout auto-release — #475)
                    self.fighter.invulnerable = False
                    self.fighter.ledge_invuln_timer = 0
                    self.fighter.ledge_regrab_lockout_timer = LEDGE_REGRAB_LOCKOUT_FRAMES
                    ledge.occupied_by = None
                    self.fighter.grabbed_ledge = None
                    self.fighter.vel.y = 1  # nudge so next frame is airborne

        # physics: gravity, edge-aware dodge clamping, movement, drop-through,
        # vertical/horizontal collision, and landing — see fighter_physics (#77).
        # Skipped while hanging — the fighter is pinned to the ledge.
        if self.fighter.grabbed_ledge is None:
            # step_physics returns True on a #145 auto-knockdown landing; the
            # adapter applies force_prone (the domain returns intent — #298/S5).
            if step_physics(self, platforms, held):
                self.force_prone(KNOCKDOWN_PRONE_FRAMES)

        # ---------- ledge grab (#14 + #311 edge-hog) ----------
        # After physics so on_ground/vel/pos are final. Grab when airborne +
        # descending + the body overlaps the catch box + not locked out. Edge-hog
        # timing (#311): an OCCUPIED edge is grabbable only once the occupant's
        # intangibility burst has lapsed (ledge_invuln_timer == 0) — grab too early
        # and the hog holds. A grab that lands on an occupied edge EVICTS the
        # occupant (mistimed hog loses the ledge; the incoming fighter takes it).
        if (
            self.fighter.grabbed_ledge is None
            and self.fighter.ledge_regrab_lockout_timer == 0
            and not self.fighter.on_ground
            and self.fighter.vel.y >= 0
        ):
            for ledge in ledges:
                occupant = ledge.occupied_by
                if occupant is not None and occupant.fighter.ledge_invuln_timer > 0:
                    continue  # hog denied: occupant still intangible
                if self.rect.colliderect(ledge.catch_rect()):
                    if occupant is not None and occupant is not self:
                        self._evict_from_ledge(occupant)  # mistimed hog -> evicted
                    self.rect.topleft = ledge.hang_topleft(self.rect.size)
                    self.fighter.vel.x = 0
                    self.fighter.vel.y = 0
                    granted = ledge_invuln_frames()
                    self.fighter.ledge_invuln_timer = granted
                    self.fighter.ledge_invuln_granted = granted  # #531: INVULN bar denominator
                    self.fighter.invulnerable = True
                    self.fighter.facing_right = ledge.facing_right()
                    self.fighter.grabbed_ledge = ledge
                    ledge.occupied_by = self
                    self.engine.force("ledge_grab")
                    break

        # Non-shield timers tick. Stateless ones (hurt/stun/landing_lag/
        # ledge_regrab_lockout/shieldstun) -> Fighter.tick_timers (#273/S1).
        # Coupled prone + dodge decrements -> Fighter.tick_action_timers (#289/S4),
        # which returns the names that hit 0 this frame. getup_roll/getup_attack
        # KEEP their inline decrement (they're set-and-ticked in the same frame by
        # the prone block below — moving them would drop that same-frame tick).
        # Placed at the top so landing_lag_timer is decremented before the dodge-end
        # read of it (`landing_lag_timer == 0`) further down.
        self.fighter.tick_timers()
        expired = self.fighter.tick_action_timers()
        if "prone_timer" in expired and self.fighter.on_ground:
            # Getup-roll (#146): the frame the prone window closes, a held
            # left/right rolls that way (intangible) instead of a neutral stand —
            # before engine.tick, so the chart routes prone -> getup_roll this frame.
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
                self.fighter.getup_attack_timer = GETUP_ATTACK.startup + GETUP_ATTACK.active + GETUP_ATTACK.recovery
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
        # (landing_lag / ledge_regrab_lockout / shieldstun via tick_timers #273;
        #  prone / dodge via tick_action_timers #289 — dodge-end reads the value)
        if self.fighter.dodge_timer == 0 and self.state == "dodge":
            self.fighter.invulnerable = False  # reset invulnerability after dodge ends
            # A waveland (#202) ends the dodge with a live slide — the landing-lag
            # window owns that momentum, so DON'T zero it here; a normal dodge end
            # still stops dead.
            if self.fighter.landing_lag_timer == 0:
                self.fighter.vel.x = 0  # stop horizontal movement after dodge ends

            # Handle spot dodge transition
            if self.fighter.spot_dodge_shield_held:
                # print(f"SPOT DODGE END: {self.char_name} ending spot dodge, shield_held={self._pressed(held, 'shield')}")  # noqa: E501
                if self._pressed(held, "shield"):
                    # Force shield attempting to true for smooth transition
                    self.fighter.shield_attempting = True
                    # print(f"SPOT DODGE TRANSITION: {self.char_name} shield_attempting set to True")
                self.fighter.spot_dodge_shield_held = False  # reset spot dodge flag

        # ---------- data-driven move clock (Task 4 / #71: MoveClock) ----------
        # Advance the move one frame and spawn its hitbox exactly once, when the
        # active window opens. The clock owns move_frame/current_move and clears
        # itself on completion (current_move -> None, attack_timer -> 0). The
        # attack-exit condition is now the derived `done_attacking` property
        # (attack_timer == 0) — #321/F3 removed the hand-latched flag. The active
        # window is startup < move_frame <= startup + active; the hitbox lives for
        # `active` frames.
        tick = self._clock.tick()
        if tick.spawn is not None:
            # #223: a projectile move (projectile_speed set) spawns a MOVING,
            # detached projectile — velocity in the facing direction, its own
            # lifetime, vanishing on hit. Normal moves keep the static hitbox.
            mv = self.current_move
            # Task 5 / #130: pass the move's full hitbox tuple so the hit-box resolves
            # every circle (multi-hitbox moves activate all boxes at once).
            if getattr(mv, "projectile_speed", None) is not None:
                # #223/#266: a projectile move spawns a MOVING, detached Projectile —
                # velocity in the facing direction, gravity + ground-bounce physics
                # (Mario-faithful, #263), its own lifetime, vanishing on hit. Physics
                # knobs are per-move overridable (getattr), else the Projectile defaults.
                facing = 1 if self.fighter.facing_right else -1
                attack_group.add(
                    Projectile(
                        self,
                        hitboxes=tick.spawn,
                        in_air=tick.in_air,
                        disappear_on_hit=True,
                        lifetime=mv.projectile_lifetime or tick.lifetime,
                        rehit_rate=mv.rehit_rate,
                        velocity=(facing * mv.projectile_speed, 0),
                        gravity=getattr(mv, "projectile_gravity", PROJECTILE_GRAVITY),
                        restitution=getattr(mv, "projectile_restitution", PROJECTILE_RESTITUTION),
                        max_bounces=getattr(mv, "projectile_max_bounces", PROJECTILE_MAX_BOUNCES),
                    )
                )
            else:
                # Smash charge (#327/3b): a chargeable move's hitboxes scale by the
                # captured charge fraction; c=0 (and non-chargeable moves) is an exact
                # identity, so the default cat's spawns are byte-identical (golden-safe).
                boxes = tick.spawn
                if getattr(mv, "chargeable", False):
                    boxes = scale_hitboxes(boxes, self.fighter.smash_charge_fraction)
                # Angled f-smash (#327/4): a forward smash aimed up/down replaces its
                # launch angle. Only set for an fsmash press, consumed here so it
                # never leaks onto a later move.
                if self.fighter.smash_angle_dir is not None:
                    boxes = angle_smash_hitboxes(boxes, _FSMASH_ANGLE[self.fighter.smash_angle_dir])
                    self.fighter.smash_angle_dir = None
                attack_group.add(
                    Attack(
                        self,
                        hitboxes=boxes,
                        in_air=tick.in_air,
                        disappear_on_hit=False,
                        lifetime=tick.lifetime,
                        rehit_rate=mv.rehit_rate,
                    )  # #213 looping; static hit-box
                )
        # (#321/F3: done_attacking is now a derived Player property — no latch.)

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
    # These rules live on Fighter (#83). update() reaches them via
    # `self.fighter._outside_blast_zone`/`self.fighter._ko`; the per-life respawn
    # now goes through `Player.reset_to_spawn` (#286, which calls
    # `fighter.reset_to_spawn` + resets the Player-owned clock/tail), and
    # fighter_input uses `_start_dodge`.

    # Stat counters live on the Fighter aggregate (#81); Player delegates so
    # callers (fighter_input, combat, the test stand-ins) are unchanged.
