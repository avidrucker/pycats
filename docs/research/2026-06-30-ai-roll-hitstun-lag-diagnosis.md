# Why AI-emitted reactive rolls never convert to a dodge — the state-label-lags-hitstun gotcha (#370)

> Diagnosis (#370, from the #338 reactive-roll line). Reactive AI rolls *emit* a valid
> `{shield, away}` combo but never *convert* to a dodge in a real battle, while the identical
> input converts in isolation. This traces the exact broken link and recommends the fix.
> **Findings only — the fix is a follow-up DEV (see below).** Date: 2026-06-30. Agent: FIG.
> Area: `area:entities`.

## TL;DR

**The fighter is in hitstun on every roll-emit frame — it just doesn't look like it, because
the FSM `state` label lags the `hurt_timer` by one frame (#8's documented ordering).** The
#338 controller gate checks `a.state` (the lagging label), sees `idle`/`fall`, and emits a
roll — but `Player.update` gates all input on the *real* signal `in_hitstun = hurt_timer > 0`
and drops it. So a juggled fighter emits rolls that are 100% wasted. This is not a missing
dodge-able state (the original #370 premise, disproven) and not an input-mechanism bug (it
converts fine in isolation) — it is the controller reading the wrong actionability signal.

## Reproduction

Headless: a level-9 `AttackerController` (`evade_chance=0.30`) vs a `Swinger` opponent that
jabs on a cycle, `p2` next to `p1`. Over 400 frames the bot emits **12–16 rolls**, **zero
convert** (`dodge_timer` never rises). The identical `{shield, dir}` input driven onto a fresh
fighter in isolation **always** starts a roll (fresh press, held, and shield-then-add all
convert — `dodge_timer` 13/12/10).

## The failing frame (traced end-to-end)

Instrumenting one emit frame (f41):

```
st_before=idle  on_ground=True  hurt_timer=13  dodge_before=0
fi_held ={shield:True, right:True}   fi_press={right:True}   ->  st_after=idle  dodge_after=0
```

Everything the dodge branch needs is present — `shield` held, `right` freshly pressed, a
grounded "idle" state — yet no dodge. The tell is **`hurt_timer=13`**.

- `Player.update` (`entities/player.py`) computes `in_hitstun = hurt_timer > 0 or stun_timer > 0`
  and calls `handle_actions` (the dodge/shield/attack decode) **only when `not in_hitstun`**
  (and not in a few locked states). The gate exists so a post-hit frame does not clobber the
  knockback with walk input (#8/#44).
- But the FSM `state` **label** flips to `hurt` *one frame after* `hurt_timer` is set (hits are
  resolved by `process_hits` *after* the frame's `engine.tick`, per the #8 comment in
  `player.update`). So there is a one-frame (and, while juggled, a sustained) window where
  `hurt_timer > 0` **and** `state == "idle"/"fall"`.
- The #338 controller gate is `dodge_able = a.state in _DODGEABLE_STATES` — it reads the
  **label**, not the timer. During the lag window it judges the bot actionable and emits a roll;
  `Player.update` then drops the input because `in_hitstun` is true.

Confirmation: adding `and a.fighter.hurt_timer == 0 and a.fighter.stun_timer == 0` to the
controller gate drops the emits from 12–16 to **0** — i.e. *every* emitted roll was during
hitstun. There was never a legitimate (non-hitstun) dodge window in this juggle. Nothing was
lost by not converting them — a fighter in hitstun **must not** dodge.

## Why isolation converts but the loop doesn't

In isolation `hurt_timer == 0` (no one is hitting the fighter), so `handle_actions` runs and the
roll converts. In the loop the bot is being juggled, so `hurt_timer > 0` on the very frames its
*label* looks idle — the difference is entirely hitstun, not the input path or the state list.

## Recommended fix (a follow-up DEV)

Gate the #338 evade on the **real** actionability signal, mirroring `Player.update`'s
`in_hitstun`:

```python
dodge_able = (getattr(a, "state", None) in _DODGEABLE_STATES
              and a.fighter.hurt_timer == 0
              and a.fighter.stun_timer == 0)
```

Layer: **controller** (`sim/controllers.py`), one line. It stops the wasted emits so the bot
only rolls when genuinely actionable. It does **not** raise conversions in a juggle — correctly,
since a hit fighter can't dodge — but it makes the emission accurate and lets conversion happen
in scenarios where the bot is *threatened but not currently being hit*.

### General lesson (reusable)

**Any AI actionability check must read the timers (`hurt_timer`/`stun_timer`), not just the FSM
`state` label** — the label lags the timers by a frame by design (#8). This gotcha applies to
#363 (spot-dodge), #374 (movement), and any future reactive-input policy. `_DODGEABLE_STATES`
alone is necessary but not sufficient.

## Scope note (ties to #343)

This vindicates #343's "evasion is a minor CPU behaviour" at the mechanism level: reactive
evasion mostly fires *under attack*, and under attack the fighter is frequently in hitstun and
**cannot** dodge. So live conversion is inherently rare regardless of the fix — the fix only
removes the wasted, dropped emits.

## Cross-refs

Diagnosed for #338 (reactive roll-away); unblocks #363 (spot-dodge) with the same fix.
Disproves the original #370 "extend dodge-able states to walk/run" hypothesis. Files:
`pycats/entities/player.py` (`in_hitstun` gate + the #8 label-lag comment),
`pycats/entities/fighter_input.py` (dodge branch), `pycats/sim/controllers.py`
(`_DODGEABLE_STATES`, the evade gate). Movement-model faithfulness (`run` state) is #373/#374.
Orientation map #185.
