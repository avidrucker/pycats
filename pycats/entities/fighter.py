"""Fighter — the Sprite-free domain aggregate for a fighter's combat state.

D1 slice 6b-1 (#81): the first courier slice of the `Player` → `Fighter`/`Sprite`
split scoped on #69. This slice extracts the combat *state* + *stats* and names
the three invariants the audit flagged (S3); the *rules* (`receive_hit`/`_ko`/…)
and `rect`/`vel` follow in 6b-2/6b-3.

`Fighter` is deliberately NOT a `pygame.sprite.Sprite` — it holds plain values
and enforces their contracts. `Player` composes one (`self.fighter`) and exposes
delegating properties so every existing reader/writer is unchanged.

Invariants (S3 — previously emergent, now enforced once, at the setter, instead
of re-derived at each mutation site):
- ``percent >= 0``                 (had NO guard before — first enforcement)
- ``0 <= shield_hp <= SHIELD_MAX_HP`` (clamps were scattered across player.py)
- ``lives >= 0``                   (was only clamped at the `_ko` site, #54)

The setters clamp to ranges that already held in practice, so behaviour is
preserved (parity byte-identical, goldens unchanged); they only remove the
*possibility* of a future edit silently violating a contract.
"""
from __future__ import annotations

from ..config import SHIELD_MAX_HP, INITIAL_LIVES


class Fighter:
    def __init__(self):
        # ---------- combat state (invariant-enforced via the setters) ----------
        self._percent = 0
        self._shield_hp = SHIELD_MAX_HP
        self._lives = INITIAL_LIVES

        # ---------- game statistics ----------
        self.attacks_made = 0  # Total attacks initiated
        self.hits_landed = 0  # Successful hits on opponent
        self.suicides = 0  # Deaths without being hit (self-inflicted)
        self.was_hit_before_ko = False  # Track if last KO was from being hit

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
