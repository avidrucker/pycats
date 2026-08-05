# PM Mario fireball cadence — animation length + earliest re-fire frame (#1060)

> Research findings (#1060). **Measures only — no code or data-value change.** Answers the
> canon question that anchors the downstream #925-problem-2 / #961 fix: *how often can PM
> Mario actually throw a new fireball?* Numbers are grounded in the **brawllib_rs PM 3.6
> datamine** (the actual `.pac` data) where the datamine yields them; anything that stays
> community-framedata or inference is labeled as such.
>
> Date: 2026-08-01. Agent: ELDERBERRY. Area: `area:combat` / `combat:cpu`.
> PM version: **3.6** (datamine overlay `pm-data/pm36-sd`; see [[brawllib-datamine-env-live]]).

## TL;DR

PM Mario's fireball (`SpecialN`) is a **49-frame** animation that becomes **interruptible on
frame 40** (`IASA`). So the soonest he can start a *second* fireball — or any move — is
**~frame 40**: the earliest re-fire interval is **~40 frames**, grounded directly in the
datamined `iasa`. The air version (`SpecialAirN`) is identical (49 / 40), so short-hop /
airborne cadence is the same.

Against pycats: the fireball **length is FAITHFUL** (pycats `neutral_b` = 48f ≈ datamine
49f, a ≤1-frame convention gap). The Lv9 CPU cadence is **DIVERGENT** — `attack_period=10`
re-presses B roughly **4× faster than the move physically permits** (10f vs the ~40f IASA
floor). That gap is the canon anchor #961 asked for: a specials-capable CPU's re-fire
interval should be bounded at **≥ ~40 frames**, not 10. *(Finding only — the value change is
a downstream architect/dev slice.)*

## 1. Fireball frame data

Primary datamine (brawllib_rs, PM 3.6 `.pac`), verbatim tool output — `examples/special_n_frames.rs`
reads `subaction.frames.len()` and `subaction.iasa` straight from Mario's fighter data:

```
SUMMARY  fighter  subaction    length  iasa  first_active  last_active  active_count
SUMMARY  Mario    SpecialN     49      40    -             -            0
SUMMARY  Mario    SpecialAirN  49      40    -             -            0
```

| Number | Value | Grounding |
|---|---|---|
| **Animation length (total)** | **49 frames** | **Datamine (primary, PM 3.6)** — `SpecialN.frames.len() = 49`. |
| **IASA / first-actionable-frame (FAF)** | **frame 40** | **Datamine (primary, PM 3.6)** — `SpecialN.iasa = 40`. |
| **Startup (fireball appears)** | **14 frames** (article spawns ~f15) | **Community framedata**, PM 3.6 — Smashboards *"Mario: Hitboxes and Frame Data [3.6]"*, recorded in-repo as `FOUND` in `docs/research/nalio-fireball-scoping-findings.md` (#155). *Not* datamined this session (see note). |
| **Fighter-hitbox active window** | **none** (`active_count = 0`) | **Datamine (primary)** — the fireball's damaging hitbox lives on the spawned **article**, not the fighter, so the fighter subaction carries no hitbox frames. Confirms the projectile model. |

**Datamine vs community framedata — the ≤1-frame convention gap.** The datamine's
`length = 49` and `iasa = 40` sit one frame off the Smashboards 3.6 table's *"48 total,
IASA 41"* (recorded in #155). This is the routine index-convention difference (`frames.len()`
counts frame *slots* 1..49; a framedata table's "total 48" usually means the last committed
frame, "IASA 41" the first actionable in its own 1-index scheme). Both sources agree on the
shape: **a ~48–49-frame move, actionable at ~frame 40–41.** I report the **datamined 49 / 40**
as the primary numbers and note the table's 48 / 41 as the concordant cross-check.

**Why startup isn't datamined here.** The fireball is created by an article-generate script
event, not a hitbox on Mario's own frames, so `first_active` over fighter hitboxes is `-`
(there is no fighter hitbox to detect). The **14-frame startup** therefore stays on the
community-framedata provenance record (#155), labeled — not asserted from the datamine.
Reading the article-generate frame off the raw script is a `thorough`-tier follow-up, out of
this ticket's moderate scope.

## 2. Earliest re-fire interval

**~40 frames**, grounded in the datamined `iasa`. `IASA = 40` means Mario regains action on
frame 40 of the fireball; the next input — a second fireball, or any other move — cannot be
*started* before then. So two consecutive fireball **starts** are **≥ ~40 frames apart**
(≈ 0.67 s at 60 fps). This is a floor set by the move itself; a human can re-fire no faster
than the animation's IASA permits.

- **Air / short-hop:** `SpecialAirN` is identical (`length 49`, `iasa 40`), so throwing from
  the air or a short-hop does **not** shorten the cadence — same ~40-frame floor. (Movement
  options like short-hop double-fireball change *positioning*, not the per-throw interval.)
- **Not modeled:** projectile lifetime / on-screen article limits (whether a prior fireball
  must expire before the next) are a separate article-count question, not this move-cadence
  floor; out of scope.

## 3. Comparison to pycats

pycats `neutral_b` (`pycats/characters/data/nalio.json`): `startup 14 / active 1 / recovery 33`
→ **48-frame total**, `name: "fireball"`, no interrupt/IASA field. Lv9 controller
(`LEVEL_PARAMS[9]` in `pycats/sim/controllers.py`): `attack_period = 10`.

| pycats number | pycats value | PM canon (datamine) | Verdict |
|---|---|---|---|
| `neutral_b` total length | 48f (14+1+33) | 49f | **FAITHFUL** (≤1-frame convention gap) |
| `neutral_b` startup | 14f | 14f (community framedata) | **FAITHFUL** |
| Early-out / IASA window | **none** — runs the full 48f | actionable at f40 (~8f early-out) | **DIVERGENT (minor)** — pycats is marginally *more* committal; the fireball has no interrupt window. |
| Lv9 re-fire cadence (`attack_period`) | **10f** | **~40f floor** (IASA) | **DIVERGENT (major)** — the CPU re-presses B ~4× faster than the move physically allows. |

The major divergence is the direct anchor for #961: because `attack_period=10 ≪ 40`, the Lv9
bot re-presses B long before the fireball resolves, and (per #961's engine finding) the fresh
special **restarts** the move — rooting the bot in the animation ~75% of frames. A re-fire
interval bounded at **≥ ~40 frames** (the datamined IASA floor) is the canon-faithful ceiling
on how fast a specials-capable CPU should legitimately re-fire.

## 4. Golden-safety note

Both pycats numbers this would inform are downstream, not touched here:

- **Move data** — `pycats/characters/data/nalio.json` `moves.neutral_b` (startup/active/
  recovery). The 48f total is already FAITHFUL; no change indicated by this research.
- **CPU cadence** — `LEVEL_PARAMS[9].attack_period` (and any specials-aware re-fire gate) in
  `pycats/sim/controllers.py`. Changing it is the #961 fix's job — a separate architect/dev
  slice, made against this ~40-frame anchor. The fireball poke branch is **Lv9-only** (gated
  on `"specials"` in `enabled_moves`), so any cadence change cannot perturb a non-Lv9 golden;
  the level-less golden controller has no `specials` and never throws (per #961 golden-safety
  and `docs/research/nalio-fireball-scoping-findings.md` Q4).

This document changes no code, data, or value.

## Sources

| Source | Quality | Gives |
|---|---|---|
| brawllib_rs datamine, PM 3.6 `.pac` (`examples/special_n_frames.rs`, `SpecialN`/`SpecialAirN`) | **primary** (PM 3.6 fighter data) | animation length **49**; **IASA 40**; no fighter hitbox (article projectile); air variant identical |
| `docs/research/nalio-fireball-scoping-findings.md` (#155) | provenance record (community framedata: Smashboards *"Mario: Hitboxes and Frame Data [3.6]"*) | startup **14**; concordant *"48 total, IASA 41"* cross-check |
| `pycats/characters/data/nalio.json` (`moves.neutral_b`) | primary (repo) | pycats `neutral_b` = 48f (14+1+33), name `fireball`, no IASA field |
| `pycats/sim/controllers.py` (`LEVEL_PARAMS[9]`) | primary (repo) | Lv9 `attack_period = 10` |
| `docs/research/cpu-lv9-noclose-findings.md` (#961) | primary (repo) | the no-close root cause this anchors (cadence ≪ move length; engine restart) |

## Caveats & gaps

- **Startup (14f) is community-framedata, not datamined** this session — the fireball is an
  article-generate event, not a fighter hitbox, so the datamine's `first_active` is `-`.
  Reading the article-spawn frame off the raw subaction script is a `thorough`-tier follow-up.
- **IASA 40 (datamine) vs 41 (framedata table)** — a ≤1-frame index-convention difference,
  reconciled above; both agree the move is actionable at ~frame 40–41.
- **Article/projectile-count limits** (must a prior fireball expire before the next?) are a
  separate question from the move-cadence floor and were not investigated.
- Web framedata pages were not quotable this session (Smashboards returned HTTP 403,
  `ssbwiki.com/Mario_(PM)` lists no fireball frame numbers); the datamine stands in as the
  stronger primary, with #155's in-repo record as the community cross-check.
