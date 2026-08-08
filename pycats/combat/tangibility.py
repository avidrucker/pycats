"""The 3-way immunity state a defender presents to an incoming hit (#802).

Ratified by decision **#784**; the mechanics are grounded in the #797 findings
(``docs/research/2026-07-20-pm-invincible-hitlag-findings.md``). Three states,
distinguished by the #774 §1.1 test *does the attack connect?*:

- ``TANGIBLE``   — normal; the hit connects and resolves in full.
- ``INTANGIBLE`` — the attack *passes through*: hurtbox detection is skipped, no hit
  registers, and the attacker takes **no** hitlag (nobody freezes). This is today's
  dodge / ledge-grab / getup immunity.
- ``INVINCIBLE`` — the attack *connects* but the defender is "otherwise unaffected":
  the attacker takes hitlag (freezes), while the defender's damage, knockback,
  hitstun, and hitlag are all zeroed. This is the respawn-descent window (#506).

Precedence is **INTANGIBLE > INVINCIBLE > TANGIBLE** — a fighter with both immunity
signals live resolves to the most protective, INTANGIBLE. Engine-confirmed in #797
(§Q4-bonus): meleelight ``hurtBoxStateUpdate`` runs the intangible check after the
invincible one, so intangible (pass-through) wins ties. The PM-3.6 step is
``[inference]`` — no PM primary exists; the strongest sources are the meleelight
Melee-engine reimplementation and series-universal SmashWiki, plus the PM 3.6
codeset carrying no override.
"""

from enum import Enum, auto


class Tangibility(Enum):
    """A defender's immunity state for the frame. See module docstring for the
    per-state hit-resolution behavior and the precedence order."""

    TANGIBLE = auto()
    INTANGIBLE = auto()
    INVINCIBLE = auto()


def resolve_tangibility(intangible: bool, invincible: bool) -> Tangibility:
    """The most-protective tangibility for the given active immunity signals.

    Precedence INTANGIBLE > INVINCIBLE > TANGIBLE (#784; #797 §Q4-bonus): if the
    intangible signal is live it wins outright (pass-through), else invincibility,
    else the default TANGIBLE.
    """
    if intangible:
        return Tangibility.INTANGIBLE
    if invincible:
        return Tangibility.INVINCIBLE
    return Tangibility.TANGIBLE
