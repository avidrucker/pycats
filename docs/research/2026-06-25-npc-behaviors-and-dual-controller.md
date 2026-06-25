# Findings: NPC behavior archetypes + dual-controller architecture (#48)

> A bounded research spike scoping the first child of **#47** (watchable real-time
> 2-NPC battle). Answers: (1) what PM/Brawl CPU AI actually does, (2) how to express
> three archetypes — **attacker / follower / idler** — as deterministic RNG-free
> policies, (3) the cleanest way to drive *both* players, (4) how much of
> `ChaseController` becomes the `attacker`. Read-only; deliverable is this doc +
> the #47 decomposition. **No production code.**
>
> Code grounded against `pycats/sim/controllers.py`, `pycats/sim/runner.py`,
> `watch.py`, `pycats/entities/player.py`, `pycats/core/input.py` (HEAD `2813364`).
> Source: SmashWiki [Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence).
> Date: 2026-06-25. Ticket #48; umbrella #47; relates #46, #24 (PM research), #38.

## 1. What PM/Brawl CPU AI actually does — and why we can't copy it

The honest headline: **authentic Smash CPU AI is the wrong model for pycats, by
construction.** It is stochastic and reaction-driven, while pycats controllers must
be RNG-free and position-driven to stay golden/parity-safe (`controllers.py` docstring;
[fidelity doc](./pm-framerate-fidelity.md)). What we borrow is the *taxonomy and the
behavioral tendencies*, not the decision mechanism.

What SmashWiki documents for Brawl CPUs (confidence noted):

| Behavior | Detail | Confidence |
|---|---|---|
| Difficulty is a **0–100 scalar** | Brawl Lv1=0, Lv3=21, Lv5=42, Lv9=100; labels Puny→Nasty | explicit |
| Difficulty governs **reaction speed + follow-through *probability*** | "how likely they are to follow through with a decision, as well as how fast they react" | explicit |
| Low-level → simple kit | weak jabs/tilts; "almost never using their shield… or at random times in Brawl" | explicit |
| High-level → richer kit | aerials, smashes, grabs; Lv9 **1-frame** reactions / perfect shield from Brawl on (Toomai) | explicit |
| **Recovery** scales with level | low CPUs "recover in a simple, predictable pattern with their up specials"; high CPUs alternate techniques | explicit |
| **Edge-guarding** is a known CPU *weakness* | first three games (incl. Brawl) "not avoiding or fighting off edge-guarders effectively" | explicit |
| Brawl CPUs **do not learn** | datamining found no AI state persisted to saves — behavior is a pure function of game state | explicit (myth-busted) |
| PM-specific CPU AI | **no authoritative source found** — PM is a Brawl mod; treat as Brawl-derived | gap (consistent w/ [fighter-states doc](./brawl-projectm-fighter-states.md) caveats) |

**The translation we adopt:** map the *difficulty scalar* and *behavioral tendency*
onto **deterministic parameters** (cadence period, standoff distance, attack range,
aggression = how far it commits) rather than probabilities. "Low-level = passive,
predictable, rarely shields" becomes our **idler**; "high-level = closes, pressures,
attacks on cadence" becomes our **attacker**; the spacing/shadowing tendency becomes
our **follower**. The reaction-time knob collapses to *zero* (we read exact positions
each frame) — which is fine: we are building demo/benchmark opponents, not a
difficulty ladder.

## 2. The three archetypes, distilled

Ranked by build value for #47 (a *watchable* 2-NPC fight wants two movers that
engage). Each is a pure function of the live `(attacker, target)` rects — no RNG,
no history beyond integer frame counters.

| Archetype | Intent (PM analogue) | Approach | Spacing | Attacks? | Extra state |
|---|---|---|---|---|---|
| **attacker** | high-level aggressor | close to `standoff` | hold gap; back off if stacked | yes, on `attack_period` cadence | `_last_attack` |
| **follower** | shadow/pressure, no commit | mirror target's horizontal motion | hold a **larger** shadow gap | no (or rare) | direction hysteresis |
| **idler** | low-level baseline opponent | none (hold position) | n/a | no | `_f` for optional periodic shield |

- **attacker** = today's `ChaseController` almost verbatim (see §5). It already
  closes distance, holds a standoff, chases an elevated target (jump) or a lower one
  (drop through thin platforms), clamps to `safe_x`, and attacks on a cadence when
  in range and roughly level.
- **follower** = attacker minus the attack, plus a wider `standoff` and a "match the
  target's last horizontal direction" rule so it trails rather than collides. This
  is the "pressure without committing" behavior; it makes a watchable spacing dance
  and is a safe sparring partner for tuning the attacker.
