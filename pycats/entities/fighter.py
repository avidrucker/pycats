"""Fighter — the Sprite-free domain aggregate for a fighter's combat state + rules.

The end of the D1 `Player` god-object decomposition (#69), landed across slices
6b-1 (#81, combat state + stats + S3 invariants), 6b-2 (#83, the rules), 6b-3a
(#84, kinematics) and 6b-3b (#87, timers/flags/facing/weight). `Fighter` now owns
**all** of a fighter's simulation state and the rules over it; `Player` is the
thin `pygame.sprite.Sprite` adapter that composes a `Fighter`, wires the
subsystems (`_clock`/`_input`/`engine`/`tail`), exposes delegating properties so
every reader/writer is unchanged, and orchestrates the per-frame `update()`.

`Fighter` is deliberately NOT a `pygame.sprite.Sprite` — it holds plain values
(`pygame.Rect`/`Vector2` are kept as value types per the #69 Sprite-free, not
pygame-free, boundary), enforces its contracts, and runs the rules. It is
**self-contained** (#264/S6): no back-reference to the Player. Domain methods that
need an FSM transition (`_ko`, the #145 auto-knockdown in `_handle_landing`)
*return intent*; the Player adapter applies it. The dependency is strictly
one-way — adapter → entity — and an AST guard pins it.

Invariants (S3 — enforced once, at the setter, instead of re-derived per site):
- ``percent >= 0``                 (had NO guard before — first enforcement)
- ``0 <= shield_hp <= SHIELD_MAX_HP`` (clamps were scattered across player.py)
- ``lives >= 0``                   (was only clamped at the `_ko` site, #54)

Invariants (S3 — enforced once, at the setter, instead of re-derived per site):
- ``percent >= 0``                 (had NO guard before — first enforcement)
- ``0 <= shield_hp <= SHIELD_MAX_HP`` (clamps were scattered across player.py)
- ``lives >= 0``                   (was only clamped at the `_ko` site, #54)
"""

from __future__ import annotations

import math

import pygame  # type: ignore

from ..combat.knockback import (
    hitlag_frames,
    hitstun_frames,
    knockback,
    sakurai_angle,
    set_knockback,
)
from ..combat.shield import shield_break_stun_frames, shieldstun_frames
from ..combat.tangibility import resolve_tangibility
from ..config import (
    BLAST_PADDING,
    BLAST_PADDING_X,
    CROUCH_CANCEL_FACTOR,
    DASH_DURATION,
    DODGE_AIR_SPEED,
    DODGE_SPEED,
    DODGE_TIME,
    GETUP_ROLL_FRAMES,
    GETUP_ROLL_SPEED,
    INITIAL_LIVES,
    KNOCKBACK_LAUNCH_FACTOR,
    KNOCKDOWN_VY_THRESHOLD,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    PLAYER_SIZE,
    RESPAWN_DELAY_FRAMES,
    SAKURAI_ANGLE_CODE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DRAIN_PER_FRAME,
    SHIELD_MAX_HP,
    WAVEDASH_ANGLE_DEG,
    WAVEDASH_LANDING_LAG,
)

# Where a KO'd fighter's rect is parked while dead — far off any stage so it can't
# collide or render on-screen during the respawn wait (#425: named sentinel).
_KO_OFFSCREEN_POS = (-1000, -1000)


