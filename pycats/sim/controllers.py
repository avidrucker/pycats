"""Deterministic input controllers for headless battles.

These are NOT in-game AI — they are scripted, RNG-free policies used to drive
demo/benchmark battles and to *generate* fixed input timelines. Capture a
controller's `emitted` frames and replay that list through both backends to keep
parity tests a clean byte-identical comparison on identical inputs.
"""
from __future__ import annotations

from ..core.input import InputFrame


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

    def __init__(self, attacker_num=1):
        self.attacker_num = attacker_num
        self._prev = set()
        self._f = 0
        self.emitted = []  # recorded InputFrames, for freezing into a fixed list

    def decide(self, a, t, frame) -> set:
        """Return the set of keys to HOLD this frame. `a` is this controller's
        player, `t` the other. Override in an archetype."""
        raise NotImplementedError

    def __call__(self, p1, p2, frame):
        a, t = (p1, p2) if self.attacker_num == 1 else (p2, p1)
        held = self.decide(a, t, frame)
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
                 attack_range=45, safe_x=(110, 850), drop_threshold=20):
        super().__init__(attacker_num)
        # safe_x is the range the attacker will walk to — the thick platform's
        # standing extent (x[80..880]) minus a body-margin. Widened from the old
        # 770 for #44: realistic knockback decay no longer launches the target
        # off-stage in one hit, so it can linger near the platform edges; the bot
        # must be able to follow it there to keep racking up damage to a KO.
        self.attack_period = attack_period
        self.standoff = standoff          # desired horizontal gap (stand beside, not on top of)
        self.attack_range = attack_range
        self.safe_x = safe_x
        # Task 5 retune: drop_threshold — if attacker is grounded and target is
        # this many pixels *below* (positive dy), hold 'down' to drop through any
        # thin platform the attacker is standing on so they reach the target's
        # level.  Purely a policy parameter; 0 disables the behaviour.
        self.drop_threshold = drop_threshold
        self._last_attack = -10_000

    def decide(self, a, t, frame) -> set:
        keys = a.controls
        held = set()

        if t.is_alive:
            dx = t.rect.centerx - a.rect.centerx
            dy = t.rect.centery - a.rect.centery
            adx = abs(dx)
            cx = a.rect.centerx
            lo, hi = self.safe_x
            toward = keys["right"] if dx > 0 else keys["left"]
            away = keys["left"] if dx > 0 else keys["right"]
            # Maintain a standoff gap: close in if too far, back off if stacked
            # on top of the target (adx ~ 0 would otherwise deadlock).
            move = None
            if adx > self.standoff + 8:
                move = toward
            elif adx < self.standoff - 8:
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
            if dy < -30 and a.on_ground and adx < 120:
                held.add(keys["up"])
            # Drop through thin platforms when target is below.  Pressing 'down'
            # while grounded on a thin platform causes solve_vertical to let the
            # player fall through it, putting them on the same y-level as the
            # target.  Only activate when dy exceeds the policy threshold so the
            # bot doesn't perpetually fall through the main platform.
            if self.drop_threshold > 0 and dy > self.drop_threshold and a.on_ground:
                held.add(keys["down"])
            # Attack on a cadence when at standoff range and roughly level. The
            # vertical tolerance is wide enough to keep engaging after knockback
            # nudges the target a platform up/down, avoiding a positional
            # deadlock under the post-startup hitbox timing.
            in_range = (self.standoff - 18) <= adx <= self.attack_range and abs(dy) < 60
            if in_range and (self._f - self._last_attack) >= self.attack_period:
                held.add(keys["attack"])
                self._last_attack = self._f

        return held


# Back-compat alias: the original single controller was the attacker policy.
ChaseController = AttackerController


class IdlerController(BaseController):
    """A deterministic baseline opponent. By default a true no-op (emits nothing),
    so it stands in for an idle player transparently. Optionally performs minimal
    RNG-free activity: with `shield_period > 0`, holds `shield` for `shield_hold`
    frames at the start of each `shield_period`-frame cycle. Position-independent.
    """

    def __init__(self, attacker_num=1, shield_period=0, shield_hold=0):
        super().__init__(attacker_num)
        self.shield_period = shield_period
        self.shield_hold = shield_hold

    def decide(self, a, t, frame) -> set:
        if self.shield_period > 0 and (self._f % self.shield_period) < self.shield_hold:
            return {a.controls["shield"]}
        return set()