- **idler** = the baseline. Default: emit nothing (the current "other player" state).
  Optional deterministic flavor: hold `shield` for K frames every N frames, or take a
  single step on a fixed period — enough to prove dual-control end-to-end without
  introducing a real fight. Mirrors "low-level CPU, rarely/ randomly shields" but
  made periodic (deterministic) instead of random.

## 3. Deterministic expression in pycats (Q2)

All three fit the existing `controller(p1, p2, frame) -> InputFrame` protocol
unchanged. The mechanics that make this safe:

- **Edge-aware emission is already solved.** `ChaseController` tracks `_prev` and
  derives `pressed = held - _prev`, `released = _prev - held` per frame, and appends
  to `self.emitted` (`controllers.py:97-102`). Every archetype reuses this verbatim —
  it is the freeze-for-parity contract.
- **Per-player keymaps make outputs disjoint.** A controller emits only its own
  player's keycodes, pulled from `a.controls` (`controllers.py:48`). `Player._pressed`
  reads `self.controls[name] in key_set` (`player.py:480`), so a player ignores any
  keycode not in its own map. **This is the load-bearing invariant for §4.**
- **State is integer frames + positions only.** `_f`, `_last_attack`, `_prev` — all
  integers/sets; decisions branch on `dx/dy/adx` from rects. No floats-as-keys, no
  RNG, no wall-clock. Reproducible across runs and backends.