class Fighter:
    def __init__(self, x, y, facing_right, fighter_data):
        # No back-reference to the owning Player (#264/S6): all simulation state is
        # Fighter's own, and the few Player-side effects are returned as intent for
        # the adapter to apply.

        # ---------- per-character stats from FighterData (#123/#126) ----------
        # weight feeds the knockback formula (#40); the movement constants are
        # read per-fighter by the physics/input layer. All default (in
        # FighterData) to the config globals, so the default cat is unchanged.
        self.weight = fighter_data.weight
        self.gravity = fighter_data.gravity
        self.max_fall_speed = fighter_data.max_fall_speed
        self.move_speed = fighter_data.move_speed
        self.dash_speed = fighter_data.dash_speed  # #388: the faster tap-burst speed
        self.jump_vel = fighter_data.jump_vel
        self.max_jumps = fighter_data.max_jumps

        # ---------- crouch geometry (#124) ----------
        # stand_size is the body's full standing box; crouch_size/_hurtbox are
        # the per-cat crouch geometry (None = this fighter can't crouch).
        # Per-fighter stand_size (#275): a small archetype (Kirby) overrides it;
        # None falls back to the global config.PLAYER_SIZE (#286: read config
        # directly rather than reaching through the Player adapter's SIZE).
        self.stand_size = tuple(fighter_data.stand_size or PLAYER_SIZE)
        self.crouch_size = fighter_data.crouch_size
        self.crouch_hurtbox = fighter_data.crouch_hurtbox
        self.crouch_attempting = False  # set per-frame by input (down on ground)
        # Prone/knockdown geometry (#173): lying-down counterpart of crouch, used
        # while state == "prone" (entered via Player.force_prone). None = no posture.
        self.prone_size = fighter_data.prone_size
        self.prone_hurtbox = fighter_data.prone_hurtbox

        # ---------- kinematics (#84 / 6b-3a) ----------
        # The authoritative body box + velocity now live on the domain object;
        # Player exposes them as delegating get/set properties (pygame value
        # types, kept per the #69 Sprite-free-not-pygame-free boundary).
        self.rect = pygame.Rect(0, 0, self.stand_size[0], self.stand_size[1])
        self.rect.midbottom = (x, y)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.spawn_point = pygame.Vector2(x, y)

        # ---------- combat state (invariant-enforced via the setters) ----------
        self._percent = 0
        self._shield_hp = SHIELD_MAX_HP
        self._lives = INITIAL_LIVES

        # ---------- game statistics ----------
        self.attacks_made = 0  # Total attacks initiated
        self.hits_landed = 0  # Successful hits on opponent
        self.suicides = 0  # Deaths without being hit (self-inflicted)
        # Cumulative percent damage dealt to / received from opponents across the
        # whole match. These are match-scoped like the counters above: they are
        # deliberately NOT reset by reset_to_spawn (#98), so they survive respawns
        # and only start fresh when a new Player is built for a new match.
        self.damage_given = 0.0  # Total percent damage this fighter dealt
        self.damage_taken = 0.0  # Total percent damage this fighter received
        self.was_hit_before_ko = False  # Track if last KO was from being hit

        # ---------- spawn / KO ----------
        self.is_alive = True

        # ---------- timers / counters (#87 / 6b-3b) ----------
        self.respawn_timer = 0  # frames until next spawn
        self.dodge_timer = 0
        self.dash_timer = 0  # #388: initial-dash burst window; `dash` state while > 0
        # #388 slice 2b (#403): double-tap edge-detection. `dash_input_window`
        # counts down after a fresh directional press; a second same-direction
        # press while it's > 0 is a double-tap → `_start_dash`. `dash_input_dir`
        # records the first tap's direction (+1 right / -1 left, 0 = disarmed).
        self.dash_input_window = 0
        self.dash_input_dir = 0
        self.hurt_timer = 0
        self.stun_timer = 0
        self.prone_timer = 0  # knockdown/getup window (#13); prone while > 0
        self.getup_roll_timer = 0  # getup-roll duration + intangibility window (#146)
        self.getup_attack_timer = 0  # wake-up attack duration out of prone (#225)
        self.landing_lag_timer = 0  # post-waveland action lock (#202); locked while > 0
        self.grabbed_ledge = None  # the Ledge being held, or None (#14); its presence
        # is the authoritative "am I hanging" signal the statechart reads. No hang
        # timeout (#475: PM has no hang timer) — hang persists until the fighter acts.
        self.ledge_regrab_lockout_timer = 0  # post-release regrab suppression (#14)
        self.ledge_intangible_timer = 0  # percent-scaled ledge-grab intangibility burst (#311)
        self.ledge_intangible_granted = 0  # the burst's granted length at grab; INTANG bar denominator (#531)
        self.ledge_getup_timer = 0  # neutral ledge-getup climb window; edge frees at half (#311)
        self.ledge_regrab_count = 0  # consecutive ledge grabs w/o touching ground (#656);
        # drives the 5-regrab anti-plank cutoff. Resets on landing (_handle_landing) or
        # getting hit (receive_hit). Grab 6+ grants only the placeholder residual burst.
        self.land_impact_vy = 0.0  # downward speed at last ground contact (#145)
        self.hitlag_timer = 0  # freeze frames on a clean hit (#138); both fighters
        self.shieldstun_timer = 0  # locked-in-shield frames after a block (#140)
        # attack_timer is a derived property on Player over its MoveClock (#71).
        # Smash charge (#327 slice 3a): while charging a chargeable smash, the
        # timer accumulates 0..SMASH_CHARGE_FRAMES and pending_smash_key holds the
        # move being charged; the release/max fires it (fighter_input). The #334
        # CHARGE bar reads smash_charge_timer. smash_charge_fraction is captured at
        # fire time for the slice-3b output scaling.
        self.smash_charge_timer = 0
        self.pending_smash_key = None
        self.smash_charge_fraction = 0.0
        # Angled f-smash (#327 slice 4): None / "up" / "down", captured at the smash
        # press and applied (then cleared) at the fsmash's Attack spawn.
        self.smash_angle_dir = None
        self.intangible_timer = 0  # intangibility mid-dodge, post-respawn, or while ledge grabbing
        self.jumps_remaining = self.max_jumps
        self.air_dodge_ok = True  # players can only air dodge once per sustained jump/fall, until they land
        self.intangible = False  # dodging / post-hit / respawn / ledge-grab intangibility
        # Respawn-descent invincibility window (#802 machinery; SET by #506's respawn
        # flow, not here). While > 0 the fighter is INVINCIBLE: a hit CONNECTS but the
        # defender is "otherwise unaffected" (attacker freezes, defender zeroed) — see
        # pycats.combat.tangibility. Distinct from `intangible` (pass-through). Ticked
        # down in Player.update alongside the other immunity timers.
        self.invincible_timer = 0
        # (#321/F3: done_attacking is a derived Player property now — no field here.)

        # ---------- shield / dodge flags ----------
        self.shield_attempting = False  # shield visual helper
        self.drop_platform = None  # platform drop-through reference
        self.dodge_blocked_by_edge = False  # current dodge is blocked by an edge
        self.spot_dodge_shield_held = False  # shield was held during a spot dodge
        # PM-faithful air dodge (#184): True while an air dodge is in progress, so the
        # statechart routes the dodge's exit to `helpless` (not `fall`); cleared on land.
        self.air_dodge_active = False
        # Special-recovery / up-B (#578): True from a recovery move's start until it
        # lands, so the move's airborne exit routes to `helpless` (#184) like an air
        # dodge. Armed in fighter_input on a `grants_recovery` move; cleared on land.
        self.recovery_active = False
        # Wavedash (#202): True while a *diagonal-down* air dodge is in progress, so
        # landing cancels into a waveland (slide + landing lag) rather than a plain
        # land. Set in _start_dodge, consumed/cleared in _handle_landing.
        self.wavedash_armed = False

        # ---------- facing ----------
        self.facing_right = facing_right
        self.original_facing_right = facing_right  # restored on respawn

    # ---------- combat state ----------
    @property
    def percent(self) -> float:
        return self._percent

    @percent.setter
    def percent(self, value) -> None:
        self._percent = max(0, value)  # percent >= 0 (S3 — first guard)

    @property
    def shield_hp(self) -> float:
        return self._shield_hp

    @shield_hp.setter
    def shield_hp(self, value) -> None:
        # 0 <= shield_hp <= SHIELD_MAX_HP (S3 — consolidate the scattered clamps).
        # Rounding stays at the tick site: it's a precision policy, not the range
        # invariant.
        self._shield_hp = min(max(value, 0), SHIELD_MAX_HP)

    @property
    def lives(self) -> int:
        return self._lives

    @lives.setter
    def lives(self, value) -> None:
        self._lives = max(0, value)  # lives >= 0 (#54)

    # ---------- stat counters ----------
    def record_attack_made(self) -> None:
        """Record that this fighter initiated an attack."""
        self.attacks_made += 1

    def record_hit_landed(self) -> None:
        """Record that this fighter successfully hit an opponent."""
        self.hits_landed += 1

    def record_hit_received(self) -> None:
        """Record that this fighter was hit by an opponent."""
        self.was_hit_before_ko = True

    def record_damage_given(self, amount) -> None:
        """Record percent damage this fighter dealt to an opponent (#98)."""
        self.damage_given += amount

    @property
    def tangibility(self):
        """This fighter's immunity state for the frame (#802), derived from the
        imperative `intangible` flag and the `invincible_timer`, most-protective-wins
        (INTANGIBLE > INVINCIBLE > TANGIBLE). See pycats.combat.tangibility."""
        return resolve_tangibility(self.intangible, self.invincible_timer > 0)

    # ----------- per-frame timers ------------
    def tick_timers(self) -> None:
        """Advance the fighter's *stateless* per-frame timers (S1/#273).

        These decrement with no transition side-effect, so the aggregate owns the
        tick (was inline in `Player.update()`, N2). `ledge_hang`/`respawn` (other
        regions) and `hitlag` (bound to the freeze early-return) stay in
        `Player.update()` until later slices (#264 S4b/S5)."""
        for name in (
            "hurt_timer",
            "stun_timer",
            "landing_lag_timer",
            "ledge_regrab_lockout_timer",
            "shieldstun_timer",
            "dash_input_window",
            "invincible_timer",  # #802: respawn-invincibility window (stateless; #506 sets it)
        ):  # #403: double-tap window (stateless)
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, v - 1)

    def tick_action_timers(self) -> set:
        """Decrement the cleanly-movable transition-coupled timers; return the
        names that hit 0 THIS frame (#264/S4).

        The aggregate owns the *decrement* (N2); the *decisions* on expiry stay in
        `Player.update()` because they read input + drive Player wiring. The
        returned set gives `prone` its once-on-expiry semantics (a timer already at
        0 never re-appears, so the getup decision fires exactly once); `dodge`'s
        every-frame transition reads the value directly, so it's decremented here
        but callers don't gate on the return.

        NOT moved: `getup_roll_timer`/`getup_attack_timer` are *set inside the
        prone-expiry block and decremented by their own blocks in the same frame*,
        so they must keep their inline decrement (moving it here would drop that
        same-frame tick — an off-by-one on the getup duration)."""
        expired = set()
        for name in ("prone_timer", "dodge_timer", "dash_timer"):
            v = getattr(self, name)
            if v > 0:
                v -= 1
                setattr(self, name, v)
                if v == 0:
                    expired.add(name)
        return expired

    def tick_respawn(self) -> None:
        """Advance the respawn countdown (#264/S4b). Unfloored — it keeps counting
        past 0 while a permanently-dead fighter (lives == 0) waits, matching the
        old inline `respawn_timer -= 1`. The reset trigger + early-return stay in
        Player.update()."""
        self.respawn_timer -= 1

    def _dislodge_from_ledge(self) -> None:
        """Knock a ledge-hanging fighter off the edge (#475). PM lets you hit a hanger
        off once its grab-intangibility burst has lapsed; with no auto-drop timeout,
        this is how a hang ends under attack. Free the edge, clear the hang + its
        intangibility, arm the regrab lockout (so the launch can't instantly re-grab),
        and go airborne — the caller's knockback then carries the fighter away."""
        if self.grabbed_ledge is not None:
            self.grabbed_ledge.occupied_by = None
        self.grabbed_ledge = None
        self.ledge_intangible_timer = 0
        self.intangible = False
        self.ledge_regrab_lockout_timer = LEDGE_REGRAB_LOCKOUT_FRAMES
        self.on_ground = False

    # ----------- hit processing ------------
    def receive_hit(self, atk, is_crouching=False):
        """Called by combat system when this player is struck.

        `is_crouching` is passed in by `combat.process_hits` (#283/S2) — the domain
        rule no longer reaches up into the adapter's FSM state label. Defaults
        False so the "no `.state` ⇒ not crouching" contract holds for minimal
        combat stand-ins and non-crouch callers."""
        self.record_hit_received()  # Track that this player was hit
        self.ledge_regrab_count = 0  # getting hit resets the anti-plank regrab count (#656)
        # A connecting hit reaches receive_hit only past the ledge-grab intangibility
        # burst (combat skips `intangible` defenders), so any hit that lands while
        # hanging knocks the fighter OFF the ledge (#475). Release the hang before the
        # knockback below so the launch actually carries — while grabbed_ledge is set,
        # Player.update pins the body and discards velocity. This is what lets a hanger
        # be edge-guarded / KO'd now that there's no auto-drop timeout to do it.
        if getattr(self, "grabbed_ledge", None) is not None:
            self._dislodge_from_ledge()
        if self.shield_attempting and self.shield_hp > 0:
            self.shield_hp = self.shield_hp - atk.damage  # setter clamps >= 0
            if self.shield_hp == 0:
                self._start_stun()  # shield broke -> dizzy stun (#12) supersedes
            else:
                # Shield held: shieldstun (#140) locks the defender in shield for
                # floor(dmg*0.345) frames, and BOTH fighters take shield hitlag
                # (the #138 deferral). Player.update runs the hitlag freeze first,
                # then ticks shieldstun — Smash ordering (hitlag, then shieldstun).
                self.shieldstun_timer = shieldstun_frames(atk.damage)
                hl = hitlag_frames(atk.damage)
                self.hitlag_timer = hl
                atk.owner.fighter.hitlag_timer = hl
        #### TODO: elif dodging
        else:
            # Phase 1 (#40): authentic Brawl/PM knockback + hitstun-from-knockback.
            self.percent += atk.damage
            # Credit the percent damage to both sides for the win-screen stats
            # (#98). Only the non-shield path counts — a shielded hit deals shield
            # damage, not percent, so it is correctly excluded here.
            self.damage_taken += atk.damage
            atk.owner.fighter.record_damage_given(atk.damage)
            # Weight-dependent set knockback (#211): a WDSK hit's launch ignores
            # the victim's percent (set) but still scales with weight + KBG/BKB.
            # The hit still dealt its damage % above; only the knockback is set.
            wdsk = getattr(atk, "set_knockback", None)
            if wdsk is not None:
                kb = set_knockback(wdsk, self.weight, atk.base_knockback, atk.knockback_growth)
            else:
                kb = knockback(self.percent, atk.damage, self.weight, atk.base_knockback, atk.knockback_growth)
            # Crouch-cancel (#135): a hit taken while in the `crouch` state (#124)
            # has its knockback scaled down by CROUCH_CANCEL_FACTOR (0.67x, PM)
            # before launch + hitstun are derived — crouch as a defensive tool.
            # Hitlag scaling (the "c" multiplier) stays deferred this slice.
            if is_crouching:
                kb *= CROUCH_CANCEL_FACTOR
            self.hurt_timer = hitstun_frames(kb)
            self.cancel_smash_charge()  # a hit mid-charge abandons the smash (#327/3a)
            self.smash_angle_dir = None  # ...and its aimed angle (#327/4)
            # (the red hurt-flash is now render-time: render_battle.body_tint #75)
            direction = 1 if atk.owner.fighter.facing_right else -1  # the direction of the attack
            # Sakurai-angle sentinel (#203): 361 is a code, not literal degrees —
            # resolve it from this hit's knockback + whether we're grounded.
            angle_deg = atk.angle
            if angle_deg == SAKURAI_ANGLE_CODE:
                angle_deg = sakurai_angle(kb, self.on_ground)
            radians = math.radians(angle_deg)
            # Initial launch velocity (#44): KB * launch factor. It then bleeds
            # off via decay_velocity each hitstun frame in update() — Smash-style
            # ease-out rather than a constant slide (#43). Issue #8: COMBINE the
            # defender's existing horizontal momentum (`+=`) instead of
            # overwriting it; vertical stays an override (`=`) so a launch sets the
            # arc rather than adding to fall speed.
            launch = kb * KNOCKBACK_LAUNCH_FACTOR
            self.vel.x += launch * math.cos(radians) * direction
            self.vel.y = launch * -math.sin(radians)  # up = negative y
            # Hitlag / freeze frames (#138): BOTH fighters freeze for a few frames
            # before the slide begins. The launch velocity + hurt_timer are set
            # now but neither acts until the freeze ends — Player.update returns
            # early while hitlag_timer > 0, so position is held, hitstun does not
            # tick, and the attacker's move clock pauses. Knockback then proceeds
            # intact. Percent (above) already applied, so damage shows at impact.
            hl = hitlag_frames(atk.damage)
            self.hitlag_timer = hl
            atk.owner.fighter.hitlag_timer = hl

    def receive_hit_invincible(self, atk) -> None:
        """INVINCIBLE defender (#802, decision #784): the hit CONNECTS but this
        defender is "otherwise unaffected" — only the ATTACKER takes hitlag.

        Grounded in the #797 findings
        (docs/research/2026-07-20-pm-invincible-hitlag-findings.md, Q1/Q2/§6):
        meleelight `executeRegularHit` sets the attacker's hitlag before bailing out
        of the invincible victim's processing, so the attacker freezes while the
        defender's percent, knockback, hitstun, and hitlag all stay at zero. SmashWiki
        (series-universal): "the attacker will still experience hitlag … the opponent
        will otherwise be unaffected." The PM-3.6 step is `[inference]`; no PM primary
        exists. Contrast `receive_hit` (TANGIBLE, full resolution) and the INTANGIBLE
        skip in `combat.process_hits` (pass-through, no attacker hitlag)."""
        # Attacker freezes exactly as on a normal hit; the invincible defender is left
        # untouched — no percent, knockback, hitstun, or hitlag applied to it.
        atk.owner.fighter.hitlag_timer = hitlag_frames(atk.damage)

    def _handle_landing(self, was_airborne: bool) -> bool:
        """Resolve a landing. Returns True when the #145 auto-knockdown triggers
        (the caller, via step_physics -> Player.update, applies force_prone — the
        domain no longer reaches the Player engine, #298/S5)."""
        if self.on_ground and was_airborne:
            self.ledge_regrab_count = 0  # touching the stage resets the anti-plank count (#656)
            self.jumps_remaining = self.max_jumps  # reset jumps when landing
            self.air_dodge_ok = True  # reset air dodge availability
            self.air_dodge_active = False  # landing ends helpless/special-fall (#184)
            self.recovery_active = False  # landing ends up-B recovery/helpless (#578)

            # Waveland (#202): a diagonal-down air dodge that touches the ground
            # cancels into a grounded slide + landing lag. End the dodge cleanly
            # (drop intangibility now) but KEEP the horizontal velocity — that's the
            # slide, which decays under GROUND_FRICTION during the lag. The chart
            # routes dodge/helpless -> `landing_lag` while landing_lag_timer > 0, and
            # the dodge-end vel.x zeroing in player.update is guarded off the timer so
            # the momentum survives.
            if self.wavedash_armed:
                self.wavedash_armed = False
                self.landing_lag_timer = WAVEDASH_LANDING_LAG
                self.dodge_timer = 0
                self.intangible = False
            # Auto landing-velocity knockdown (#145): landing hard while still in
            # hitstun (tumble) without teching forces `prone` (#13). The hurt-timer
            # gate is what separates this from a normal jump landing (same impact
            # speed, but hurt_timer == 0). Clear hurt_timer so the getup exit
            # (prone -> idle when prone_timer hits 0) doesn't pop back into hurt.
            if self.hurt_timer > 0 and self.land_impact_vy >= KNOCKDOWN_VY_THRESHOLD:
                self.hurt_timer = 0
                return True  # caller applies force_prone (#298/S5)
        return False

    def _handle_takeoff(self, was_airborne: bool) -> None:
        """Symmetric counterpart to _handle_landing (#473, ruling #466): on a
        ground->air transition, forfeit the grounded jump so only the midair
        jump(s) remain. PM-faithful — leaving the ground without jumping loses the
        grounded jump.

        The clamp is correct for every takeoff cause without knowing which:
        - jumped off  → the jump press already set jumps_remaining = max_jumps-1,
          so min(...) is a no-op;
        - walked / fell / dropped off → max_jumps clamps down to max_jumps-1;
        - launched (hitstun) → input gated, still max_jumps → clamps to max_jumps-1
          (a launched fighter keeps its midair jump).
        Respawn is not special-cased: today's airborne spawn has no ground->air
        transition, so this never fires on spawn (#480)."""
        if not was_airborne and not self.on_ground:
            self.jumps_remaining = min(self.jumps_remaining, self.max_jumps - 1)

    # ============================================================= KO / respawn
    def _outside_blast_zone(self) -> bool:
        # Horizontal (left/right) uses the wider BLAST_PADDING_X (#733, temporary
        # game-feel experiment — see config.py); vertical (top/bottom) stays on
        # BLAST_PADDING.
        return (
            self.rect.right < -BLAST_PADDING_X
            or self.rect.left > SCREEN_WIDTH + BLAST_PADDING_X
            or self.rect.bottom < -BLAST_PADDING
            or self.rect.top > SCREEN_HEIGHT + BLAST_PADDING
        )

    def _ko(self):
        # Track if this was a suicide (no hit received before KO)
        if not self.was_hit_before_ko:
            self.suicides += 1

        # Decrement; the lives>=0 invariant (#54) is now enforced once, in the
        # Fighter.lives setter (#81), instead of clamped here. This keeps a
        # zero-life player from going negative if the is_alive / respawn gates
        # ever let a re-KO through.
        self.lives -= 1
        self.is_alive = False
        self.respawn_timer = RESPAWN_DELAY_FRAMES
        # hide sprite off-screen
        self.rect.center = _KO_OFFSCREEN_POS
        self.vel.update(0, 0)
        # FSM transition applied by the caller (Player.update) — the domain no
        # longer drives the Player engine (#298/S5).

    def reset_to_spawn(self):
        """Domain half of the per-life reset to a clean spawn state (#34).

        Both reset paths go through `Player.reset_to_spawn` (#286) — the per-life
        respawn (`Player.update`) and the new-match reset (`battle_screen`) — so
        the two cannot silently drift; that wrapper calls this then resets the
        Player-owned clock/tail. This resets only per-life/spawn state; it does
        NOT touch match-scoped fields
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
        self.jumps_remaining = self.max_jumps
        self.air_dodge_ok = True
        self.air_dodge_active = False  # clear helpless/special-fall on respawn (#184)
        self.recovery_active = False  # nor a pending up-B recovery (#578)
        self.wavedash_armed = False  # nor a pending waveland (#202)
        self.percent = 0
        self.shield_hp = SHIELD_MAX_HP
        self.shield_attempting = False
        self.was_hit_before_ko = False  # reset hit tracking for the next life
        # Transient hitstun / action timers + flags. _ko early-returns from
        # update(), so these never tick down during death; clearing them here is
        # what keeps a player KO'd mid-hurt/stun (#9) or mid-dodge/attack (#31)
        # from carrying that state into its next life (a frozen dodge_timer, a
        # leaked intangible=True, etc.).
        self.respawn_timer = 0
        self.dodge_timer = 0
        self.hurt_timer = 0
        self.stun_timer = 0
        self.landing_lag_timer = 0  # don't carry a waveland lock across a KO/respawn (#202)
        # Ledge-hang (#14): free the held edge and clear the hang so a KO/respawn or
        # match reset can't leave a fighter pinned or an edge permanently occupied.
        if self.grabbed_ledge is not None:
            self.grabbed_ledge.occupied_by = None
        self.grabbed_ledge = None
        self.ledge_regrab_lockout_timer = 0
        self.ledge_regrab_count = 0  # a KO/respawn starts the anti-plank count fresh (#656)
        self.hitlag_timer = 0  # don't carry a freeze across a KO/respawn (#138)
        self.shieldstun_timer = 0  # nor a block-stun (#140)
        self.intangible_timer = 0
        self.intangible = False
        self.invincible_timer = 0  # don't carry a respawn-invincibility window across a KO/respawn (#802)
        self.spot_dodge_shield_held = False
        self.cancel_smash_charge()  # don't carry a pending charge across KO/respawn (#327/3a)
        self.smash_angle_dir = None  # nor a pending aimed-fsmash angle (#327/4)
        self.dodge_blocked_by_edge = False
        # (#321/F3: done_attacking is derived on Player; the clock reset below
        #  in Player.reset_to_spawn makes it True.)
        # (visual reset is render-time now: render_battle.body_tint #75)
        # The Player-owned wiring reset here — the move clock (attack_timer/
        # current_move/move_frame derive from it) and the Verlet tail layout (#41)
        # — now lives in Player.reset_to_spawn (#286/S3), which calls this then
        # resets self._clock + self.tail. The aggregate no longer reaches `owner`.

    # state starters ----------------------------
    def cancel_smash_charge(self) -> None:
        """Abandon an in-progress smash charge (#327/3a): drop the accumulated
        timer + the pending move. Called on a mid-charge hit (receive_hit) and on
        KO/respawn (reset_to_spawn); the input handler also uses it to release."""
        self.smash_charge_timer = 0
        self.pending_smash_key = None

    def tick_shield(self, shielding: bool) -> None:
        """Per-frame shield-HP tick (#341).

        While shielding, the shield drains by SHIELD_DRAIN_PER_FRAME and BREAKS
        into the dizzy `stun` if it empties — matching Melee/PM, where a shield
        that reaches 0 by ANY means breaks, not only by a connecting hit. This is
        the drain-path counterpart of the hit-path break in `receive_hit`; both
        now route a 0-hp shield through `_start_stun()` (the single break rule).
        While not shielding, the shield regenerates. The setter clamps
        [0, SHIELD_MAX_HP]."""
        if shielding:
            self.shield_hp = round(self.shield_hp - SHIELD_DRAIN_PER_FRAME, 2)
            if self.shield_hp == 0:
                self._start_stun()  # shield broke -> dizzy stun (#12/#341)
        else:
            self.shield_hp = round(self.shield_hp + SHIELD_DRAIN_PER_FRAME, 2)

    def _start_stun(self) -> None:
        # Shield-break "dizzy" (#12): damage-scaled duration (Melee/PM). The
        # engine flips state -> "stun" on the next tick (the chart/FSM `stun`
        # entry guards on stun_timer > 0); input is locked while the timer runs.
        self.stun_timer = shield_break_stun_frames(self.percent)
        self.vel.update(0, 0)

    def start_getup_roll(self, direction: int) -> None:
        """Roll out of `prone` (#146): a directional getup with intangibility.

        Holding left/right as the getup window ends rolls that way instead of a
        neutral stand. Grants intangibility for the roll and sets an initial
        horizontal velocity that decays under friction. ``direction`` is -1 (left)
        or +1 (right). Reuses the same intangible/timer machinery as the dodge.
        """
        self.getup_roll_timer = GETUP_ROLL_FRAMES
        self.intangible = True
        self.intangible_timer = GETUP_ROLL_FRAMES
        self.vel.update(direction * GETUP_ROLL_SPEED, 0)

    def _start_dash(self, direction: int) -> None:
        """Begin an initial-dash burst (#388, slice 2a). Sets the burst window and
        launches at `dash_speed` in `direction` (+1 right, -1 left), facing that way.
        Mirrors `_start_dodge` as the seam the input layer calls; slice 2b's
        double-tap detection is the caller. `run` (the sustained state after the
        burst) is slice 3. Grounded only for now."""
        self.dash_timer = DASH_DURATION
        self.vel.x = direction * self.dash_speed
        self.facing_right = direction > 0

    def _start_dodge(self, dir_x: int, dir_y: int = 0) -> None:
        self.dodge_timer = DODGE_TIME
        self.intangible = True
        self.dodge_blocked_by_edge = False  # Reset edge blocking flag
        self.wavedash_armed = False  # only a diagonal-down air dodge re-arms it (below)

        # Only set spot_dodge_shield_held for ground-based spot dodges (not air dodges)
        if dir_x == 0 and self.on_ground:
            # Ground spot dodge - no movement, special thin platform protection
            self.vel.update(0, 0)  # No movement for ground spot dodge
            self.spot_dodge_shield_held = True
        elif dir_x == 0 and not self.on_ground:
            # Neutral air dodge (PM/Melee, #184): HALT momentum — replace velocity
            # with ~zero (hover), not Brawl-style preserve. Gravity still applies
            # over the dodge frames. Routes to `helpless` on exit via air_dodge_active.
            self.vel.update(0, 0)
            self.air_dodge_active = True
            self.spot_dodge_shield_held = False
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
            elif dir_y > 0:
                # Diagonal-down air dodge → wavedash (#202): SET the burst at the
                # canonical wavedash angle below horizontal (SmashWiki: 17.1°) so it
                # drives into the ground. Landing then cancels into a grounded slide
                # (the waveland) via wavedash_armed. +y is down.
                ang = math.radians(WAVEDASH_ANGLE_DEG)
                self.vel.update(dir_x * DODGE_AIR_SPEED * math.cos(ang), DODGE_AIR_SPEED * math.sin(ang))
                self.air_dodge_active = True
                self.wavedash_armed = True
            else:
                # Directional air dodge (PM/Melee, #184): SET (replace) velocity to a
                # fixed burst in the stick direction and zero vertical — not Brawl-style
                # additive/preserve. Routes to `helpless` on exit via air_dodge_active.
                self.vel.update(dir_x * DODGE_AIR_SPEED, 0)
                self.air_dodge_active = True
            self.spot_dodge_shield_held = False
