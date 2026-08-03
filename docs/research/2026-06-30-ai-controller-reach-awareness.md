# AI controller reach-awareness — real per-character/per-move reach vs the hardcoded `attack_range=45` (#285)

> Research findings (#285, surfaced scoping #277; AI umbrella #250). The
> `AttackerController` gates every attack/spacing decision on a single hardcoded
> `attack_range=45`, but fighters have **genuinely asymmetric reach** — per
> character *and* per move. This doc catalogues the real reach, maps the seam to
> derive it, re-evaluates #277's "symmetric proxy" premise, and gives an ordered
> DEV recommendation. **Findings + spec only — no controller code this ticket.**
>
> Code grounded against `pycats/sim/controllers.py`, `pycats/entities/attack.py`,
> `pycats/combat/geometry.py`, and `pycats/characters/{nalio,birky,narz,default}_cat.py`
> at HEAD. Reach numbers are computed directly from the live `FighterData` (script
> in the appendix), not eyeballed. Date: 2026-06-30. Agent: FIG. Area: `area:combat`.

## TL;DR

- **Reach is real and asymmetric.** Effective ground reach (measured center-to-center,
  the same axis the controller's `attack_range` uses) spans **18–64 px** across the
  three authored fighters — a **46 px** spread. The flat `45` fits *no* character
  well.
- **Per-move variance dominates per-character variance.** Within a single fighter
  (Narz) ground reach runs 18 → 64 px (a 46 px spread); across fighters the *committed*
  move (forward-tilt, post-#292) runs 52 → 64 px (a 12 px spread). So *which move*
  matters more than *which cat*.
- **No new plumbing is needed to derive reach.** The controller's `decide(a, t, …)`
  already receives both `Player`s, and each exposes its real `.fighter_data.moves`
  and body width. Reach is computable at decision time from data already in hand.
- **The cleanest first step is per-committed-move reach.** Since #292, a leveled bot
  commits the forward-tilt every attack, so reading that one move's reach from
  `a.fighter_data.moves["ftilt"]` gives per-move accuracy *without* needing the fuller
  move-selection maturity of #142/#143.
- **#285 sharpens #277 but does not hard-block it.** #277 deliberately ships a
  symmetric `shield_threat_range` proxy and defers real reach as "future polish". The
  finding here — reach is *not* symmetric — means the proxy is a coarse fit; the
  recommendation is a small reach-derivation DEV ticket that #277 can then consume.
- **Golden-safe path exists.** Gate reach-derivation behind a level knob exactly like
  `reactive_shield`/`whiff_punish`/`enabled_moves`; the level-less default keeps
  `attack_range=45`, so `tests/golden/` stays byte-identical.

## Q1 — Reach catalogue

**Metric.** For each move, `tip = max(dx + r)` over its hitboxes (the forward-most
point from the fighter's top-left origin, facing right — see `resolve_circle`,
`cx = origin_x + dx` when facing right). Converted to a **center-relative reach**
`reach_ctr = tip − width/2`, because the controller compares against `adx =
|t.rect.centerx − a.rect.centerx|` (center-to-center). All bodies are 40 px wide
(half-width 20) today, so `reach_ctr = tip − 20`.

Ground moves (the ones spacing/`attack_range` act on), reach-from-center in px:

| Fighter  | jab | ftilt | utilt | dtilt | attack¹ | fireball | **ground max** | **ground min** |
|----------|----:|------:|------:|------:|--------:|---------:|---------------:|---------------:|
| Nalio    |  53 |    58 |    27 |  58²  |   58²   |    49    |         **58** |         **27** |
| Birky    |  35 |    52 |    40 |  47²  |   47²   |    —     |         **52** |         **35** |
| Narz     |  48 |    64 |    18 |    56 |    38   |    —     |         **64** |         **18** |
| default  |   — |     — |     — |     — |    38   |    —     |         **38** |         **38** |
| **controller** | | | | | | | **flat `attack_range=45` for everyone** | |

¹ `"attack"` is the neutral-ground alias key (`move_select.resolve_move_key` fallback).
For Nalio/Birky it maps onto the down-tilt; Narz authors a distinct `"attack"`.
² Nalio's/Birky's `"attack"` slot *is* their down-tilt, so those two columns coincide.

Aerials, for reference (reach-from-center, px): Nalio `fair 52 / uair 21 / dair 27 /
nair 25 / bair −3`; Birky `fair 60 / uair 31 / dair 31 / nair 22 / bair 10`; Narz
`fair 62 / nair 52 / uair 16 / dair 18 / bair −48`. (Negative = the box sits behind
the fighter's center — a back-air.)

**Effective connect distance is a little longer than `reach_ctr`.** To land, the
attacker's tip must reach the opponent's near hurtbox edge, not its center. The
opponent's hurtbox adds roughly its own half-extent — Nalio/Birky hurtbox circles are
`r≈13–14` centered near `dx=20`, so add ~13 px. So *connect gap ≈ `reach_ctr` +
opponent_hurtbox_half*. That correction is itself **per-character** (a wide body is
easier to reach), which is a second, independent reason the controller wants the
*opponent's* data, not just its own.

### What the flat 45 actually gets wrong

- **It under-uses the committed move's range.** Since #292 a leveled bot throws the
  forward-tilt, whose reach is **52–64** — all *above* 45. The bot only presses attack
  once the gap is `≤ 45`, so it walks 7–19 px closer than it needs to, surrendering the
  spacing it could hold and stepping into the opponent's counter-range.
- **It would whiff the short moves.** Every fighter has ground moves *below* 45 —
  Birky's jab (35), every up-tilt (18–40), Narz's `attack` (38). A bot that threw one
  of those at a 45 px gap would fall short. Today this is masked only because the
  committed move happens to be the long forward-tilt.
- **It cannot express footsies (the #277 goal).** "Stand just outside the opponent's
  reach" needs the *opponent's* real reach; a flat symmetric 45 mis-sizes that band by
  up to ±19 px depending on matchup and move.

## Q2 — Derivation seam

**Finding: the data is already at the decision site — no constructor plumbing is
required.**

- `build_players(p1_char, p2_char)` (`sim/runner.py`) loads each archetype's
  `FighterData` via `load_fighter_data` and injects it into the `Player`
  (`char_name` stays `"P1"/"P2"`, but `fighter_data` is the *real* archetype data).
- `AttackerController.decide(self, a, t, frame, attacks)` receives both `Player`s.
  Verified live: `a.fighter_data.moves` and `t.fighter_data.moves` are full move
  dicts, and `a.rect.width` / `t.rect.width` give the bodies. So a `reach_of(player,
  move_key)` helper — `max(dx+r) − width/2` over `player.fighter_data.moves[key]` — is
  computable for **self and opponent** every frame, from objects already in scope.

Three derivation options, in increasing precision (and dependency):

1. **Per-committed-move (recommended first).** Compute the reach of the single move the
   bot actually throws. Post-#292 that is the forward-tilt for a tilt-enabled leveled
   bot, so `reach_of(a, "ftilt")`. Per-move-accurate today because there is effectively
   one committed ground move; needs nothing from #142/#143.
2. **Per-character max/representative.** Precompute one number per fighter (e.g. its
   committed move, or a capped max) at controller construction — `cpu_controllers`
   would pass the char, or the controller reads `a.fighter_data` on first frame.
   Simplest state, but a plain *max* invites over-commit (standing at 58 then throwing a
   27-reach up-tilt whiffs), so if this route is taken it should key off the
   *committed* move, not the raw max.
3. **Full per-move, opponent-aware (later).** Once move-selection (#142/#143) lets the
   bot *choose* among jab/tilt/aerial, pick per-frame the move whose reach fits the
   current gap, and size the retreat band off `reach_of(t, t's committed move)`. This is
   the footsies end-state; gated on move-selection maturity.

## Q4 — Per-move vs per-character

**Per-move variance is the larger effect**, so a single per-character `attack_range` is
not enough for the footsies end-state:

- Within Narz, ground reach spans **18 → 64** (46 px).
- Across fighters, the *committed* forward-tilt spans **52 → 64** (12 px).

But there is a pragmatic shortcut: **today there is effectively one committed ground
move** (the forward-tilt, since #292), so *per-committed-move* reach captures the
per-move accuracy that matters *now* with none of the move-selection machinery. Full
per-move selection is a #142/#143-gated follow-up, not a prerequisite.

## Q3 — Does it unblock #277? (re-evaluation)

**#285 sharpens #277; it does not hard-block it — and #277's own "symmetric proxy"
premise is the thing this finding corrects.**

- #277's design deliberately approximates opponent reach with the symmetric
  `shield_threat_range` band and lists "per-archetype reach data" under *Out of scope
  (future polish)*. So #277 *can* ship on the proxy.
- The finding here is that reach is **not** symmetric (18–64 px), so the proxy is a
  coarse fit — acceptable for #277's *secondary* retreat behavior (a rough danger
  band), but weak for anything sharper.
- Crucially, #277's own **primary** value ("approach-when-safe so #274's whiff-punish
  lands") depends on the **bot's own** committed-move reach — which is derivable *now*
  (Q2, option 1) and is more accurate than the flat 45 the approach currently targets.

**Recommendation for #277:** unblock it, but land a small reach-derivation DEV first
(below) so #277's approach targets the bot's real committed reach instead of 45; keep
the symmetric band for the secondary retreat for now, with opponent-reach substitution
as the documented follow-up. Update #277's blocked-reasoning to "was: blocked pending
#285 reach findings; now: proceed on real own-reach + symmetric retreat proxy, per
`docs/research/2026-06-30-ai-controller-reach-awareness.md`."

## Q5 — Golden-safety

Same pattern as every prior leveled-AI change (#232/#238/#248/#254/#274/#292): the
new behavior rides a **level-gated knob**, and the **level-less default is byte-
identical**.

- Add an optional knob (e.g. `reach_aware: bool`, default `False`; or an explicit
  `attack_range=None` sentinel meaning "derive"). Default `AttackerController()` keeps
  the literal `attack_range=45`.
- `level_params` turns it on for reactive levels (5/7/9) alongside `reactive_shield` /
  `whiff_punish`; low/default stay on the constant.
- `tests/golden/` is driven by the level-less default path, so it stays clean. Leveled
  behavior has **no** frozen golden (it is asserted behaviorally — see
  `tests/test_bot_match_resolves.py`, `tests/test_cpu_difficulty.py`), so the change
  lands with its *own* able-to-fail regression (a reach-aware bot commits from a
  character-appropriate gap; the default does not), not a golden update.

## Ordered DEV recommendation

1. **DEV-A — derive the attacker's own reach from its committed move** *(small, do
   first)*. Replace the flat `attack_range=45` with `reach_of(a, committed_move_key)`
   (`"ftilt"` post-#292) when a level knob is on; default stays 45. Highest ROI,
   composes directly with #292, needs no new plumbing (Q2 option 1). Regression:
   reach-aware bot's `in_range` gate keys off ~52–64 not 45; default byte-identical.
2. **DEV-B — feed opponent reach into #277's spacing** *(unblocks/sharpens #277)*.
   Size #277's retreat band off `reach_of(t, …)` instead of the symmetric
   `shield_threat_range` proxy; keep the proxy as the fallback for characters without
   authored moves. Lands as part of, or immediately after, #277.
3. **DEV-C — full per-move reach** *(later, gated on #142/#143)*. When the bot
   deliberately selects among jab/tilt/aerial, choose per-frame the move whose reach
   fits the current gap. This is the footsies end-state; deferred until move-selection
   is richer.

## Non-goals (unchanged from the ticket)

- No reach-aware controller **code** this ticket — spec/findings only.
- No per-archetype balance tuning (#117) or move-selection logic (#142/#143).
- No change to the difficulty ladder (#231/#148).

## Appendix — reproduction

Reach numbers computed directly from the live `FighterData`:

```python
from pycats.combat.data import load_fighter_data
from pycats.config import PLAYER_SIZE

def reach_ctr(mv, width):
    return max(hb.circle.dx + hb.circle.r for hb in mv.hitboxes) - width / 2

for ch in ("nalio", "birky", "narz", "default"):
    fd = load_fighter_data(ch)
    w = (fd.stand_size or PLAYER_SIZE)[0]
    ground = {mv.name: reach_ctr(mv, w) for mv in fd.moves.values() if not mv.in_air}
    print(ch, ground)
```

## Cross-refs

Surfaced scoping #277 (reactive spacing — corrects its "no asymmetry" premise); AI
umbrella #250; decision-model research #251
(`docs/research/2026-06-30-cpu-ai-decision-model.md`); difficulty ladder #148/#231;
move-selection seam #142/#143; the #292 fix that makes the forward-tilt the committed
move; controllers `pycats/sim/controllers.py`; characters
`pycats/characters/{nalio,birky,narz,default}_cat.py`; geometry
`pycats/combat/geometry.resolve_circle`. Orientation map #185.
