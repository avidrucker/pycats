# Ledge regrab intangibility — the 5-grab cutoff + its HUD

> The PM **anti-plank** ledge rule as implemented in pycats: a **hard 5-regrab
> count cutoff** (NOT gradual per-grab decay), plus the two above-head HUD
> indicators that visualise it. Companion to the interaction map
> [ledge-mechanics.md](./ledge-mechanics.md) (which owns grab/hang/getup/edgeguard);
> this doc owns the regrab-count sub-mechanic and its display. Sim shipped in
> [#656](https://github.com/avidrucker/pycats/issues/656); HUD is
> [#657](https://github.com/avidrucker/pycats/issues/657) (dots) +
> [#658](https://github.com/avidrucker/pycats/issues/658) (bar). Spec ticket
> [#720](https://github.com/avidrucker/pycats/issues/720). PM 3.6.

**Audience:** a contributor — human or agent — implementing or modifying the ledge
regrab cutoff or its HUD. Assumes the [00-overview](./00-overview.md) conventions
(60 Hz integer frames). Named landmarks, not line numbers.

## The mechanic (sim)

In Project M a character may grab the ledge an **unlimited** number of times, but
the intangibility that a grab grants is **rationed**:

- **Grabs 1–5** (consecutive, *without touching the ground*) each grant the **full
  fixed burst** of **21 frames** of intangibility.
- **Grab 6 and beyond** grant only a **small residual** of **5 frames** — a
  **PLACEHOLDER** value (see *Values & provenance*), non-zero, modelling the "few
  frames during the initial ledge snap" the primary source mentions.

This is a **hard count cutoff**, not a gradual decay. Earlier pycats framing (and
older text in `ledge-mechanics.md`) described intangibility "scaling down with each
regrab" — a Smash-4/Ultimate model. PM's real rule, ratified in
[#670](https://github.com/avidrucker/pycats/issues/670), is the count cutoff above.

### The counter

`Fighter.ledge_regrab_count` (in `pycats/entities/fighter.py`) tracks consecutive
grabs without touching the ground. It is **1 on the first grab** (incremented at the
grab site in `Player.update`, `pycats/entities/player.py`, before the burst is
granted). The grant is resolved by the pure function `ledge_regrab_invuln_frames`
(`pycats/entities/ledge.py`):

```text
count 1..5  -> LEDGE_INVULN_BASE_FRAMES              (21f, full burst)
count 6+    -> LEDGE_POST_CUTOFF_RESIDUAL_FRAMES     (5f, placeholder residual)
```

### Reset conditions

`ledge_regrab_count` resets to **0** on any of three events — the chain is over and
the next grab is again grab #1:

1. **Landing on the ground** — `Fighter._handle_landing` (the air→ground edge).
2. **Getting KO'd / respawn** — `Fighter.reset_to_spawn`.
3. **Getting hit** — `Fighter.receive_hit`. See the decision below.

## The get-hit reset — a recorded decision

**Getting hit resets the count.** This is the PM primary rule, and it was
**ratified by the owner (2026-07-08)** — recorded here so a future agent does not
"simplify" it away.

> **PMDT 3.5, "Ledge Invincibility":** "After a character regrabs the ledge five
> times without touching the ground, that character no longer receives invulnerability
> for grabbing the ledge again (except for a few frames during the initial ledge
> snap) **until he or she either lands on the stage or gets hit**."

**Intent:** the anti-plank cutoff targets the *staller*. Resetting on-hit is
*forgiving to the victim* — a fighter being edge-guarded gets a fresh count rather
than being double-punished for having grabbed the ledge a few times. Shipped in
`Fighter.receive_hit` (#656).

## The HUD — invuln bar over grabs-left dots

Two above-head indicators, stacked **top to bottom: (A) invuln bar → (B) grabs-left
dots → (C) the cat.** They visualise two *different* quantities and have two
*different* lifecycles.

| chain state (`ledge_regrab_count`) | (A) invuln bar | (B) grabs-left dots |
| --- | --- | --- |
| 0 — no chain / just reset | none | none |
| 1st grab | 21f, counting down (while hanging) | 5 dots |
| 2nd–5th grab | 21f, counting down | 4 → 1 dots |
| 6th+ grab (past cutoff) | 5f residual, counting down | none |

### (B) Grabs-left dots — the discrete grab-budget

Each dot is **one remaining grab (of 5) that still gives the full 21f invuln**. The
count is pinned to the shipped field:

```text
dots = max(0, LEDGE_REGRAB_INVULN_CUTOFF + 1 - ledge_regrab_count)
```

shown **only while `1 <= ledge_regrab_count <= 5`** (at count 0, or 6+ past the
cutoff, no dots render). So: first grab → 5 dots, fifth grab → 1 dot, sixth grab →
none. On-screen label: **"grabs left"**. Derive the `5` from
`LEDGE_REGRAB_INVULN_CUTOFF`, never hardcode it.

### (A) Invuln bar — the current grab's window

A smooth countdown of the **current grab's** intangibility (a bar is the right shape
— 21 discrete dots would be unreadable). This **revives the [#531] INVULN bar**,
which never rendered because it was suppressed while `state == "ledge_hang"` — the
one state in which the ledge burst is ever live. #658 must **drop that
`state != "ledge_hang"` suppression** (in `render_battle.py`'s `STATUS_SOURCES`, and
the matching `_invuln_remaining_max` suppression) **for the ledge-grab bar only** —
a deliberate reversal of the original hide-during-hang choice, not a blanket change
to the dodge/getup/respawn invuln bars.

**Residual bar scaling — normalized per-grant.** The 6th+ grab's 5f bar behaves like
any other bar: it starts full and drains over its own duration (5/5 → 4/5 → … → 0),
**not** proportional to the 21f max. This is already what the existing `timer /
granted` ratio does (`draw_timer_bars` / the `ledge_invuln` source's `ratio`), with
`granted = 5` for a residual grab — so the residual bar needs no special-casing; it
is a normal INVULN bar with a shorter granted length. (Rejected: a proportional-to-21f
stub. The bar reads as *duration*, not *budget*; the grabs-left dots — absent past
the cutoff — already signal the reduced budget.)

### Two lifecycles

- **The bar is per-grab.** It shows only while `ledge_invuln_timer > 0`, i.e. during
  a hang, and ends the moment the fighter leaves the ledge (getup or drop zero the
  timer).
- **The dots are per-chain.** They persist through the airborne jump/attack *between*
  grabs (the count holds) and vanish only when the count resets (land / KO / hit).

## Values & provenance

| value | constant | frames | basis |
| --- | --- | --- | --- |
| Cutoff count | `LEDGE_REGRAB_INVULN_CUTOFF` | 5 grabs | **Sourced** — PMDT 3.5 primary ("regrabs the ledge five times"), via #536 findings. |
| Full burst | `LEDGE_INVULN_BASE_FRAMES` | 21f | **Sourced** — PM 3.6 CliffCatch, fully intangible frames 1–21 (rukaidata, #671; #683 landed it, retiring the old Brawl baseline of 23). |
| Post-cutoff residual | `LEDGE_POST_CUTOFF_RESIDUAL_FRAMES` | 5f | **PLACEHOLDER — unsourced.** PM primary says only "a few frames"; #671's 3–7f is an estimate, not a datamined count. Carries a `PLACEHOLDER_VALUE_PLS_RESEARCH_ACTUAL` comment and **no `Provenance` entry** — an acknowledged gap. The real value needs a datamined engine/DOL dump, tracked as future research. |

## Implemented by

- **Sim (shipped):** [#656](https://github.com/avidrucker/pycats/issues/656) — the
  count, the cutoff, the three resets, and `ledge_regrab_invuln_frames`.
- **HUD (pending):** [#657](https://github.com/avidrucker/pycats/issues/657)
  grabs-left dots; [#658](https://github.com/avidrucker/pycats/issues/658) the revived
  invuln bar. Both should reference this doc rather than restate the spec.

[#531]: https://github.com/avidrucker/pycats/issues/531
