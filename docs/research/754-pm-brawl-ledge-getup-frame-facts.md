# PM 3.6 / Brawl ledge-recovery frame facts

> **Ticket:** [#754](https://github.com/avidrucker/pycats/issues/754) — RESEARCH: PM/Brawl ledge-getup frame facts (A1, child of #751).
> **Branch:** `br-apple/pycats-py-issue-754-research-pm-brawl-ledge-getup`
> **Date:** 2026-07-19 · **Agent:** APPLE
> **Scope:** Facts only. This doc records *what the engine/data say*; it does **not** decide pycats
> behavior (that is strand B) and does **not** cover CPU behavior (strand A2 / C4).

Every value below is labelled:

- **[primary]** — read directly from the PM 3.6 game data via the `brawllib_rs` datamine.
- **[secondary]** — from SmashWiki (a community wiki; Brawl figures unless noted). Downgraded vs
  [primary] on any conflict.
- **[inference]** — a reasoned conclusion, not a directly-read value. Flagged so it is never mistaken
  for a sourced number.
- **[OPEN]** — a fact the datamine and the wiki could **not** resolve because it is engine-hardcoded
  (not in the move data). Needs the codeset / RAM-dump path; tracked as an open question.

---

## 1. The ledge-recovery lifecycle

A fighter that grabs a ledge passes through three phases:

1. **Catch** — the brief grab animation (`CliffCatch`) the instant the ledge is seized.
2. **Hang** — an idle loop (`CliffWait`) the fighter sits in until it acts.
3. **Getup** — one of four ways off the ledge (climb, roll, jump, attack), each with a fast (≤100%
   damage) and a slow (>100% damage) variant.

The move (subaction) names are Brawl's internal names, carried unchanged into PM 3.6.

---

## 2. A character's ledge-recovery options, in full (PM 3.6, Mario)

This is the complete set of things a hanging fighter can do. **[primary]** unless noted — datamined
from `brawllib_rs @ e8dc833`, PM 3.6 overlay, fighter Mario, 2026-07-19. "Intangible" = the fighter
cannot be hit; the range is the 1-indexed frame span (whole-body intangibility). All frame lengths are
**byte-identical to vanilla Brawl** (see §5 for the single exception).

| Option | Variant (damage gate) | Subaction | Length | Intangible frames |
|---|---|---|---|---|
| **Grab the ledge** | (on catch) | `CliffCatch` | 21f | 1–21 (fully intangible) |
| **Hang / wait** | (idle loop) | `CliffWait` | 101f (loops) | none scripted — see §4 |
| **Climb up** (normal getup) | ≤100% | `CliffClimbQuick` | 35f | 1–30 |
| | >100% | `CliffClimbSlow` | 60f | 1–55 |
| **Roll up** | ≤100% | `CliffEscapeQuick` | 50f | 1–30 |
| | >100% | `CliffEscapeSlow` | 80f | 1–54 |
| **Ledge attack** | ≤100% | `CliffAttackQuick` | 56f | 1–20 |
| | >100% | `CliffAttackSlow` | 70f | 1–36 (was 44 in vanilla — §5) |
| **Ledge jump** | ≤100% | `CliffJumpQuick1` → `…Quick2` | 16f + 31f | 1–16 (part 1 fully intangible); part 2 none |
| | >100% | `CliffJumpSlow1` → `…Slow2` | 20f + 31f | 1–20 (part 1 fully intangible); part 2 none |

**Reading the table:**

- **The ≤100% / >100% split is real and consistent.** `Quick` = ≤100%, `Slow` = >100% **[inference,
  reference-backed]** — the Quick/Slow→percent mapping is the documented Brawl convention (SmashWiki
  `Edge getup`: "when the character has 100% damage or more, the action … is significantly slower"
  **[secondary]**), and every option's slow variant is strictly longer than its fast variant (climb
  35→60, roll 50→80, attack 56→70, jump part-1 16→20) **[primary]**.
- **Ledge jump is two subactions.** Part 1 is the fully-intangible launch off the ledge; part 2 is the
  airborne remainder with no intangibility. In Brawl/PM a fighter can act (air-dodge / attack) out of
  the jump, carrying the part-1 intangibility into the air (SmashWiki `Edge` **[secondary]**).
- **Ledge-attack intangibility is a fixed span here but varies by character in general** (SmashWiki
  `Edge getup`: "the amount of intangibility ledge attacks had varied from character to character"
  **[secondary]**). Mario's spans are the datamined `[primary]` values above; other cats may differ and
  would each need their own datamine.

---

## 3. Ledge-grab (catch) intangibility

- **PM 3.6:** the catch animation `CliffCatch` is **21 frames, fully intangible for all 21**
  **[primary]**.
- **Vanilla Brawl (SmashWiki `Edge`):** a ledge-grab grants "23 frames (plus the duration of the
  edge-grabbing animation, which is 23 frames, excluding Pikachu, for which it's 11 frames)"
  **[secondary]**.
- **⚠ Cross-source mismatch to resolve:** SmashWiki calls the Brawl grab animation 23 frames; the
  datamine measures `CliffCatch` at 21 frames (identical in vanilla and PM). A 2-frame gap — possibly a
  counting convention (inclusive vs exclusive) or a wiki approximation. **Do not average them; pin the
  datamined 21f as the PM 3.6 value and flag the mismatch.** **[inference]**

