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
pygame-free, boundary), enforces its contracts, and runs the rules. It keeps an
`owner` back-reference (the established `Tail(self)` pattern) through which the
rules reach the few things that remain Player's: the `_clock`/`engine`/`tail`
subsystems and `char_name`.

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

from ..config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    INITIAL_LIVES,
    SHIELD_MAX_HP,
    BLAST_PADDING,
    RESPAWN_DELAY_FRAMES,
    DODGE_TIME,
    DODGE_SPEED,
    DODGE_AIR_SPEED,
    WAVEDASH_ANGLE_DEG,
    WAVEDASH_LANDING_LAG,
    KNOCKBACK_LAUNCH_FACTOR,
    CROUCH_CANCEL_FACTOR,
    SAKURAI_ANGLE_CODE,
    GETUP_ROLL_FRAMES,
    GETUP_ROLL_SPEED,
    KNOCKDOWN_VY_THRESHOLD,
    KNOCKDOWN_PRONE_FRAMES,
)
from ..combat.knockback import (
    knockback, hitstun_frames, hitlag_frames, sakurai_angle, set_knockback,
)
from ..combat.shield import shieldstun_frames
from ..combat.shield import shield_break_stun_frames


class Fighter:
    def __init__(self, owner, x, y, facing_right, fighter_data):
        # Back-reference to the owning Player (the pygame Sprite adapter). Since
        # 6b-3b the rules reach only Player's wiring through it — `owner._clock`,
        # `owner.engine`, `owner.tail` (and `owner.char_name` in debug comments);
        # all the simulation state is now Fighter's own.
        self.owner = owner

        # ---------- per-character stats from FighterData (#123/#126) ----------
        # weight feeds the knockback formula (#40); the movement constants are
        # read per-fighter by the physics/input layer. All default (in
        # FighterData) to the config globals, so the default cat is unchanged.
        self.weight = fighter_data.weight
        self.gravity = fighter_data.gravity
        self.max_fall_speed = fighter_data.max_fall_speed
        self.move_speed = fighter_data.move_speed
        self.jump_vel = fighter_data.jump_vel
        self.max_jumps = fighter_data.max_jumps

        # ---------- crouch geometry (#124) ----------
        # stand_size is the body's full standing box; crouch_size/_hurtbox are
        # the per-cat crouch geometry (None = this fighter can't crouch).
        # Per-fighter stand_size (#275): a small archetype (Kirby) overrides it;
        # None falls back to the global owner.SIZE (config.PLAYER_SIZE).
        self.stand_size = tuple(fighter_data.stand_size or (owner.SIZE[0], owner.SIZE[1]))
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
        self.hurt_timer = 0
        self.stun_timer = 0
        self.prone_timer = 0  # knockdown/getup window (#13); prone while > 0
        self.getup_roll_timer = 0  # getup-roll duration + intangibility window (#146)
        self.getup_attack_timer = 0  # wake-up attack duration out of prone (#225)
        self.landing_lag_timer = 0  # post-waveland action lock (#202); locked while > 0
        self.grabbed_ledge = None  # the Ledge being held, or None (#14); its presence
        # is the authoritative "am I hanging" signal the statechart reads.
        self.ledge_hang_timer = 0  # hang timeout + intangibility window (#14)
        self.ledge_regrab_lockout_timer = 0  # post-release regrab suppression (#14)
        self.land_impact_vy = 0.0  # downward speed at last ground contact (#145)
        self.hitlag_timer = 0  # freeze frames on a clean hit (#138); both fighters
        self.shieldstun_timer = 0  # locked-in-shield frames after a block (#140)
        # attack_timer is a derived property over owner._clock (#71).
        self.invulnerable_timer = 0  # invulnerability mid-dodge, post-respawn, or while ledge grabbing
        self.jumps_remaining = self.max_jumps
        self.air_dodge_ok = True  # players can only air dodge once per sustained jump/fall, until they land
        self.invulnerable = False  # dodging / post-hit / respawn / ledge-grab invulnerability
        self.done_attacking = True  # used to determine when the player is done attacking

        # ---------- shield / dodge flags ----------
        self.shield_attempting = False  # shield visual helper
        self.drop_platform = None  # platform drop-through reference
        self.dodge_blocked_by_edge = False  # current dodge is blocked by an edge
        self.spot_dodge_shield_held = False  # shield was held during a spot dodge
        # PM-faithful air dodge (#184): True while an air dodge is in progress, so the
        # statechart routes the dodge's exit to `helpless` (not `fall`); cleared on land.
        self.air_dodge_active = False
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

    # ----------- per-frame timers ------------
    def tick_timers(self) -> None:
        """Advance the fighter's *stateless* per-frame timers (S1/#273).

        These decrement with no transition side-effect, so the aggregate owns the
        tick (was inline in `Player.update()`, N2). The transition-coupled timers
        (prone/getup_roll/getup_attack/ledge_hang/dodge/respawn) and `hitlag`
        (bound to the freeze early-return) stay in `Player.update()` until later
        slices (#264 S4/S5)."""
        for name in ("hurt_timer", "stun_timer", "landing_lag_timer",
                     "ledge_regrab_lockout_timer", "shieldstun_timer"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, v - 1)

    # ----------- hit processing ------------
    def receive_hit(self, atk, is_crouching=False):
        """Called by combat system when this player is struck.

        `is_crouching` is passed in by `combat.process_hits` (#283/S2) — the domain
        rule no longer reaches up into the adapter's FSM state label. Defaults
        False so the "no `.state` ⇒ not crouching" contract holds for minimal
        combat stand-ins and non-crouch callers."""
        self.record_hit_received()  # Track that this player was hit
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
                kb = set_knockback(wdsk, self.weight,
                                   atk.base_knockback, atk.knockback_growth)
            else:
                kb = knockback(self.percent, atk.damage, self.weight,
                               atk.base_knockback, atk.knockback_growth)
            # Crouch-cancel (#135): a hit taken while in the `crouch` state (#124)
            # has its knockback scaled down by CROUCH_CANCEL_FACTOR (0.67x, PM)
            # before launch + hitstun are derived — crouch as a defensive tool.
            # Hitlag scaling (the "c" multiplier) stays deferred this slice.
            if is_crouching:
                kb *= CROUCH_CANCEL_FACTOR
            self.hurt_timer = hitstun_frames(kb)
            # (the red hurt-flash is now render-time: render_battle.body_tint #75)
            direction = (
                1 if atk.owner.fighter.facing_right else -1
            )  # the direction of the attack
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

    def _handle_landing(self, was_airborne: bool):
        if self.on_ground and was_airborne:
            self.jumps_remaining = self.max_jumps  # reset jumps when landing
            self.air_dodge_ok = True  # reset air dodge availability
            self.air_dodge_active = False  # landing ends helpless/special-fall (#184)

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
                self.invulnerable = False
            # Auto landing-velocity knockdown (#145): landing hard while still in
            # hitstun (tumble) without teching forces `prone` (#13). The hurt-timer
            # gate is what separates this from a normal jump landing (same impact
            # speed, but hurt_timer == 0). Clear hurt_timer so the getup exit
            # (prone -> idle when prone_timer hits 0) doesn't pop back into hurt.
            if (self.hurt_timer > 0
                    and self.land_impact_vy >= KNOCKDOWN_VY_THRESHOLD):
                self.hurt_timer = 0
                self.owner.force_prone(KNOCKDOWN_PRONE_FRAMES)

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
        # print(f"PLAYER KO: {self.owner.char_name} fell off and lost a life! (lives: {self.lives-1})")
        # Decrement; the lives>=0 invariant (#54) is now enforced once, in the
        # Fighter.lives setter (#81), instead of clamped here. This keeps a
        # zero-life player from going negative if the is_alive / respawn gates
        # ever let a re-KO through.
        self.lives -= 1
        self.is_alive = False
        self.respawn_timer = RESPAWN_DELAY_FRAMES
        # hide sprite off-screen
        self.rect.center = (-1000, -1000)
        self.vel.update(0, 0)
        self.owner.engine.force("ko")

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
        self.jumps_remaining = self.max_jumps
        self.air_dodge_ok = True
        self.air_dodge_active = False  # clear helpless/special-fall on respawn (#184)
        self.wavedash_armed = False  # nor a pending waveland (#202)
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
        self.landing_lag_timer = 0  # don't carry a waveland lock across a KO/respawn (#202)
        # Ledge-hang (#14): free the held edge and clear the hang so a KO/respawn or
        # match reset can't leave a fighter pinned or an edge permanently occupied.
        if self.grabbed_ledge is not None:
            self.grabbed_ledge.occupied_by = None
        self.grabbed_ledge = None
        self.ledge_hang_timer = 0
        self.ledge_regrab_lockout_timer = 0
        self.hitlag_timer = 0  # don't carry a freeze across a KO/respawn (#138)
        self.shieldstun_timer = 0  # nor a block-stun (#140)
        self.invulnerable_timer = 0
        self.invulnerable = False
        self.spot_dodge_shield_held = False
        self.dodge_blocked_by_edge = False
        self.owner._clock.reset()  # attack_timer/current_move/move_frame all derive from this
        self.done_attacking = True
        # (visual reset is render-time now: render_battle.body_tint #75)
        # Re-initialize the tail to its rest layout at the spawn point (#41): the
        # Verlet tail keeps live position/velocity and freezes wherever the cat
        # flew off-screen, so without this the chain whips in from there. facing
        # and rect are set above, so the layout is correct.
        self.owner.tail.reset()

    def _respawn(self):
        #### TODO: implement temporary respawn invulnerability
        self.reset_to_spawn()

    # state starters ----------------------------
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
        or +1 (right). Reuses the same invulnerable/timer machinery as the dodge.
        """
        self.getup_roll_timer = GETUP_ROLL_FRAMES
        self.invulnerable = True
        self.invulnerable_timer = GETUP_ROLL_FRAMES
        self.vel.update(direction * GETUP_ROLL_SPEED, 0)

    def _start_dodge(self, dir_x: int, dir_y: int = 0) -> None:
        self.dodge_timer = DODGE_TIME
        self.invulnerable = True
        self.dodge_blocked_by_edge = False  # Reset edge blocking flag
        self.wavedash_armed = False  # only a diagonal-down air dodge re-arms it (below)

        # Only set spot_dodge_shield_held for ground-based spot dodges (not air dodges)
        if dir_x == 0 and self.on_ground:
            # Ground spot dodge - no movement, special thin platform protection
            self.vel.update(0, 0)  # No movement for ground spot dodge
            self.spot_dodge_shield_held = True
            # debugging
            # print(f"GROUND SPOT DODGE START: {self.owner.char_name} ground spot dodge initiated")
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
                self.vel.update(dir_x * DODGE_AIR_SPEED * math.cos(ang),
                                DODGE_AIR_SPEED * math.sin(ang))
                self.air_dodge_active = True
                self.wavedash_armed = True
            else:
                # Directional air dodge (PM/Melee, #184): SET (replace) velocity to a
                # fixed burst in the stick direction and zero vertical — not Brawl-style
                # additive/preserve. Routes to `helpless` on exit via air_dodge_active.
                self.vel.update(dir_x * DODGE_AIR_SPEED, 0)
                self.air_dodge_active = True
            self.spot_dodge_shield_held = False
