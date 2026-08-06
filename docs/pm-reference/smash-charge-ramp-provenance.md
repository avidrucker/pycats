# Smash charge ramp — primary-source provenance (research #626)

**Question (from #626, spun out of the #599 caveat):** confirm or refute Project M's
smash-attack **charge ramp of 59 frames** (vs the base-game 60) against a *primary* source,
and route the outcome — upgrade the provenance, revert to 60, or mark `⚠ undocumented`.

**Verdict in one line:** the **×1.3671 full-charge multiplier is now primary-confirmed**
(meleelight, a Melee engine reimplementation); the **59-frame ramp is neither confirmed nor
refuted by any accessible primary** — it rests on a single secondary (SmashWiki *Project M*)
that *contradicts SmashWiki's own general article* (which states 60 frames for every game
Melee→Ultimate). Recommendation: **keep 59** as the PM-specific value but **downgrade its
provenance note to `⚠ primary-unconfirmed`**, and **upgrade the multiplier's note** to cite the
meleelight primary.

Citation discipline (per RULES → PM parity, and memory `pm-parity-cite-primary-not-inference`):
primary quotes are labelled **[primary]**; secondary/wiki claims **[secondary]**; reasoning
**[inference]**. Note this corrects a mislabel in `smash-charge-hold.md` (#595), which called
SmashWiki *Project M* a "primary" — a wiki is a **citable secondary**, not primary.

---

## What each source actually says

### Multiplier — ×1.3671 at full charge → **[primary] confirmed**

`~/Documents/Study/JavaScript/meleelight/` (clone from #616 — schmooblidon/meleelight, a
faithful **Melee** engine reimplementation in JS). Every forward/down/up-smash hardcodes the
same ramp, e.g. `src/characters/marth/moves/FORWARDSMASH.js`:

```js
player[p].phys.chargeFrames++;
if (player[p].phys.chargeFrames === 60) { /* fire at cap */ }
// damage scaling elsewhere: damage *= 1 + chargeFrames * (0.3671 / 60)
```

At full charge (`chargeFrames = 60`): `1 + 60*(0.3671/60) = 1.3671`. This is a **[primary]**
engine literal for **Melee**, and PM restored Melee's multiplier — so `SMASH_CHARGE_SCALE =
1.3671` is corroborated by a primary (Melee lineage) **and** two secondaries (SmashWiki *Smash
attack*: "1.3671× damage in Melee"; SmashWiki *Project M*: "x1.3671"). Well-sourced.

### Ramp — 59 vs 60 frames → **neither confirmed nor refuted by a primary**

| Source | Tier | Says | On which game |
|---|---|---|---|
| meleelight (`chargeFrames === 60`) | **[primary]** engine literal | **60** | Melee |
| SmashWiki *Smash attack* | [secondary] | "may be charged for up to **60 frames**, or 1 second" — stated for **all** games Melee→Ultimate | Melee/Brawl/4/Ult |
| SmashWiki *Project M* | [secondary] | "chargable for **59 frames** as opposed to 60" | PM |
| brawllib_rs (`~/Documents/Study/Rust/`, #614) | — | **no charge-cap constant** — only `ShieldCharge` (unrelated) and the `SmashSwingItemCharge` action *name* | — |

The 59 comes from **one** secondary, the SmashWiki *Project M* page, and it **contradicts
SmashWiki's own general *Smash attack* article**, which puts every game at 60. No primary was
found either way for PM specifically.

### Why no PM primary is reachable

The smash charge **cap is an engine-hardcoded global**, not per-move subaction script data — so
it is **out of brawllib_rs / rukaidata scope** (confirmed here: brawllib_rs exposes no such
constant; consistent with memory `rukaidata-engine-hardcoded-limit` and the #215/#222
air-dodge-velocity precedent). PM itself was never open-sourced (Nintendo C&D, 2015). The
Sammi-Husky *Project-Smash-Attacks* PSA changelog is **silent** on charge duration. Project+
(the open continuation) ships its engine changes as a build/codeset, not grep-able source with
this literal. **The only path to a PM primary is a DOL / live-memory dump of a PM ISO** — outside
this spike's box.

---

## Routing the outcome

Per the ticket's three options — upgrade provenance / revert to 60 / mark `⚠ undocumented` —
the two config values route differently:

| Value | Now (#599) | Finding | Recommended route |
|---|---|---|---|
| `SMASH_CHARGE_SCALE` | `1.3671` | **primary-confirmed** (meleelight, Melee lineage) | **Upgrade** the provenance note — add the meleelight primary citation alongside SmashWiki. Value unchanged. |
| `SMASH_CHARGE_FRAMES` | `59` | single-secondary, **primary-unconfirmed**, contradicted by SmashWiki's general article | **Keep 59, downgrade the note** to `⚠ primary-unconfirmed` (see rationale). Value unchanged. |

**Why keep 59 rather than revert to 60.** #599 established the reconciliation rule that a
**PM-specific** source outranks a **general** Melee/Brawl value applied to PM. This spike does
not overturn that rule — it only shows the PM-specific claim lacks a *primary* and disagrees with
a *general* (non-PM) article. Reverting to 60 would substitute a general value for the
PM-specific one — the exact move #599 corrected away from — and would cost another #588 combat
golden regen for a **1-frame, sub-1%-damage** difference. Lowest-churn, most internally
consistent route: **keep the value, mark the weak sourcing honestly.**

**Escalation note (parity vs. sourcing).** Whether a PM-faithful game should hold a
PM-specific-but-primary-unconfirmed 59 over a better-sourced 60 is ultimately a
**parity-vs-provenance design judgment**, not a pure research finding. This doc recommends keep-59;
if the maintainer prefers the better-sourced 60, that is a defensible `decision:`/designer call
(record as `TUNED`, not `FOUND`). Either way it is a **value-neutral provenance edit or a
1-line config change**, not new mechanics.

---

## Recommendation & follow-up

- **No config value changes in this ticket** (research only; both numbers stay as #599 set them).
- **Recommended follow-up (one DEV ticket, filed downstream on go-ahead):** in
  `pycats/combat/provenance.py`, (a) add the meleelight primary citation to the
  `SMASH_CHARGE_SCALE` row, and (b) annotate the `SMASH_CHARGE_FRAMES` row `⚠ primary-unconfirmed
  — single secondary (SmashWiki:Project_M), contradicted by SmashWiki:Smash_attack (60, all
  games); primary needs a PM DOL/memory dump`. Value-neutral; `test_tuning_provenance.py` stays
  green (no number changes).
- Update `smash-charge-hold.md` Q4's "primary" mislabel → "secondary" (fold into the same
  follow-up or #625's doc pass).

## Update (#649) — GCT disassembly: the codeset does **not** hold the charge values as literals

Static analysis of the vanilla PM 3.6 codeset `RSBE01.gct` (staged by #640; 64,352 bytes / 8,044
Gecko codes; valid header `00d0c0de…` + terminator `f0000000…`), plus a byte search across the
**whole** extracted build (`pf/module/*.rel` etc.):

- **`1.3671` (float32 BE `3faefd22`) — absent** from the GCT and from every file in the build.
- **`0.3671` (`3ebbf488`) and the per-frame `0.3671/60` (`3bc87c4d`) — absent** everywhere.
- **Brawl's `1.4` (`3fb33333`) — present**, but only inside an **unidentified embedded
  multiplier table** in the GCT (near byte offset ~45,836: `…3fb33333…3fb33333…3faaaaab…` =
  1.4, 1.4, 1.333, among 0.91 / 1.167 / 1.579). Without a `main.dol` symbol map this table can
  **not** be tied to the smash-charge mechanic — it could be any scaling table.
- **`59` / `60`** are too low-signal to locate in ASM without symbols.

**Interpretation.** Smash charge is **global engine** behavior — it lives in Brawl's `main.dol`
(not shipped in this Homebrew set; PM hooks it via Gecko codes), and the per-fighter `ft_*.rel`
modules hold no global charge logic. The absence of any `1.3671`/`0.3671` literal means PM does
**not** store the Melee multiplier as a discoverable constant in the codeset — the computation is
engine ASM without an extractable literal.

**Correction.** This **retracts the earlier optimism** (in #640's notes and this doc's premise)
that `RSBE01.gct` would be a clean offline primary for these values. For the smash-charge ramp and
multiplier specifically, **the codeset is insufficient** — it neither confirms nor refutes 59 or
1.3671.

**Lead (unverified).** *If* the multiplier table at ~45,836 were the smash-charge table, its `1.4`
would suggest PM kept Brawl's multiplier (refuting SmashWiki's `1.3671`). That is an **unconfirmed
inference** — do not act on it; it needs symbol-mapped identification.

**Route.** #637 stays `⚠ primary-unconfirmed`. The remaining primary paths are (a) analyze
**`main.dol`** against the **`doldecomp/brawl`** symbol map to find the charge routine by name, or
(b) the **live Dolphin RAM read** at the charge-computation site (needs the Brawl ISO). Both are
later #638 children; neither is opened here.

## 2026-08-05 — `doldecomp/brawl` symbol-map route tested (#1249): dead-end

The prior "Route" note's **option (a)** — "analyze `main.dol` against the `doldecomp/brawl`
symbol map to find the charge routine **by name**" — was tested here (#1249, the #652
"viable-with-X" child). **It does not reach the value.** Recorded so option (a) is not re-attempted.

**Source read.** `doldecomp/brawl` @ commit **`d2ed7c96946f8eb8b34a0d085ed371ca257b0387`**
(`main`, pushed 2026-06-22), read via the GitHub API against that pinned SHA rather than a local
clone — the probe below closes the route before a 5 MB gitignored checkout would add evidence, and
reading raw blobs at the pinned commit is the same authoritative data. (Ticket scoped a clone +
recorded clone SHA; substituting "read @ pinned SHA" yields the identical files and the same
finding. The pinned SHA above is the provenance anchor.)

**Probe (all against `config/RSBE01_02/symbols.txt` @ that SHA — 34,802 symbols, 20,448
`type:object` data entries; the full DOL symbol map, every entry mangled-named, no `func_` stubs):**

- `grep -i 'charge|smash|tame|hold'` over **all** 34,802 symbols → **1 hit**:
  `create__20IfFoxSmashAppearTaskFP9gfArchive` (`.text:0x800F6374`) — Fox's on-screen-appearance
  task, unrelated to smash-attack charging. `grep 'Smash'` (case-sensitive) count over the whole
  map = **1** (the same line).
- Over the 20,448 `type:object` data symbols, `smash|charge|attack|tame|hold|squat` → **0 hits**.
  No named data constant for a charge cap/multiplier.
- Repo code-search (`gh api search/code repo:doldecomp/brawl`) for `SmashCharge`, `smash_charge`,
  `ChargeFrame`, `charge_frame`, `SmashHold`, `smashHold` → **0** each.
- Decompile coverage of the fighter engine is near-zero: `src/sora/ft/` (the HAL/Sora fighter
  engine module) holds only `ft_system.cpp`; `src/mo_fighter/` holds only `ft_marth`, `ft_purin`,
  and a **592-byte** `mo_fighter.cpp` stub; `include/` is entirely `st_*` stage headers — no
  fighter param header. The generic smash-charge status handler is **not** decompiled.

**Why the route dead-ends (two independent reasons).**

1. **Not a discoverable named symbol.** The charge cap/multiplier is not exposed as a named
   function or data object — 1 of 34,802 symbols matches any charge vocabulary and it is unrelated.
   Searching the map by name cannot surface it.
2. **It is an inline ASM immediate, and the map only maps _address → name_.** Even granting the
   map names every address, extracting the value needs the **DOL bytes at a known address** (to
   read the immediate in the `cmpwi …, 60`-style compare). That requires either the target
   **address** — which #649 established the PM GCT does **not** carry (no `59`/`60`/`1.3671`
   literal in the diff; a Brawl-inherited value never appears in a diff at all) — or the **`main.dol`
   itself**, which is ISO-gated (the no-ISO premise of this route). No address + no DOL ⇒ the symbol
   map cannot be anchored to the charge site.

**No value extracted.** `SMASH_CHARGE_FRAMES` (59) stays **`⚠ primary-unconfirmed`**;
`SMASH_CHARGE_SCALE` (1.3671) is unchanged (already **[primary]**-confirmed via meleelight, above).

**Route update for #637.** Option (a) is now closed as insufficient on its own. Remaining primary
paths:
- **(b) live Dolphin RAM read at the charge-computation site — #1250** (ISO-gated): reads the value
  regardless of naming; the only offline route that does not depend on a named symbol. This is now
  the **leading** reachable primary.
- **(c) new lead — `doldecomp/melee`** (a *different* decomp, far more complete than Brawl's): PM
  restores Melee's smash-charge behavior, and the meleelight **[primary]** already gives **60** for
  Melee; the Melee decomp could corroborate the ramp at engine-source level (named function + the
  immediate in decompiled C). This is **outside #1249's scope** (a Brawl-decomp ticket) and
  `doldecomp/melee` is cited-but-not-cloned (#1239 finding) — a **candidate follow-up**, not opened
  here.

## Sources

- doldecomp/brawl (partial Brawl decomp — no named charge symbol, fighter engine un-decompiled) —
  <https://github.com/doldecomp/brawl> @ `d2ed7c9`; `config/RSBE01_02/symbols.txt` (34,802 symbols)
- meleelight (Melee engine reimpl, **[primary]** literal) — `~/Documents/Study/JavaScript/meleelight/src/characters/*/moves/*SMASH.js` (clone #616)
- brawllib_rs (no charge-cap constant) — `~/Documents/Study/Rust/brawllib_rs/src/` (clone #614)
- SmashWiki — *Smash attack*: <https://www.ssbwiki.com/Smash_attack> (60 frames, all games; 1.3671× Melee / 1.4× Brawl+)
- SmashWiki — *Project M*: <https://www.ssbwiki.com/Project_M> (the sole "59 frames / x1.3671" source)
- Sammi-Husky *Project-Smash-Attacks* PSA changelog (silent on charge duration): <https://github.com/Sammi-Husky/Project-Smash-Attacks/blob/master/PSA/Changelog.txt>

## Refs

Spun out of #599 (charge-value corrections) via the #588 charged-fsmash golden. Companion:
`docs/pm-reference/smash-charge-hold.md` (#595), `docs/research-120-smash-units-and-sources.md`,
`docs/pm-reference/where-to-find-source-data.md` (#617/#625). Sourcing discipline: memories
`pm-parity-cite-primary-not-inference`, `rukaidata-engine-hardcoded-limit`.
