"""Deterministic input controllers for headless battles.

These are NOT in-game AI — they are scripted, RNG-free policies used to drive
demo/benchmark battles and to *generate* fixed input timelines. Capture a
controller's `emitted` frames and replay that list to keep golden tests a clean
byte-identical comparison on identical inputs.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..core.input import InputFrame
from ..combat.geometry import move_reach

# #338: states a fighter can start a ground roll/dodge from — mirrors
# fighter_input.can_dodge_state. The evade only emits a roll when the bot is in one,
# so the combo actually executes instead of being wasted mid-walk/attack.
_DODGEABLE_STATES = frozenset({"idle", "jump", "fall", "shield", "crouch"})

# #369: frames the jump-toward-elevated-target may stay HELD while grounded before
# the pulse kicks in. Chosen well above any normal jump-up (which leaves the ground
# in 1 frame) or brief blip, so ordinary + seeded battles are byte-identical; only a
# genuine stuck standoff (hundreds of grounded-hold frames, #367) exceeds it.
JUMP_UP_STUCK_MAX = 90

# #368: narrow anti-stall backstop (defence-in-depth, per the #376 verdict). Fires ONLY
# on a genuine no-progress lock — a leveled bot stuck within ANTI_STALL_MOVE_PX of a
# reference with NO hit landing either way and a reachable target, sustained
# ANTI_STALL_MAX frames — then injects one toward-target action. NOT a blanket idle
# timer: a legitimately-spacing bot micro-adjusts or lands cadence hits well inside 1.5s,
# so it never trips (that would kill Smash-faithful spacing/baiting, #343). Reuses #369's
# 90-frame scale; state is deliberately NOT keyed on (a lock can oscillate idle↔fall).
ANTI_STALL_MAX = 90
ANTI_STALL_MOVE_PX = 8


# ---------------------------------------------------------------------------
# CPU difficulty levels (#232, #231 / #148 step 1) — DETERMINISTIC core only.
# The seeded-RNG knobs (follow_through_p, shield_chance) are a later child.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LevelParams:
    """Deterministic AI knobs for one difficulty level."""
    reaction_delay: int   # frames in-range before the first attack fires
    attack_period: int    # frames between attacks (cadence)
    standoff: int         # desired horizontal gap (px)
    # Seeded-RNG knobs (#238 / #148 step 2), rolled against self.rng (#166):
    follow_through_p: float = 1.0   # P(commit a chosen attack); 1.0 = always
    shield_chance: float = 0.0      # P(raise shield this frame); 0.0 = never
    # #254/#251 Q2: shield REACTIVELY (only when a threat is detected incoming) vs
    # randomly. High levels shield reactively (SmashWiki: "almost always defend from
    # attacks"); low levels shield "at random times" (the #238 unconditional roll).
    # When True, shield_chance is reused as the *reliability* of a reactive shield.
    reactive_shield: bool = False
    # #274/#251: whiff-punish — when the opponent is in the RECOVERY phase of a move
    # (committed/whiffed) in range, attack immediately (bypass the cadence gate) to
    # punish the opening. High levels punish (paired with reactive_shield); low levels
    # don't. Off = the pre-#274 cadence-only attack.
    whiff_punish: bool = False
    # Capability gate (#248 / #148 step 3). Only "specials" is wired today (the bot
    # presses B → fireball); tilts/aerials emerge from the move-select seam when the
    # bot attacks while moving/airborne, and smash/grab don't exist in pycats yet —
    # they ride here as data for future gating.
    enabled_moves: frozenset = frozenset({"jab", "tilts", "aerials"})
    # #335 (DEV-A of #285): derive the melee range from the reach of the move the bot
    # actually commits (per-character/per-move) instead of the flat `attack_range=45`.
    # On for the reactive levels (5/7/9), off for low/default → golden-safe.
    reach_aware: bool = False
    # #277 (model A, re-spec per #343): press the advantage on a vulnerable opponent —
    # when the opponent is in move recovery (no threat) and the bot is in melee range,
    # suppress the standoff back-off so it holds/presses instead of retreating. On for
    # the reactive levels (5/7/9), off for low/default → golden-safe. NOT footsies:
    # `standoff` is never widened (Smash CPUs approach committally, #343).
    reactive_spacing: bool = False
    # #338 (re-scoped per #343): reactive ROLL-AWAY — on a detected threat, roll away
    # (a `shield`+away combo) instead of shielding, as a seeded alternative. Rolled
    # BEFORE the shield and mutually exclusive with it. A higher-skill option: off
    # at/below Lv5 (keeps those tests byte-identical), graded up at 7/9. Default 0.0
    # → level-less/low never roll (golden-safe). ⚠ values are tuning starting points.
    evade_chance: float = 0.0


# Anchor rows for Lv 1/3/5/7/9 (#148 Q5). ⚠ The *axes* are sourced; the *numbers*
# are pycats interpolations — tuning starting points, not measured PM data.
LEVEL_PARAMS: dict[int, LevelParams] = {
    1: LevelParams(reaction_delay=30, attack_period=48, standoff=45, follow_through_p=0.15, shield_chance=0.00, reactive_shield=False, whiff_punish=False, enabled_moves=frozenset({"jab"})),
    3: LevelParams(reaction_delay=20, attack_period=36, standoff=40, follow_through_p=0.35, shield_chance=0.05, reactive_shield=False, whiff_punish=False, enabled_moves=frozenset({"jab", "tilts"})),
    5: LevelParams(reaction_delay=12, attack_period=24, standoff=35, follow_through_p=0.55, shield_chance=0.15, reactive_shield=True,  whiff_punish=True,  enabled_moves=frozenset({"jab", "tilts", "aerials"}), reach_aware=True, reactive_spacing=True),
    7: LevelParams(reaction_delay=6,  attack_period=16, standoff=32, follow_through_p=0.80, shield_chance=0.40, reactive_shield=True,  whiff_punish=True,  enabled_moves=frozenset({"jab", "tilts", "aerials"}), reach_aware=True, reactive_spacing=True, evade_chance=0.15),
    9: LevelParams(reaction_delay=1,  attack_period=10, standoff=30, follow_through_p=1.00, shield_chance=0.85, reactive_shield=True,  whiff_punish=True,  enabled_moves=frozenset({"jab", "tilts", "aerials", "specials"}), reach_aware=True, reactive_spacing=True, evade_chance=0.30),
}


def level_params(level: int) -> LevelParams:
    """Knobs for `level` (1-9). Intermediate levels reuse the nearest filled anchor;
    a tie (even levels are equidistant between odd anchors) resolves to the HIGHER
    anchor. Out-of-range clamps to the nearest end."""
    anchors = sorted(LEVEL_PARAMS)
    nearest = min(anchors, key=lambda a: (abs(a - level), -a))
    return LEVEL_PARAMS[nearest]


DEFAULT_CONTROLLER_SEED = 0

# #166: the default controller seed. rng=None resolves to random.Random(this) so
# every sim/golden/parity run is reproducible by construction; live variation is
# strictly opt-in (watch.py injects a clocktime/`--seed` Random instead).
DEFAULT_CONTROLLER_SEED = 0


class BaseController:
    """Scaffolding shared by all deterministic archetype controllers.

    Owns the per-frame bookkeeping every archetype needs: resolving
    `(attacker, target)` from `attacker_num`, edge detection (`pressed`/
    `released` from the previous frame's `held`), capturing each `InputFrame`
    into `emitted` (for freezing a fixed input list), and the integer frame
    counter `_f`. Subclasses supply the policy via `decide(a, t, frame) -> set`
    returning the keys to *hold* this frame.

    `attacker_num` is 1 or 2; player refs are resolved per-frame from the
    (p1, p2) passed to `__call__`, so a controller can be built before
    `run_battle` creates the players.
    """

    def __init__(self, attacker_num=1, rng=None):
        self.attacker_num = attacker_num
        self._prev = set()
        self._f = 0
        self.emitted = []  # recorded InputFrames, for freezing into a fixed list
        # #166: injected seeded PRNG. Default is a FIXED seed so sims/goldens/
        # parity stay reproducible; live callers inject a clocktime-seeded Random.
        # The RNG lives ONLY at the controller edge — it can influence the chosen
        # InputFrame but never reaches the (input-only) FSM backends.
        self.rng = rng if rng is not None else random.Random(DEFAULT_CONTROLLER_SEED)

    def decide(self, a, t, frame, attacks=None) -> set:
        """Return the set of keys to HOLD this frame. `a` is this controller's
        player, `t` the other. `attacks` (#254) is the live `Attack` sprite group
        (opponent hitboxes + projectiles) for threat-aware policies; None when the
        caller supplies no battle context (default → unchanged, golden-safe).
        Override in an archetype."""
        raise NotImplementedError

    def __call__(self, p1, p2, frame, attacks=None):
        a, t = (p1, p2) if self.attacker_num == 1 else (p2, p1)
        held = self.decide(a, t, frame, attacks)
        pressed = held - self._prev
        released = self._prev - held
        self._prev = held
        self._f += 1
        fi = InputFrame(held=set(held), pressed=set(pressed), released=set(released))
        self.emitted.append(fi)
        return fi


class AttackerController(BaseController):
    """Drives `attacker` to hunt down `target` and attack; `target` gets no input.

    Deterministic: decisions depend only on live positions (no randomness), so a
    given backend produces the same battle every run. Movement keys are held;
    jump/attack are pulsed (one frame) so the game sees fresh key presses.
    """

    def __init__(self, attacker_num=1, attack_period=12, standoff=30,
                 attack_range=45, safe_x=(110, 850), drop_threshold=20, rng=None,
                 reaction_delay=0, level=None,
                 follow_through_p=1.0, shield_chance=0.0,
                 reactive_shield=False, whiff_punish=False,
                 shield_threat_range=160, shield_threat_dy=80,
                 enabled_moves=frozenset({"jab", "tilts", "aerials"}),
                 fireball_range=450, reach_aware=False, reactive_spacing=False,
                 evade_chance=0.0):
        super().__init__(attacker_num, rng=rng)
        # #232/#238/#248: a difficulty `level` (1-9) overrides the knobs from the
        # #148 table; level=None keeps the explicit defaults (golden-safe).
        if level is not None:
            lp = level_params(level)
            attack_period = lp.attack_period
            standoff = lp.standoff
            reaction_delay = lp.reaction_delay
            follow_through_p = lp.follow_through_p
            shield_chance = lp.shield_chance
            reactive_shield = lp.reactive_shield
            whiff_punish = lp.whiff_punish
            enabled_moves = lp.enabled_moves
            reach_aware = lp.reach_aware
            reactive_spacing = lp.reactive_spacing
            evade_chance = lp.evade_chance
        # #248: capability gate + ranged-special (fireball) poke distance. Default
        # excludes "specials" → the ranged-special branch never fires (golden-safe).
        self.enabled_moves = enabled_moves
        self.fireball_range = fireball_range  # ⚠ GUESS px (ranged-poke band)
        # #238: seeded-RNG knobs (rolled against self.rng, #166). Defaults keep the
        # pre-#238 behaviour AND never touch the rng stream (always commit; never shield).
        self.follow_through_p = follow_through_p
        self.shield_chance = shield_chance
        # #254: reactive (threat-gated) shielding. False = the #238 unconditional
        # random roll (low-level flavour / golden-safe default). When True, the bot
        # only shields when an opponent hitbox/projectile is detected incoming within
        # `shield_threat_range` px (and `shield_threat_dy` px vertically), after the
        # `reaction_delay` window; shield_chance is then the per-frame *reliability*.
        self.reactive_shield = reactive_shield
        # #274: punish a committed/whiffed move during its recovery (off = cadence-only).
        self.whiff_punish = whiff_punish
        self.shield_threat_range = shield_threat_range  # ⚠ GUESS px (~2 char-lengths, #251)
        self.shield_threat_dy = shield_threat_dy        # ⚠ GUESS px (vertical threat band)
        self._threat_since = None  # frame a threat first appeared (reaction-window tracker)
        self.level = level
        # reaction_delay (#232): frames the target must stay in range before the
        # FIRST attack fires. 0 = react instantly (the pre-#232 behaviour).
        self.reaction_delay = reaction_delay
        self._in_range_since = None
        # safe_x is the range the attacker will walk to — the thick platform's
        # standing extent (x[80..880]) minus a body-margin. Widened from the old
        # 770 for #44: realistic knockback decay no longer launches the target
        # off-stage in one hit, so it can linger near the platform edges; the bot
        # must be able to follow it there to keep racking up damage to a KO.
        self.attack_period = attack_period
        self.standoff = standoff          # desired horizontal gap (stand beside, not on top of)
        self.attack_range = attack_range
        # #335 (DEV-A of #285): when on, the melee-range gates derive from the reach
        # of the move the bot actually commits, per character, instead of this flat
        # constant. Default off → `_melee_range` returns `attack_range` unchanged.
        self.reach_aware = reach_aware
        # #277 (model A): suppress the standoff back-off when the opponent is vulnerable.
        self.reactive_spacing = reactive_spacing
        # #338: seeded reactive roll-away (evade). Default 0.0 → never rolls (golden-safe).
        self.evade_chance = evade_chance
        self.safe_x = safe_x
        # Task 5 retune: drop_threshold — if attacker is grounded and target is
        # this many pixels *below* (positive dy), hold 'down' to drop through any
        # thin platform the attacker is standing on so they reach the target's
        # level.  Purely a policy parameter; 0 disables the behaviour.
        self.drop_threshold = drop_threshold
        self._last_attack = -10_000
        # #369: consecutive frames the jump-toward-elevated-target gate has held while
        # the bot is STILL grounded (the jump never took). A normal jump leaves the
        # ground on frame 1 → gate's on_ground goes False → this resets, so normal
        # jumps and brief blips are byte-identical (goldens/seeded battles safe). Only
        # a PROLONGED grounded-hold (the standoff limit cycle, #367) trips the pulse.
        self._jump_up_stuck = 0
        # #368: no-progress detector state. `_noprog_ref` = (centre_x, centre_y, own %,
        # target %) reference; `_noprog` = consecutive frames within ANTI_STALL_MOVE_PX
        # of it with no percent change (a lock). Only the leveled path arms it.
        self._noprog = 0
        self._noprog_ref = None

    def _in_threat_band(self, a, ox, oy) -> bool:
        """Is point (ox, oy) within the shield threat band around the bot `a`?"""
        return (abs(ox - a.rect.centerx) <= self.shield_threat_range
                and abs(oy - a.rect.centery) <= self.shield_threat_dy)

    def _threat_incoming(self, a, t, attacks) -> bool:
        """#254: is `t` threatening `a` right now? Two signals (#251 decision model):

        1. **Melee windup** — `t` is executing an attack move within the threat band.
           We react to the *windup* (not the active hitbox sprite), because an already-
           live hitbox lands before a shield can rise — too late to be reactive.
        2. **Projectile/active hitbox** — an opponent-owned `Attack` sprite in the band;
           a *moving* projectile must also be *closing* (heading toward the bot).

        Pure function of the frame snapshot → deterministic, replay/golden-safe."""
        # (1) opponent winding up a move nearby (gives lead time to shield). #274:
        # only startup/active is a THREAT — a move in recovery is a whiff-punish
        # opportunity (see _whiff_open), not something to shield.
        mv = getattr(t, "current_move", None)
        if mv is not None and t.fighter.is_alive and t.move_frame <= mv.startup + mv.active:
            if self._in_threat_band(a, t.rect.centerx, t.rect.centery):
                return True
        # (2) opponent-owned hitbox/projectile in flight.
        for atk in (attacks or ()):
            if getattr(atk, "owner", None) is not t or not getattr(atk, "active", True):
                continue
            if not self._in_threat_band(a, atk.rect.centerx, atk.rect.centery):
                continue
            vel = getattr(atk, "velocity", None)
            if vel is not None:
                vx = vel[0]
                dx = atk.rect.centerx - a.rect.centerx
                # closing = moving toward the bot (opposite sign to its offset); a
                # stationary projectile already in-band counts as incoming.
                if vx != 0 and dx * vx >= 0:
                    continue
            return True
        return False

    def _committed_move_key(self) -> str:
        """The ground move this bot actually throws (#335). Mirrors the #292 rule:
        a leveled, tilt-enabled bot commits the forward-tilt; everything else jabs.
        So the derived reach tracks the move that will actually land."""
        if self.level is not None and "tilts" in self.enabled_moves:
            return "ftilt"
        return "jab"

    def _melee_range(self, a) -> float:
        """The center-to-center gap within which the bot will commit its attack.

        #335 (DEV-A of #285): when `reach_aware`, derive it from the real reach of
        the move the bot commits (`_committed_move_key`) on *this* character, so a
        long-reach cat (Narz f-tilt 64) presses from farther than a short one and the
        bot stops using one flat number for every fighter/move. Falls back to the
        fixed `attack_range` when off, or when the character lacks that move (e.g. the
        default cat) — keeping the level-less default byte-identical (golden-safe)."""
        if not self.reach_aware:
            return self.attack_range
        # Tolerate a minimal combat stand-in with no `fighter_data` (the #283-style
        # stub): fall back to the fixed range rather than reaching into absent data.
        fd = getattr(a, "fighter_data", None)
        if fd is None:
            return self.attack_range
        reach = move_reach(fd, self._committed_move_key(), a.rect.width)
        return self.attack_range if reach is None else reach

    def _whiff_open(self, a, t) -> bool:
        """#274: is the opponent `t` in the RECOVERY phase of a move and within melee
        range of `a`? Recovery = move_frame past startup+active while the move is still
        live (the clock clears the move at frame >= total). A punishable opening."""
        mv = getattr(t, "current_move", None)
        if mv is None or not t.fighter.is_alive:
            return False
        if t.move_frame <= mv.startup + mv.active:
            return False  # still startup/active (a threat, not an opening)
        adx = abs(t.rect.centerx - a.rect.centerx)
        dy = abs(t.rect.centery - a.rect.centery)
        return adx <= self._melee_range(a) and dy < 60

    def decide(self, a, t, frame, attacks=None) -> set:
        keys = a.controls
        held = set()

        # Ledge recovery (#291): a hanging fighter only escapes by pressing up (the
        # neutral getup, #14) — otherwise it hangs to a timeout/drop KO. Skilled bots
        # (level >= 5) recover; low levels and the default (level=None) fall through
        # unchanged, so the baseline / golden-safe controller is untouched.
        if (getattr(a.fighter, "grabbed_ledge", None) is not None
                and self.level is not None and self.level >= 5):
            return {keys["up"]}

        if t.fighter.is_alive:
            dx = t.rect.centerx - a.rect.centerx
            dy = t.rect.centery - a.rect.centery
            adx = abs(dx)
            cx = a.rect.centerx
            # #248 (thread 3): ranged fireball poke (B), for a specials-enabled level.
            # Checked BEFORE the shield roll so a specials bot zones/pokes rather than
            # shielding it away; it still falls through to movement on non-poke frames,
            # so it also closes in. Cadence + follow-through gated. Default enabled_moves
            # has no "specials" → never fires (golden-safe).
            if ("specials" in self.enabled_moves and abs(dy) < 60
                    and self.attack_range < adx <= self.fireball_range
                    and (self._f - self._last_attack) >= self.attack_period
                    and (self.follow_through_p >= 1.0
                         or self.rng.random() < self.follow_through_p)):
                self._last_attack = self._f
                return {keys["special"]}
            # Shield (defensive frame — no move/attack). Two regimes (#254/#251 Q2):
            if self.reactive_shield:
                # High level: shield REACTIVELY — only when an opponent hitbox/
                # projectile is detected incoming, after the reaction window, with
                # shield_chance as the reliability. Never shields in open space (the
                # user's complaint). Default level-less path has reactive_shield=False
                # so this branch never runs (golden-safe; rng untouched).
                if self._threat_incoming(a, t, attacks):
                    if self._threat_since is None:
                        self._threat_since = self._f
                    reacted = (self._f - self._threat_since) >= self.reaction_delay
                    if reacted:
                        # #338: reactive ROLL-AWAY — rolled BEFORE the shield and
                        # mutually exclusive with it. A ground roll is a `shield`+away
                        # combo (fighter_input Priority-1/3 → _start_dodge(±1, 0)); away
                        # is the key pointing away from the opponent. Only emitted when
                        # the bot is in a DODGE-ABLE state (matches fighter_input's
                        # `can_dodge_state`), so the roll actually executes rather than
                        # being a wasted input mid-walk/attack — the reactive shield
                        # naturally enters `shield` state on a threat, then this rolls.
                        # evade_chance 0.0 short-circuits the rng, so a non-evading
                        # level's shield stream is byte-identical (golden-safe).
                        dodge_able = getattr(a, "state", None) in _DODGEABLE_STATES
                        if (dodge_able and self.evade_chance > 0.0
                                and self.rng.random() < self.evade_chance):
                            away = keys["left"] if dx > 0 else keys["right"]
                            return {keys["shield"], away}
                        if (self.shield_chance > 0.0
                                and self.rng.random() < self.shield_chance):
                            return {keys["shield"]}
                else:
                    self._threat_since = None
            # #238: low-level stochastic shield (seeded, #166) — "shields at random
            # times." Default shield_chance 0.0 → no roll, no change (golden-safe).
            elif self.shield_chance > 0.0 and self.rng.random() < self.shield_chance:
                return {keys["shield"]}
            # #274: whiff-punish — the opponent committed a laggy move and is now in
            # its RECOVERY phase, in range → strike the opening IMMEDIATELY, bypassing
            # the attack_period cadence gate, gated by follow-through reliability.
            # Default whiff_punish=False → never runs (golden-safe; rng untouched).
            if self.whiff_punish and self._whiff_open(a, t):
                if (self.follow_through_p >= 1.0
                        or self.rng.random() < self.follow_through_p):
                    self._last_attack = self._f
                    return {keys["attack"]}
            lo, hi = self.safe_x
            toward = keys["right"] if dx > 0 else keys["left"]
            away = keys["left"] if dx > 0 else keys["right"]
            # Maintain a standoff gap: close in if too far, back off if stacked
            # on top of the target (adx ~ 0 would otherwise deadlock).
            # #277 (model A): press the advantage — when `reactive_spacing` and the
            # opponent is in move recovery (vulnerable, no incoming threat) and the bot
            # is within melee range (`_whiff_open`), SUPPRESS the back-off so it holds/
            # presses instead of retreating from a punishable opponent. NOT footsies —
            # `standoff` is never widened (Smash CPUs approach committally, #343).
            # Gated on `reactive_spacing`, so the level-less default never evaluates the
            # helpers and is byte-identical (golden-safe); deterministic (no rng).
            press_in = (self.reactive_spacing and self._whiff_open(a, t)
                        and not self._threat_incoming(a, t, attacks))
            move = None
            if adx > self.standoff + 8:
                move = toward
            elif adx < self.standoff - 8 and not press_in:
                move = away
            # Clamp: allow moving back toward centre from outside, but never
            # press further past a blast-zone-side bound.
            if move == keys["right"] and cx >= hi:
                move = None
            elif move == keys["left"] and cx <= lo:
                move = None
            if move is not None:
                held.add(move)
            # Jump toward an elevated target, but only when roughly underneath it
            # (else jumping straight up never reaches the platform -> bounce loop).
            # The horizontal window is wide enough to chase a target knocked onto
            # a neighbouring platform (Task 4's data-driven attack times can leave
            # the target on a different level after knockback).
            # PULSED when stuck (#369, mechanism #367): the jump fires on a fresh
            # press edge (`pressed = held - prev`), so HOLDING `up` every frame gives
            # exactly ONE press -> one jump -> then the bot sits idle holding `up`
            # forever (a stable standoff limit cycle). A NORMAL jump-up leaves the
            # ground immediately, so `on_ground` goes False and `up` releases on its
            # own — those are unchanged. Only when the bot held `up` last frame yet is
            # STILL grounded (the jump didn't take) do we skip this frame, forcing a
            # release so a fresh press re-fires the jump next frame and the bot climbs.
            if dy < -30 and a.fighter.on_ground and adx < 120:
                self._jump_up_stuck += 1
                # Held for the first JUMP_UP_STUCK_MAX frames (byte-identical to the
                # old always-hold, so normal jumps + short blips are unchanged); once
                # the bot has been grounded-and-wanting-up that long it is genuinely
                # stuck, so release on odd counts -> a fresh press re-fires the jump.
                if self._jump_up_stuck <= JUMP_UP_STUCK_MAX or self._jump_up_stuck % 2 == 0:
                    held.add(keys["up"])
            else:
                self._jump_up_stuck = 0
            # Drop through thin platforms when target is below.  Pressing 'down'
            # while grounded on a thin platform causes solve_vertical to let the
            # player fall through it, putting them on the same y-level as the
            # target.  Only activate when dy exceeds the policy threshold so the
            # bot doesn't perpetually fall through the main platform.
            if self.drop_threshold > 0 and dy > self.drop_threshold and a.fighter.on_ground:
                held.add(keys["down"])
            # Attack on a cadence when at standoff range and roughly level. The
            # vertical tolerance is wide enough to keep engaging after knockback
            # nudges the target a platform up/down, avoiding a positional
            # deadlock under the post-startup hitbox timing.
            in_range = (self.standoff - 18) <= adx <= self._melee_range(a) and abs(dy) < 60
            # #232: reaction_delay — wait this many frames after entering range
            # before the first attack (a higher level reacts faster). With the
            # default reaction_delay=0 this is always satisfied → unchanged.
            if in_range:
                if self._in_range_since is None:
                    self._in_range_since = self._f
                reacted = (self._f - self._in_range_since) >= self.reaction_delay
            else:
                self._in_range_since = None
                reacted = False
            if in_range and reacted and (self._f - self._last_attack) >= self.attack_period:
                # #238: follow-through — commit the attack only with probability
                # follow_through_p (seeded). p >= 1.0 skips the roll (always commit,
                # golden-safe default); a failed roll hesitates and retries later.
                commit = (self.follow_through_p >= 1.0
                          or self.rng.random() < self.follow_through_p)
                if commit:
                    held.add(keys["attack"])
                    self._last_attack = self._f
                    # #292: convert a NEUTRAL grounded attack into a forward-tilt.
                    # The bot converges to `standoff` and strikes from rest, so the
                    # move-select seam always resolved the neutral **jab** — a
                    # set-knockback move (WDSK) whose launch is fixed regardless of
                    # the victim's percent, so it can NEVER KO. No bot match could
                    # end by KO (the loser juggled past 1400% with all stocks). A
                    # leveled tilt-capable bot instead holds "toward" so a
                    # percent-scaling **f-tilt** lands — the only launch that grows
                    # with damage and can finish. Gated to leveled bots with tilts
                    # enabled, so the level-less golden-safe default and the
                    # jab-only Lv1 are byte-identical. Skipped when up/down already
                    # steer an intended u-tilt/d-tilt (both also scaling moves), so
                    # no sideways drift is injected into a jump/drop.
                    if (self.level is not None and "tilts" in self.enabled_moves
                            and a.fighter.on_ground
                            and keys["up"] not in held
                            and keys["down"] not in held):
                        held.add(toward)

        # --- #368 anti-stall backstop (leveled-only, deterministic, no rng) --------
        # Detect a no-progress lock and inject one toward-target action. A legit-
        # spacing / engaging bot moves > ANTI_STALL_MOVE_PX or lands a hit (percent
        # moves) within 1.5s, resetting the reference, so this never fires then.
        if self.level is not None:
            # getattr defaults keep minimal combat stubs (no .percent) working (#137/#291).
            cur = (a.rect.centerx, a.rect.centery,
                   getattr(a.fighter, "percent", 0), getattr(t.fighter, "percent", 0))
            ref = self._noprog_ref
            reachable = getattr(t.fighter, "is_alive", True)
            progressed = (ref is None
                          or abs(cur[0] - ref[0]) > ANTI_STALL_MOVE_PX
                          or abs(cur[1] - ref[1]) > ANTI_STALL_MOVE_PX
                          or cur[2] != ref[2] or cur[3] != ref[3])
            if progressed or not reachable:
                self._noprog = 0
                self._noprog_ref = cur
            else:
                self._noprog += 1
            if reachable and self._noprog >= ANTI_STALL_MAX:
                # Policy locked -> force progress toward the target, overriding any
                # conflicting horizontal decision above (no left+right cancel). The
                # vertical is PULSED (alternate frames) for a fresh press edge (#369).
                dx = t.rect.centerx - a.rect.centerx
                dy = t.rect.centery - a.rect.centery
                held.discard(keys["left"])
                held.discard(keys["right"])
                held.add(keys["right"] if dx > 0 else keys["left"])
                if dy < -ANTI_STALL_MOVE_PX and self._noprog % 2 == 0:
                    held.add(keys["up"])
                elif dy > ANTI_STALL_MOVE_PX:
                    held.add(keys["down"])

        return held


# Back-compat alias: the original single controller was the attacker policy.
ChaseController = AttackerController


class IdlerController(BaseController):
    """A deterministic baseline opponent. By default a true no-op (emits nothing),
    so it stands in for an idle player transparently. Optionally performs minimal
    activity: with `shield_period > 0`, holds `shield` for `shield_hold` frames at
    the start of each `shield_period`-frame cycle (RNG-free, deterministic). With
    `shield_chance > 0` (#166), instead rolls the injected PRNG each frame and
    holds `shield` with that probability — the first consumer of the seeded-RNG
    seam, so a seed change visibly changes shield timing. Position-independent.
    """

    def __init__(self, attacker_num=1, shield_period=0, shield_hold=0,
                 shield_chance=0.0, rng=None):
        super().__init__(attacker_num, rng=rng)
        self.shield_period = shield_period
        self.shield_hold = shield_hold
        self.shield_chance = shield_chance

    def decide(self, a, t, frame, attacks=None) -> set:
        # #166 first consumer: an rng-jittered shield. A real PRNG roll per frame,
        # so two seeds diverge while a fixed seed repeats — the end-to-end proof
        # that the injected RNG reaches a chosen InputFrame (and nothing else).
        if self.shield_chance > 0.0:
            return {a.controls["shield"]} if self.rng.random() < self.shield_chance else set()
        if self.shield_period > 0 and (self._f % self.shield_period) < self.shield_hold:
            return {a.controls["shield"]}
        return set()


class FollowerController(BaseController):
    """Shadows the target at a `standoff` distance and mirrors its movement,
    applying spatial pressure WITHOUT committing to an attack. Deterministic and
    position-driven: the attacker's horizontal spacing logic (close in if too
    far, back off if too close, clamped to `safe_x`) minus the attack and the
    vertical jump/drop. The wide default gap makes the shadowing visually
    distinct from the attacker.
    """

    def __init__(self, attacker_num=1, standoff=120, safe_x=(110, 850), rng=None):
        super().__init__(attacker_num, rng=rng)
        self.standoff = standoff
        self.safe_x = safe_x

    def decide(self, a, t, frame, attacks=None) -> set:
        held = set()
        if not t.fighter.is_alive:
            return held
        keys = a.controls
        dx = t.rect.centerx - a.rect.centerx
        adx = abs(dx)
        cx = a.rect.centerx
        lo, hi = self.safe_x
        toward = keys["right"] if dx > 0 else keys["left"]
        away = keys["left"] if dx > 0 else keys["right"]
        # Maintain the standoff gap: close in if too far, back off if too close.
        move = None
        if adx > self.standoff + 8:
            move = toward
        elif adx < self.standoff - 8:
            move = away
        # Never press further past a blast-zone-side bound (allow coming back in).
        if move == keys["right"] and cx >= hi:
            move = None
        elif move == keys["left"] and cx <= lo:
            move = None
        if move is not None:
            held.add(move)
        return held