---

## 4. Ledge-**hang** intangibility — why it is not in this data **[OPEN]**

The hang idle loop `CliffWait` is 101 frames and carries **zero scripted intangibility** **[primary]**.

That is the key structural finding: **the intangibility a fighter keeps *while hanging* is applied by
the engine, not written into the `CliffWait` move.** SmashWiki's "23 frames of ledge intangibility"
figure therefore describes an **engine timer**, and it does not appear anywhere in the move data the
datamine can read. **[inference]**

Consequence: the following three facts are **[OPEN]** — unreachable by the datamine or the wiki, and
requiring the engine-code / RAM-dump path (see the `rukaidata-engine-hardcoded-limit` note, #215/#192):

- **q(hang-window):** the exact PM 3.6 ledge-hang intangibility window, and whether it matches Brawl's
  23 frames.
- **q(regrab):** whether each ledge *regrab* refreshes intangibility, or it is staled/removed on repeat
  grabs (the planking nerf). SmashWiki gives no Brawl regrab-staling rule — its decay section is
  Melee-only, and the explicit regrab nerf is an Ultimate change **[secondary]**.

---

## 5. Max-hang duration + expiry **[secondary / OPEN]**

- **Vanilla Brawl (SmashWiki `Edge`):** maximum hang time is **~6 seconds under 100% damage** and
  **~5 seconds at 100% or above** **[secondary]**.
- **[OPEN] What expiry does:** SmashWiki gives the timer but **not** the behavior when it runs out —
  whether the fighter is forced to fall, forced into an auto-getup, or left hanging but hittable. Not in
  move data. Needs the engine source.
- **[OPEN] PM 3.6 cap:** PM may have retuned the 6s/5s figures; unconfirmed. Needs the PM engine value.

This bears directly on #706 (a Lv9 fighter wall-hang that never appears to time out).

---

## 6. PM 3.6 vs vanilla Brawl — the divergence

Across Mario's **entire** `Cliff*` set, PM 3.6 changes **exactly one value** vs vanilla Brawl
**[primary]**:

- **`CliffAttackSlow` (>100% ledge-attack) intangibility: 44 frames → 36 frames (−8).**

Every other `Cliff*` frame-length and intangibility span is identical between vanilla Brawl and PM 3.6.
Practical takeaway: for ledge-recovery frame data, the Brawl baseline is a safe source for pycats
**except** the >100% ledge-attack, where PM must be used.

---

## 7. Status against the ticket's three research questions

| # | Question | Status |
|---|---|---|
| 1 | Getup options + frame data (≤100% vs >100%) | **Answered [primary]** — §2 table. |
| 2 | Ledge-intangibility window + regrab/staling | **Partial** — catch window §3 [primary] + Brawl baseline [secondary]; hang-window & regrab **[OPEN]** (§4). |
| 3 | Max hang + expiry behavior | **Partial** — Brawl cap [secondary] §5; PM cap & expiry behavior **[OPEN]**. |

The **[OPEN]** items in §4–§5 are all engine-hardcoded — the exact class of value the ticket's source
caveat warned the datamine would not reach.

---

## 8. Provenance — how to reproduce

**Datamine [primary]:**

```
cd ~/Documents/Study/Rust/brawllib_rs && . ~/.cargo/env
cargo run --release --example cliff_lengths -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay (drop -m for vanilla)
  -f Mario
```

- `brawllib_rs` clone `@ e8dc83313ebc3da31288c076097e80aec47324b2`, run 2026-07-19.
- Frame length = `subaction.frames.len()`. Intangibility = frames whose hurtboxes carry an
  `Intangible*` `HurtBoxState` (whole-body). `cliff_lengths.rs` is a throwaway example (a copy of
  `wait_lengths.rs` filtered to `Cliff*`).
- `.pac` data is copyrighted and never committed.

**Secondary:** SmashWiki [`Edge`](https://www.ssbwiki.com/Edge),
[`Edge getup`](https://www.ssbwiki.com/Edge_getup), [`Planking`](https://www.ssbwiki.com/Planking) —
all fetched 2026-07-19.

**Claims ledger:** the individual facts above are drafted (ungated) in the git-excluded
`claims-data/ledge-getup/` ledger (drafts d1–d11), awaiting human admission via `/verify-claims`.

---

## 9. Downstream (not decided here)

- **Strand C — landing this data in code:** [#771](https://github.com/avidrucker/pycats/issues/771)
  encodes the §2 getup-option table as sourced pycats constants, grounded in this doc.
- **Strand B** (#751) — what a pycats no-input/idle fighter *should* do on the ledge, grounded in §2.
- **Code-audit child** (#751) — what getup states `pycats/entities/fighter.py` implements today (a
  soft prerequisite for #771).
- **The [OPEN] engine facts** (§4–§5) — a follow-up research thread (codeset / RAM-dump path) for the
  hang-window / max-hang / expiry / regrab numbers is **pending a necessity check** — not yet filed; it
  is filed only if strand B/C actually needs those numbers. A faithful #706 hang-timeout fix depends on
  it.
