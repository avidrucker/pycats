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
    MAX_JUMPS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    INITIAL_LIVES,
    SHIELD_MAX_HP,
    BLAST_PADDING,
    RESPAWN_DELAY_FRAMES,
    DODGE_TIME,
    DODGE_SPEED,
    KNOCKBACK_LAUNCH_FACTOR,
)
from ..combat.knockback import knockback, hitstun_frames
from ..combat.shield import shield_break_stun_frames


class Fighter:
    def __init__(self, owner, x, y, facing_right, weight):
        # Back-reference to the owning Player (the pygame Sprite adapter). Since
        # 6b-3b the rules reach only Player's wiring through it — `owner._clock`,
        # `owner.engine`, `owner.tail` (and `owner.char_name` in debug comments);
        # all the simulation state is now Fighter's own.
        self.owner = owner

        self.weight = weight  # fighter weight; feeds the knockback formula (#40)

        # ---------- kinematics (#84 / 6b-3a) ----------
        # The authoritative body box + velocity now live on the domain object;
        # Player exposes them as delegating get/set properties (pygame value
        # types, kept per the #69 Sprite-free-not-pygame-free boundary).
        self.rect = pygame.Rect(0, 0, owner.SIZE[0], owner.SIZE[1])
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
        # attack_timer is a derived property over owner._clock (#71).
        self.invulnerable_timer = 0  # invulnerability mid-dodge, post-respawn, or while ledge grabbing
        self.jumps_remaining = MAX_JUMPS
        self.air_dodge_ok = True  # players can only air dodge once per sustained jump/fall, until they land
        self.invulnerable = False  # dodging / post-hit / respawn / ledge-grab invulnerability
        self.done_attacking = True  # used to determine when the player is done attacking

        # ---------- shield / dodge flags ----------
        self.shield_attempting = False  # shield visual helper
        self.drop_platform = None  # platform drop-through reference
        self.dodge_blocked_by_edge = False  # current dodge is blocked by an edge
        self.spot_dodge_shield_held = False  # shield was held during a spot dodge

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

    # ----------- hit processing ------------
    def receive_hit(self, atk):
        """Called by combat system when this player is struck."""
        self.record_hit_received()  # Track that this player was hit
        if self.shield_attempting and self.shield_hp > 0:
            self.shield_hp = self.shield_hp - atk.damage  # setter clamps >= 0
            if self.shield_hp == 0:
                self._start_stun()
        #### TODO: elif dodging
        else:
            # Phase 1 (#40): authentic Brawl/PM knockback + hitstun-from-knockback.
            self.percent += atk.damage
            # Credit the percent damage to both sides for the win-screen stats
            # (#98). Only the non-shield path counts — a shielded hit deals shield
            # damage, not percent, so it is correctly excluded here.
            self.damage_taken += atk.damage
            atk.owner.record_damage_given(atk.damage)
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
        #### TODO: implement spawning animation
        #### TODO: implement respawn visible count-down
        self.reset_to_spawn()

    # state starters ----------------------------
    def _start_stun(self) -> None:
        # Shield-break "dizzy" (#12): damage-scaled duration (Melee/PM). The
        # engine flips state -> "stun" on the next tick (the chart/FSM `stun`
        # entry guards on stun_timer > 0); input is locked while the timer runs.
        self.stun_timer = shield_break_stun_frames(self.percent)
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
            # print(f"GROUND SPOT DODGE START: {self.owner.char_name} ground spot dodge initiated")
        elif dir_x == 0 and not self.on_ground:
            # Air dodge - preserve Y velocity, no horizontal movement
            # self.vel.x = 0  # Only reset horizontal velocity for air dodge
            self.spot_dodge_shield_held = False
            # debugging
            # print(f"AIR DODGE START: {self.owner.char_name} air dodge initiated (preserving Y velocity)")
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
