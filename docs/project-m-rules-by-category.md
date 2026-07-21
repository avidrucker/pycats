# Project M rules by category

High-level index of the PM mechanics pycats has researched. Each row points to the detailed
local doc + the primary citation — this file is the map, the local docs are the territory.
PM canon = **Project M 3.6**. Status per ADR-0003 provenance (FOUND / GUESS / TUNED / DIVERGENCE).

> Complements `docs/pm-reference/00-overview.md` (prose overview); this file is the greppable
> by-category pointer table. One line per entry; detail lives in the linked doc. Append a row when
> a mechanic is researched/validated (spikes #538, #539, …).
>
> Part of the parity doc set — front door: [`docs/project-m-parity.md`](./project-m-parity.md).

The **`Constant`** column names the bare `combat/provenance.py` key for rows that map 1:1 to a single
constant (blank for compound/mechanic rows). `tests/test_tuning_provenance.py` gates it: a keyed row's
`Status` must match the registry's `status` for that key (#635, the #575 Tier-1 consistency gate).

| Category | Mechanic | Status | Constant | pycats value(s) | Local doc | Primary source |
|---|---|---|---|---|---|---|
| Ledge | Ledge-grab intangibility (fixed burst) | FOUND | `LEDGE_INTANGIBLE_BASE_FRAMES` | `LEDGE_INTANGIBLE_BASE_FRAMES = 21` | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | [rukaidata PM3.6 — CliffCatch](https://rukaidata.com/PM3.6/Mario/subactions/CliffCatch.html) (intangible 1–21, flat across characters; #671) |
| Ledge | Ledge intangibility **percent-scaling** (magnitude) | REMOVED (#543 / #683) |  | ~~`+0.3/%` cap `60` (#311)~~ → dropped; flat 21f now | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | none — PM %-dependence is getup **speed** (≥100%) + hang time, not intangibility magnitude |
| Intangibility | Action intangibility (dodge / roll / spot-dodge / air-dodge / ledge-grab / getup) — single mutually-exclusive body-state, overwrite not ORed (**#520** Layer 1) | FOUND |  | single `Fighter.intangible` bool — already PM-shaped (one body-state, one collision check) | [research/2026-07-04-invuln-timer-state-model.md](./research/2026-07-04-invuln-timer-state-model.md) → "Correction (2026-07-05)" | **T1** `brawllib_rs`: `self.hurtbox_state_all = state.clone();` (event **overwrites** `=`, one `HurtBoxState`) — [script_runner.rs](https://raw.githubusercontent.com/rukai/brawllib_rs/master/src/script_runner.rs); one-colour debug **T2** [SmashWiki — Intangibility](https://www.ssbwiki.com/Intangibility) |
| Invincibility | Timed invincibility (respawn ~120f; Starman) — separate frame-counted overlay that **composes** with Layer 1 (**#520** Layer 2 · **#537** Correction) | FOUND |  | **unimplemented** — no timed-overlay source today (#506); would be pycats' first genuinely-overlapping intangibility source | [research/2026-07-04-invuln-timer-state-model.md](./research/2026-07-04-invuln-timer-state-model.md) → "The corrected model" | **T2** [SmashWiki — Revival platform](https://www.ssbwiki.com/Revival_platform): post-drop *"a further period of invincibility (2 seconds, or 120 frames)"* keyed to dismount. **Truncation gap closed (#830):** acting does **not** truncate the post-drop window — it runs the full 120 f in real time (meleelight engine; PM `[inference]`), see [research/2026-07-21-respawn-invincibility-validation-findings.md](./research/2026-07-21-respawn-invincibility-validation-findings.md). Render is a **blink**, not solid (same doc). |
| Respawn | KO → respawn freeze delay (pre-drop) | TUNED | `RESPAWN_DELAY_FRAMES` | `RESPAWN_DELAY_FRAMES = int(2*FPS) = 120` (≈2 s) | [research/2026-07-03-pm-spawn-respawn-mechanics.md](./research/2026-07-03-pm-spawn-respawn-mechanics.md) → "pycats now" | none — pycats **ruleset** value; registry note: *"ruleset value, no canon"* (not a PM-canon frame count) |
| Respawn | Post-platform-drop respawn invincibility (~120f / ~2 s) | FOUND |  | **unimplemented** (#506; epic #482) — `reset_to_spawn` today even clears leaked `intangible` | [research/2026-07-03-pm-spawn-respawn-mechanics.md](./research/2026-07-03-pm-spawn-respawn-mechanics.md) → "PM / Melee model" | **T2** [SmashWiki — Revival platform](https://www.ssbwiki.com/Revival_platform): on-platform *"intangible … disappears as soon as the player moves or attacks"*, then a post-drop *"period of invincibility (2 seconds, or 120 frames)"*. **#830 validation:** duration confirmed 120 f; acting does not truncate the post-drop window; rendered as a **blink** (not solid) — [research/2026-07-21-respawn-invincibility-validation-findings.md](./research/2026-07-21-respawn-invincibility-validation-findings.md). |

> **Resolved (#683):** the percent-scaling constants (`LEDGE_INVULN_PER_PERCENT` `+0.3/%`, cap
> `LEDGE_INVULN_MAX_FRAMES` `60`) were **removed** — the ledge burst is now a flat 21f (row above),
> sourced from PM 3.6 CliffCatch (#671). The old DIVERGENCE row is kept above, marked REMOVED, for history.

> **Reading the Intangibility / Invincibility / Respawn rows:** `Status` records the **canon provenance** of the mechanic
> (FOUND = sourced from PM), while the `pycats value(s)` column states what pycats does **today** —
> so a `FOUND` row can still read **unimplemented** there. PM intangibility is a **two-layer** model
> (**#520** + the **#537** Correction): *Layer 1* action body-state (single, mutually-exclusive —
> pycats' one `intangible` bool already matches it) and *Layer 2* timed overlays (respawn ~120f,
> Starman) that **compose** with Layer 1. Only Layer 2 is a gap: pycats has no timed-overlay source
> yet — respawn invincibility is unimplemented (**#506**, epic **#482**), and it is the first
> genuinely-overlapping source the derive-not-write unify in #520 Q3 is meant to unblock.
