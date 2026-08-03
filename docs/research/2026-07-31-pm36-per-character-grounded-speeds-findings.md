# PM 3.6 per-character grounded-movement speeds — roster survey (#814)

**Role:** RESEARCH · parent #813 (grounded-speed provenance umbrella) · child 1.
**Date:** 2026-07-31 · **Agent:** FIG.
**Question:** In PM 3.6, do walk-max / initial-dash / run-max speeds vary per character, and by how much?

## TL;DR

1. **Yes — all three are independent per-character attributes** in the fighter param table
   (`walk_max_vel` @0x08, `dash_init_vel` @0x10, `dash_run_term_vel` @0x1c). They are separately
   tuned f32s, not derived from one scalar. Datamined directly from the PM 3.6 codeset.
2. **The walk:dash:run ratio is NOT constant** — it is strongly character-specific. For some
   fighters run-max **exceeds** initial-dash (Fox, Sonic, Captain); for others run-max is **below**
   initial-dash (Samus, Dedede, Falco, Ike, Jigglypuff) — their initial dash burst is *faster* than
   their sustained run.
3. **Nalio = Mario correction (the #813 payoff):** PM 3.6 Mario is **walk 1.1 / dash 1.5 /
   run 1.5** — `dash_init_vel == dash_run_term_vel == 1.5`. The current pycats guess of run **1.55**
   is the **Project+** value, pulled from a SmashWiki table explicitly labeled *"Stats (Project+)"*.
   Confirmed discrepancy: **1.55 = Project+, 1.5 = PM 3.6.**
4. **For Nalio there is no dash-vs-run *speed* gap** — not merely a pixel-rounding artifact
   (`1.5 → 8px`, `1.5 → 8px`) but a genuine **attribute equality** (1.5 == 1.5). PM's dash/run
   distinction for Mario is about **state + acceleration** (instant burst to 1.5, then sustained),
   not a higher run terminal velocity. This directly bears on #808/#374 (see §5).

---

## Method & provenance

Datamined with `brawllib_rs` (the live PM datamine env, [[brawllib-datamine-env-live]]) reading the
**fighter attribute table** — the engine param block, *not* per-subaction scripts (the ticket flagged
that risk; the attributes do live in the param table and brawllib exposes them).

- Source layers: `-d` vanilla Brawl (extracted ISO `DATA/files`) overlaid with `-m` **PM 3.6 codeset**
  (`pm-data/pm36-sd`, the extracted PM 3.6 SD `projectm/` tree). Attribute reads reflect the PM 3.6
  overlay where it overrides, which for movement is everywhere PM retuned.
- Helper: `examples/movement_attrs.rs` (throwaway, added to the brawllib clone) prints a TSV of the
  seven ground-movement attributes for the whole roster in one pass.
- Attribute offsets (verbatim from `brawllib_rs` `src/sakurai/fighter_data/mod.rs::fighter_attributes`):
  `walk_init_vel` @0x00, `walk_acc` @0x04, **`walk_max_vel` @0x08**, **`dash_init_vel` @0x10**,
  `dash_run_acc_a` @0x14, `dash_run_acc_b` @0x18, **`dash_run_term_vel` @0x1c** (= max run speed).

**Two validations that this is trustworthy PM 3.6:**

1. **Overlay applies.** Diffing PM (`-m`) vs vanilla Brawl (no `-m`) shows PM 3.6 changed most
   fighters' ground movement — e.g. Fox walk 1.45→1.6, dash 2.1→1.9; Bowser dash 1.0→1.3;
   Sonic run 3.5→4.0; Ganon run 1.16→1.35. So the overlay is being read, not silently ignored.
   (Mario's *terminal* speeds happen to be unchanged from Brawl — 1.1/1.5/1.5 — though PM retuned his
   dash accel 0.0998→0.06, so the values are genuine PM 3.6, not a fall-through.)
2. **Offsets are correct.** The vanilla-Brawl reads match the canonical published Brawl attribute
   spreadsheet exactly (Mario 1.1/1.5/1.5, Fox walk 1.45 dash 2.1, Bowser dash 1.0), confirming the
   offset interpretation. Same parser + offsets produce the PM reads.

**The Project+ trap, documented (ticket method — flag Project+ vs PM 3.6):** SmashWiki
`Mario_(PM)` lists the speed table under a heading reading verbatim **"Stats (Project+)"**, with
"1.5 – Initial dash" and **"1.55 – Run"**. That 1.55 is the number pycats' current guess chain
(#808→#373→#119→#120) adopted as "PM Mario run". It is a **Project+** value, never a PM 3.6 primary.
The datamine above is the PM 3.6 primary and gives **1.5**.

---

## Deliverable 1 — Are walk/dash/run distinct per-character attributes? **Yes.**

Three independent f32 fields per fighter (offsets above). No global; no derivation from a single
scalar. The engine also stores separate accelerations (`dash_run_acc_a/b`) governing how fast a
fighter accelerates from `dash_init_vel` toward `dash_run_term_vel` — so "run" is the *sustained
terminal state*, reached by acceleration, not a second launch speed.

## Deliverable 2 — Sourced per-character table (PM 3.6 primary)

Full roster, units are u/f (in-game units per frame). `run_max` = `dash_run_term_vel`. Cats currently
mapped: **Nalio = Mario** (only assignment so far; birky/narz/gnok archetypes not yet PM-mapped).

| Fighter (internal) | walk_max | dash_init | **run_max** | walk_acc | dash_acc_a | dash_acc_b |
|---|---|---|---|---|---|---|
| **Mario (Nalio)** | **1.1** | **1.5** | **1.5** | 0.1 | 0.06 | 0.02 |
| Captain (Falcon) | 0.85 | 2.0 | 2.3 | 0.1 | 0.15 | 0.01 |
| Dedede | 0.95 | 1.4 | 1.22 | 0.0 | 0.04 | 0.02 |
| Diddy | 1.25 | 1.7 | 1.9 | 0.1 | 0.1 | 0.02 |
| Donkey | 1.2 | 1.8 | 1.8 | 0.1 | 0.05 | 0.02 |
| Falco | 1.4 | 1.9 | 1.5 | 0.1 | 0.1 | 0.02 |
| Fox | 1.6 | 1.9 | 2.2 | 0.1 | 0.1 | 0.02 |
| GKoopa (Giga) | 0.6 | 1.9 | 1.7 | 0.05 | 0.16 | 0.08 |
| GameWatch | 1.1 | 1.5 | 1.5 | 0.1 | 0.06 | 0.02 |
| Ganon | 0.73 | 1.3 | 1.35 | 0.0 | 0.08 | 0.01 |
| Ike | 1.2 | 2.0 | 1.55 | 0.0 | 0.065 | 0.0 |
| Kirby | 0.85 | 1.5 | 1.5 | 0.1 | 0.08 | 0.02 |
| Koopa (Bowser) | 0.75 | 1.3 | 1.65 | 0.07 | 0.04 | 0.02 |
| Link | 1.2 | 1.5 | 1.4 | 0.1 | 0.1 | 0.02 |
| Lucario | 1.3 | 2.05 | 1.85 | 0.1 | 0.15 | 0.02 |
| Lucas | 0.82 | 1.725 | 1.725 | 0.13 | 0.04 | 0.02 |
| Luigi | 1.1 | 1.3 | 1.34 | 0.1 | 0.06 | 0.02 |
| Marth | 1.6 | 1.5 | 1.8 | 0.0 | 0.06 | 0.0 |
| Metaknight | 1.22 | 1.75 | 2.1 | 0.13 | 0.08 | 0.02 |
| Mewtwo | 1.0 | 1.4 | 1.4 | 0.1 | 0.05 | 0.1 |
| Ness | 0.84 | 1.45 | 1.6 | 0.1 | 0.04 | 0.02 |
| Peach | 0.85 | 1.2 | 1.3 | 0.1 | 0.1 | 0.02 |
| Pikachu | 1.24 | 1.8 | 1.8 | 0.1 | 0.08 | 0.02 |
| Pikmin (Olimar) | 0.9 | 1.4 | 1.61 | 0.1 | 0.05 | 0.02 |
| Pit | 1.18 | 1.5 | 1.82 | 0.13 | 0.1 | 0.02 |
| PokeFushigisou (Ivysaur) | 1.05 | 1.4 | 1.5 | 0.04 | 0.08 | 0.02 |
| PokeLizardon (Charizard) | 0.7 | 1.5 | 2.07 | 0.0 | 0.05 | 0.02 |
| PokeZenigame (Squirtle) | 0.9 | 1.32 | 1.45 | 0.1 | 0.15 | 0.01 |
| Popo (Ice Climbers) | 0.95 | 1.4 | 1.4 | 0.1 | 0.05 | 0.02 |
| Purin (Jigglypuff) | 0.7 | 1.4 | 1.1 | 0.1 | 0.065 | 0.02 |
| Robot (R.O.B.) | 1.1 | 1.24 | 1.55 | 0.1 | 0.1 | 0.02 |
| Roy | 1.2 | 1.4 | 1.61 | 0.0 | 0.07 | 0.0 |
| SZerosuit (ZSS) | 1.35 | 1.7 | 2.05 | 0.3 | 0.08 | 0.02 |
| Samus | 1.0 | 1.86 | 1.55 | 0.1 | 0.1 | 0.02 |
| Sheik | 1.2 | 1.7 | 1.8 | 0.1 | 0.1 | 0.02 |
| Snake | 0.875 | 1.3 | 1.55 | 0.1 | 0.1 | 0.02 |
| Sonic | 1.4 | 1.7 | 4.0 | 0.1 | 0.12 | 0.02 |
| ToonLink | 1.2 | 1.8 | 1.6 | 0.1 | 0.1 | 0.02 |
| Wario | 0.85 | 1.3 | 1.55 | 0.13 | 0.06 | 0.02 |
| Wolf | 1.3 | 2.1 | 2.0 | 0.15 | 0.1 | 0.02 |
| Yoshi | 1.15 | 1.33 | 1.6 | 0.1 | 0.08 | 0.02 |
| Zelda | 0.8 | 1.275 | 1.275 | 0.1 | 0.12 | 0.02 |

(`PokeTrainer` reads all-zero — a shell entity, no own movement. `WarioMan` is a Final-Smash form.)

## Deliverable 3 — Spread + ratio

- **walk_max:** 0.7 (Charizard/Jigglypuff) → 1.6 (Fox/Marth) — a **2.3× spread**.
- **dash_init:** 1.2 (Peach) → 2.1 (Wolf) — **1.75×**.
- **run_max:** 1.1 (Jigglypuff) → 4.0 (Sonic) — **3.6×**; excluding Sonic's outlier, top is ZSS/Fox ~2.2.
- **Ratio is character-specific, three distinct regimes:**
  - **run > dash** (accelerate into a faster run): Fox, Captain, Sonic, Bowser, Marth, Sheik, Charizard, ZSS, Metaknight…
  - **run == dash** (run = sustained dash, no speed change): **Mario/Nalio**, GameWatch, Kirby, Donkey, Pikachu, Lucas, Mewtwo, Wolf-ish…
  - **run < dash** (initial burst faster than sustained run): Samus, Dedede, Falco, Ike, Jigglypuff, Link, ToonLink, Lucario.

So a faithful port cannot assume "run is the fast state" — for a third of the roster the initial dash
is the fastest ground speed and run is a *decel* target.

## Deliverable 4 — Integer-pixel reality (`PX_PER_UNIT = 5.4`, round-to-int)

pycats renders integer px/frame. `px = round(u × 5.4)`. Whether a dash/run *speed* gap survives:

| Fighter | dash px | run px | gap survives? |
|---|---|---|---|
| **Mario (Nalio)** | **8** | **8** | **no — collapse** |
| Fox | 10 | 12 | yes |
| Falco | 10 | 8 | yes (run **slower**) |
| Captain | 11 | 12 | yes |
| Sonic | 9 | 22 | yes |
| Marth | 8 | 10 | yes |
| Bowser | 7 | 9 | yes |
| Ganon | 7 | 7 | no — collapse |
| Donkey | 10 | 10 | no — collapse |
| Jigglypuff | 8 | 6 | yes (run **slower**) |
| Sheik | 9 | 10 | yes |
| Samus | 10 | 8 | yes (run **slower**) |
| Dedede | 8 | 7 | yes (run **slower**) |
| Wolf | 11 | 11 | no — collapse |
| Zelda | 7 | 7 | no — collapse |
| Pikachu | 10 | 10 | no — collapse |
| Ike | 11 | 8 | yes (run **slower**) |

**Takeaways for a pixel-resolution port:**
- **Nalio/Mario: dash 8 == run 8.** No gap at any resolution — the underlying attributes are equal.
- ~7 of the sampled fighters collapse to equal px (Mario, Ganon, Donkey, Wolf, Zelda, Pikachu…).
- Several show **run < dash** even in px (Falco, Samus, Dedede, Ike, Jigglypuff) — a faithful port
  would have them *decelerate* out of the initial-dash burst into a slower run.
- Only the fast-runner archetypes (Fox, Captain, Sonic, Marth, Bowser…) show run **faster** than dash.

---

## §5 — Bearing on #808 / #374 (the DEV consumer)

#808 ("sustained `run` state + `run_speed`") and its design parent #374 assume **dash ≠ run means
distinct speeds** and plan a `RUN_SPEED` config distinct from `DASH_SPEED`. For **Nalio (the only
mapped cat), that premise is false in PM 3.6:**

- `RUN_SPEED` pinned to Nalio/Mario would be `round(1.5 × 5.4) = 8` — **identical to `DASH_SPEED = 8`**.
- The equality is a real attribute fact (1.5 == 1.5), not a rounding coincidence. So no amount of
  sub-pixel precision recovers a Mario dash/run *speed* gap.
- PM's dash-vs-run distinction for Mario is **state + acceleration**: initial dash instantly sets
  1.5; holding transitions to a sustained *run* that stays at the same 1.5 terminal (rather than
  decaying to walk). The observable difference is **"keeps moving at dash speed vs. decays to walk"**,
  and **turn/skid rules**, not a higher px/frame.

**This does not block the #808 run-*state* machinery** — the FSM leaf, held-direction flag, and
`dash → hold → run` transition are all still needed and are speed-independent. What it changes is the
**value story**: for Nalio, `run_speed == dash_speed` (both 1.5 u → 8 px). The decision to make is
whether pycats models run as a distinct *number* at all for Nalio, or whether dash≠run is expressed
purely as **state/turn-rules** with a shared 8 px terminal (matching PM). That is an
architect/value-basis call for the #808/#374 owner — this survey supplies the primary basis.

**Child-2 of #813 (Mario re-pin, unblocks #808)** now has its answer: PM 3.6 Mario run-max = **1.5
u/f = round(8.1) = 8 px**, provenance = brawllib_rs datamine of the PM 3.6 codeset (this doc), to be
recorded as a **`FOUND`** value under ADR-0003/#233, superseding the Project+ 1.55 guess.

## Reproduce

```
cd ~/Documents/Study/Rust/brawllib_rs && . ~/.cargo/env
cargo run --release --example movement_attrs -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd
# drop -m for the vanilla-Brawl comparison
```

## Out of scope (per ticket)

- Re-pinning Mario's value into config / `FighterData` (downstream DEV, child 2 of #813 + #808).
- Non-speed attributes (gravity/fall/jump/air); per-fighter tuning of the unmapped cats
  (birky/narz/gnok) pending their archetype assignment.

## Relationships

Parent **#813**; sibling child 2 (Mario re-pin → unblocks **#808**). Design lineage **#374/#373**;
unit basis **#119/#120**; provenance registry **ADR-0003 / #233**. Confirms the
[[grounded-speeds-projectplus-not-pm36]] trace and the Project+≠PM-3.6 lesson (#815 TIL).