Sketch (illustrative — the real work is the #47 children, not this doc):

```python
class FollowerController(BaseController):
    def decide(self, a, t, frame):           # returns the held-key set
        held = set()
        if not t.is_alive:
            return held
        dx = t.rect.centerx - a.rect.centerx
        adx = abs(dx)
        if adx > self.shadow_gap + 8:         # trail at a wide gap
            held.add(a.controls["right"] if dx > 0 else a.controls["left"])
        # no attack key — pressure without committing
        return self._clamp_to_safe_x(a, held)
```

## 4. Dual-controller architecture (Q3) — recommended

**Recommendation: add a `controllers=(c1, c2)` parameter to `run_battle`, merge the
two emitted frames by set-union, and keep `controller=` as a back-compat alias.**
This is a small, low-risk change because the keycode namespaces are disjoint (§3).

Today `run_battle` calls **one** controller and applies its frame to *both* players;
the idle player is idle only because the active controller emits keycodes the idle
player's keymap ignores (`runner.py:104-109`). Generalizing:

```python
def run_battle(..., controller=None, controllers=None, ...):
    if controller is not None and controllers is None:
        controllers = (controller, None)      # back-compat: one driver, other idle
    ...
    for f in range(frames):
        if controllers is not None:
            # call BOTH on the SAME pre-update snapshot, THEN apply (determinism)
            frames_each = [c(p1, p2, f) if c else _empty_frame() for c in controllers]
            fi = InputFrame(
                held=set().union(*(x.held for x in frames_each)),
                pressed=set().union(*(x.pressed for x in frames_each)),
                released=set().union(*(x.released for x in frames_each)),
            )
        else:
            fi = frame_inputs[f] if f < len(frame_inputs) else _empty_frame()
        for p in players:
            p.update(fi, platforms, attacks)
        ...
```

Why this shape over a new "2-player controller protocol":

- **Minimal blast radius.** Existing `controller=ChaseController(1)` callers (watch
  `--match`, #46, goldens) are unchanged: `controllers=(c, None)` reproduces today's
  behavior exactly, since a 1-player controller already emits only its own keys.
- **Parity capture still works.** The **merged** `fi` per frame is exactly what
  `frame_inputs` replays. Recommend `run_battle` optionally collect the merged frames
  (e.g. return them, or accept an `emit_sink`) so a 2-NPC battle can be frozen into a
  fixed list and replayed byte-identically across backends — the same freeze trick the
  single-controller flow uses via `controller.emitted`. (Each controller's own
  `.emitted` also still records its half, if per-player capture is wanted.)
- **Order-independent + race-free.** `held/pressed/released` are sets → union is
  order-independent. Both controllers are called on the **frame-start snapshot before
  any `p.update`**, so neither sees the other's mutation mid-frame. No read-after-write
  hazard; fully deterministic.

**`watch.py`:** add a `--vs <archetype>` option that builds
`controllers=(ChaseController(1), <Archetype>Controller(2))` and runs the live
presenter — this is the literal "watchable 2-NPC battle" deliverable of #47.

## 5. Reuse: how much of `ChaseController` becomes `attacker` (Q4)

**~90%.** `ChaseController` *is* the attacker seed; the work is extraction, not
rewrite:

- **Keep as-is (becomes `AttackerController`):** the whole `__call__` body — standoff
  close/back-off, `safe_x` clamp, jump-toward-elevated, drop-through-to-lower, cadence
  attack. The `#46` robustness work (ledge-stall under realistic knockback, the widened
  `safe_x` from #44) lands here directly.
- **Extract into a `BaseController`:** the boilerplate shared by all three archetypes —
  the `(a, t)` attacker/target resolve from `attacker_num`, the `_prev`/`pressed`/
  `released` edge bookkeeping, the `self.emitted` capture, and a `_clamp_to_safe_x`
  helper. Archetypes override a single `decide(a, t, frame) -> set[int]` returning the
  held-key set; the base wraps it into the `InputFrame` + capture.
- **Net:** `attacker.decide` = current chase body; `follower.decide` = chase body minus
  the attack branch + wider gap + mirror rule; `idler.decide` = empty (+ optional
  periodic shield).

## 6. Determinism / parity risks (flagged)

1. **Keycode disjointness is load-bearing.** The union merge is only unambiguous
   because P1_KEYS ∩ P2_KEYS = ∅ and each controller emits from `a.controls`. A future
   controller that emitted the wrong player's keys would cross-talk. *Mitigation:* a
   `BaseController` that derives keys solely from its own `a.controls`, + a test
   asserting a P2 controller emits no P1 keycodes.
2. **Snapshot-before-apply ordering.** Both controllers must read the frame-start
   state; calling one after a `p.update` would leak state. The §4 shape enforces this
   (compute `frames_each` fully, then apply). Worth a comment + test.
3. **New goldens, not changed ones.** Single-controller goldens replay frozen
   `frame_inputs` and are untouched. 2-NPC scenarios need their **own** golden
   snapshots; capture via the merged-frame freeze (§4). Independent of the eventual
   "vs-legacy → vs-golden" oracle flip in [pm-mechanics §6.1](./pm-mechanics-implementation-analysis.md).
4. **Two live policies can deadlock/oscillate.** attacker-vs-attacker or a follower
   trailing forever may never resolve → a watch run needs a frame cap (watch already
   passes `frames=6000` + `stop_on_match_over`). Keep the cap; don't rely on KO.

## 7. Recommended #47 decomposition (file one child at a time, per RULES)

Ranked; **file Child A first** — it unblocks every other slice and is the smallest.

- **A — dual-controller seam.** `controllers=(c1,c2)` + union-merge in `run_battle`,
  `controller=` back-compat alias, merged-frame capture for replay; regression test
  (two controllers, disjoint-key assertion, byte-identical replay). *Small.* Unblocks B–E.
- **B — `BaseController` + reframe `ChaseController` as `AttackerController`.** Extract
  shared scaffolding behind `decide()`; keep behavior identical (existing chase goldens
  stay green = the regression proof). *Small–medium.*
- **C — `IdlerController` (baseline).** Empty/periodic-shield; validates dual-control
  cheaply via attacker-vs-idler. *Trivial.*
- **D — `FollowerController`.** Mirror + wide-standoff spacing policy. *Medium.*
- **E — watchable 2-NPC mode.** `watch.py --vs <archetype>`; a 2-NPC golden scenario;
  optional video. *Small–medium.* This is the user-visible #47 payoff.

**Perceived ROI: High.** Child A is a few-line, low-risk seam change that turns a
single-bot demo into a 2-NPC sandbox; B is pure refactor guarded by existing goldens;
C–E are additive. No blocked threads (unlike the PM-signature mechanics in
[pm-mechanics §7](./pm-mechanics-implementation-analysis.md)).

**Recommendation:** ✅ Decompose into the 5 children above; file **A** now.

## Sources

- SmashWiki — Artificial intelligence (CPU difficulty 0–100, reaction/follow-through
  probability, Brawl recovery/edge-guard/shield behavior, no-learning datamine):
  https://www.ssbwiki.com/Artificial_intelligence
- In-repo: `pycats/sim/controllers.py`, `runner.py`, `watch.py`,
  `pycats/entities/player.py:480`, `pycats/core/input.py`.
- Related research: [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md)
  (no PM-specific authoritative source — applies to CPU AI too),
  [pm-mechanics-implementation-analysis.md](./pm-mechanics-implementation-analysis.md)
  (oracle flip, roadmap), [pm-framerate-fidelity.md](./pm-framerate-fidelity.md)
  (determinism/fixed-timestep). Quality bar:
  [knockback-launch-physics-findings.md](./knockback-launch-physics-findings.md).
