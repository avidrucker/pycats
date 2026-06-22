"""Deterministic input controllers for headless battles.

These are NOT in-game AI — they are scripted, RNG-free policies used to drive
demo/benchmark battles and to *generate* fixed input timelines. Capture a
controller's `emitted` frames and replay that list through both backends to keep
parity tests a clean byte-identical comparison on identical inputs.
"""
from __future__ import annotations

from ..core.input import InputFrame


class ChaseController:
    """Drives `attacker` to hunt down `target` and attack; `target` gets no input.

    Deterministic: decisions depend only on live positions (no randomness), so a
    given backend produces the same battle every run. Movement keys are held;
    jump/attack are pulsed (one frame) so the game sees fresh key presses.
    """

    def __init__(self, attacker_num=1, attack_period=12, standoff=40,
                 attack_range=58, safe_x=(110, 820)):
        # attacker_num is 1 or 2; the other player is the (idle) target. Player
        # refs are resolved per-frame from the (p1, p2) passed to __call__, so a
        # ChaseController can be built before run_battle creates the players.
        self.attacker_num = attacker_num
        self.attack_period = attack_period
        self.standoff = standoff          # desired horizontal gap (stand beside, not on top of)
        self.attack_range = attack_range
        self.safe_x = safe_x
        self._prev = set()
        self._last_attack = -10_000
        self._f = 0
        self.emitted = []  # recorded InputFrames, for freezing into a fixed list

    def __call__(self, p1, p2, frame):
        a, t = (p1, p2) if self.attacker_num == 1 else (p2, p1)
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
            # Attack on a cadence when at standoff range and roughly level. The
            # vertical tolerance is wide enough to keep engaging after knockback
            # nudges the target a platform up/down, avoiding a positional
            # deadlock under the post-startup hitbox timing.
            in_range = (self.standoff - 18) <= adx <= self.attack_range and abs(dy) < 60
            if in_range and (self._f - self._last_attack) >= self.attack_period:
                held.add(keys["attack"])
                self._last_attack = self._f

        pressed = held - self._prev
        released = self._prev - held
        self._prev = held
        self._f += 1
        fi = InputFrame(held=set(held), pressed=set(pressed), released=set(released))
        self.emitted.append(fi)
        return fi
