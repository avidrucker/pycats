# Parity data-source capability catalog (#1239)

> **What this is:** a single reference inventory of **every data source pycats has used**
> for Project M / Smash-lineage parity, stating for each one — from **observation** where
> feasible (2026-08-05 probes) — *what it contains*, its *lineage rung + fidelity tier*, and
> *what is obtainable in our environment* vs what needs an artifact we do not have.
>
> **This is a capability map, not a standard.** It does not decide source priority, rank
> ties, or change any value — that is the provenance-standard ARC ticket (#1240), which this
> doc feeds. See "Out of scope."
>
> **Complements, does not replace:** [`../pm-reference/where-to-find-source-data.md`](../pm-reference/where-to-find-source-data.md)
> is the *decision map* ("for data type X, which source?"). This doc is the *per-source
> capability + obtainability* matrix ("for source S, what can it give us **here**, and where
> is its ceiling?"). The #1223 case — CPU decision *logic* decodable from doldecomp but the
> per-character AI *weight tables* being runtime data not in that source — is the exact
> question this catalogs once, for every source.

## Conventions

**Lineage rung** — where the datum originates in the Smash family. PM is a Brawl mod that
restored much Melee behavior, so a value can trace to any of:

- **PM** — a Project M build / codeset / PM-specific override (the retail target).
- **Brawl** — base-Brawl engine or scripted data PM inherited unchanged.
- **Melee** — Melee behavior PM restored; authoritative for values PM took verbatim.
- **meleelight** — a faithful **reimplementation** of Melee (not the retail ROM); a
  SECONDARY proxy for a Melee/PM literal, but a direct read of engine *logic*.

**Fidelity tier** — **T1 primary** (the actual build data / decompiled retail source /
running build RAM) vs **T2 secondary** (prose, a reimplementation's magnitude, a
community frame-data thread). A reimplementation is T1 for the *state-machine logic* it
encodes but T2 for any retail *magnitude* it asserts.

**Setup state legend:** ✅ live locally · 🌐 online-only (reachable) · ⛔ blocked/unreachable
· 🧩 partial (env staged, gated on a missing artifact).

---

## Summary matrix

| # | Source | Rung | Tier | Setup (2026-08-05) | Holds | Obtainable **here** — ceiling |
|---|--------|------|------|--------------------|-------|-------------------------------|
| 1 | rukaidata (PM3.6) | PM | T1 (moves) | 🌐 200 OK | per-move hitbox geometry+timing, BKB/KBG/angle/size, scripted self-vel | HTTP fetch of HTML pages. **No engine globals.** |
| 2 | brawllib_rs | PM (over Brawl base) | T1 | ✅ `@e8dc833`, .pac live | per-move hitboxes, FighterAttributes (walk/dash/run/grav/jump/weight), anim frame lengths, subaction scripts | Full, via cargo. **Panics on stage .pac; no engine globals.** |
| 3 | meleelight | meleelight (Melee reimpl) | T1 logic / T2 magnitude | ✅ `@27af171` | engine state machine: hitlag/immunity, air-dodge, crouch-cancel, charge mult 1.3671, drift/friction | Read JS source directly. **Reimpl, not retail ROM; PM overrides absent.** |
| 4 | doldecomp/melee | Melee | T1 | 🌐 online-only — **not cloned** | Melee decompilation: engine logic/model + symbol-traceable literals | GitHub/web only; **no local checkout, no pinned SHA** (citations lean on meleelight as the local stand-in). |
| 5 | SmashWiki / ssbwiki | Melee/Brawl/PM | T2 | 🌐 200 OK | prose + documented formulas (KB terms, hitstun, shieldstun, hitlag, Sakurai angle, per-char pages) | HTTP fetch. **Secondary; prefer a PM page over a general value.** |
| 6 | Project-M-CC codesets | PM | T1 (overrides) | ✅ local text (3.6/3.61) | PM-specific engine overrides — the "what changed" (Gecko/PSA codes) | grep the named CC codeset locally. **A code = ASM; reading a global means decoding, not grep.** |
| 7 | OpenSA / dantarion | Brawl | T1 (Brawl actions) | ⛔ **000 unreachable** | Brawl engine action/state script data (action IDs, intangibility windows) | **None right now — host down, no local mirror.** Partial cover via brawllib_rs + SmashWiki Brawl. |
| 8 | Smashboards / Liquipedia | Melee/PM | T2 | 🧩 human-only (403 to bots) | community frame-data threads (e.g. getup-roll frames), competitive prose | **Manual browser only — automated fetch 403s.** |
| 9 | stage-bounds datamine | PM (stage .pac) | T1 | ✅ `scripts/datamine_stage_bounds.py` | stage blast/camera/spawn bounds (Dead/CamLimit/Player/Rebirth bones) | Pure-stdlib script, needs the stage .pac. **Fills the gap brawllib can't (it panics on stages).** |
| 10 | PM globals RAM-dump (Dolphin+Riivolution) | PM (running build) | T1 | 🧩 env staged, gated | engine-hardcoded globals no offline primary exposes (e.g. smash charge cap) | **Blocked on a clean legal NTSC-U Brawl ISO + the extraction child of #638.** |

---

## Per-source detail

### 1 · rukaidata (rukaidata.com, PM 3.6)
- **What it is:** a web rendering of the actual PM 3.6 fighter `.pac` subaction scripts.
  URL pattern `https://rukaidata.com/PM3.6/<Fighter>/subactions/<Subaction>.html`.
- **Setup:** 🌐 online-only, **reachable** — `AttackS4S` page returned `200` on 2026-08-05.
- **Rung / tier:** PM · T1 primary for per-move data (it is the PM build's own script data).
- **Holds:** per-move hitbox geometry + timing, damage, BKB/KBG/angle/size/positions,
  scripted self-velocity.
- **Obtainable here:** yes — HTTP fetch + HTML parse (or the bincode payload). No auth.
- **Ceiling / gotcha:** exposes **only** per-move subaction scripts. Engine-hardcoded
  globals (gravity as an engine constant, air-dodge force, L-cancel, the smash-charge cap)
  are **not** here — route those elsewhere ([[rukaidata-engine-hardcoded-limit]], #215/#222).

### 2 · brawllib_rs
- **What it is:** the `rukai/brawllib_rs` Rust library, reading raw `.pac` archives.
- **Setup:** ✅ live — clone `~/Documents/Study/Rust/brawllib_rs` `@e8dc833`; PM data at
  `~/Documents/Study/Rust/pm-data/{brawl-dump/DATA/files (-d), pm36-sd (-m)}` (both present:
  22 / 1 entries). Needs cargo (`. ~/.cargo/env`; not on the non-login PATH).
- **Rung / tier:** feeds it Brawl base `-d` + PM 3.6 overlay `-m` → effectively **PM** · T1.
- **Holds:** per-move hit boxes (via `scripts/brawllib/hitbox_dump.rs`), per-fighter
  `FighterAttributes` (walk/dash/run max, gravity, base + fast-fall terminal, full/short-hop
  jump vel, double-jump mult, jump count, weight — via `datamine_fighter_attributes.sh`),
  animation frame lengths (Wait1=51f, [[brawllib-datamine-env-live]]), subaction scripts.
- **How to run:** `scripts/datamine_hitboxes.sh <Fighter> <Subaction> [out.json]`;
  `scripts/datamine_fighter_attributes.sh <out.csv>`. Recipe:
  `docs/tooling-brawllib-rs-datamine-recipe.md`.
- **Obtainable here:** yes, fully offline.
- **Ceiling / gotcha:** **panics on any stage `.pac`** (`arc::arc()` assumes ARC-child-0 is a
  fighter `Sakurai` block; backtrace at `sakurai::arc_sakurai`) — use source 9 for stages.
  **No engine globals** (same limit as rukaidata — it reads scripts + attributes, not
  hardcoded constants).

### 3 · meleelight
- **What it is:** `schmooblidon/meleelight`, a faithful **JS reimplementation** of Melee.
- **Setup:** ✅ live — clone `~/Documents/Study/JavaScript/meleelight` `@27af171`. Engine
  logic under `src/physics/` (`physics.js`, `hitDetection.js`, `damageTypes.js`, …),
  `src/characters/`, `src/animations/`.
- **Rung / tier:** meleelight · **T1 for the state-machine logic** it encodes,
  **T2 for any retail magnitude** it asserts (a SECONDARY proxy for undocumented PM values —
  see the `@27af171 physics.js` provenance entries tagged "SECONDARY proxy").
- **Holds:** the engine hit-resolution / hitlag / immunity **state machine**
  ([[meleelight-engine-logic-source]]), air-dodge (`ESCAPEAIR.js`), crouch-cancel scale,
  smash full-charge multiplier (`1 + chargeFrames*(0.3671/60)` → 1.3671), drift/friction.
  Use for engine-globals the per-move datamines can't answer.
- **Obtainable here:** yes — read the source files directly.
- **Ceiling / gotcha:** it is a **reimplementation, not the retail ROM** — a magnitude is the
  author's reading of Melee, and **PM-specific overrides are not captured** (PM ≠ Melee where
  PM changed a value).

### 4 · doldecomp/melee
- **What it is:** the `doldecomp/melee` decompilation of retail Melee (GALE01).
- **Setup:** 🌐 **online-only — NOT cloned locally** (searched `~/Documents/Study` and `$HOME`:
  no checkout, no pinned SHA). Cited in `pycats/combat/provenance.py` (e.g.
  `escapeair_force=3.1u/f`), but the **local** stand-in for those citations is meleelight —
  the doldecomp reference itself is not reproducible offline here.
- **Rung / tier:** Melee · T1 primary (decompiled retail source).
- **Holds:** Melee engine logic/model + literals traceable to named symbols; the authoritative
  source for a Melee-inherited constant PM restored unchanged.
- **Obtainable here:** **online only** — needs a fresh clone or web fetch of a specific file,
  and any citation should **record the SHA** (none is pinned today).
- **Ceiling / gotcha:** **runtime data is not in the source** — the #1223 finding: Melee CPU
  decision *logic* is decodable from doldecomp, but the per-character CPU-AI *weight tables*
  are runtime data that need a Melee `GALE01` DOL/RAM dump we do not have.

### 5 · SmashWiki / ssbwiki
- **What it is:** the community wiki. `https://www.ssbwiki.com/<Page>`.
- **Setup:** 🌐 reachable — `Project_M` page `200` on 2026-08-05.
- **Rung / tier:** cross-lineage (Melee/Brawl/PM pages) · **T2 secondary** (the repo's citable
  secondary tier).
- **Holds:** documented formulas the registry already cites — knockback terms (§2 of spec #39),
  hitstun 0.4/unit, shieldstun 0.345, hitlag (Brawl-onward cap, 1/2.6 d-term), Sakurai-angle
  361 sentinel, wavedash values, and per-character pages (`Mario_(PM)` gravity/jump).
- **Obtainable here:** yes — HTTP fetch.
- **Ceiling / gotcha:** secondary. For a PM-specific number prefer the **PM** page/changelog
  over a general Melee/Brawl value; prose is not always the exact engine literal.

### 6 · Project-M-CC codesets (the PMDT-changelog local channel)
- **What it is:** `~/Documents/Study/reference/Project-M-CC` — PM codesets in **text**.
  `[Dev Resources]/codes-3_6.txt` is the nameless 1:1 text mirror of vanilla `RSBE01.gct`;
  `[Text Codesets]/codes-cc-3_6.txt` is the **named** CC codeset (read Gecko codes by name).
  Also 3.61 variants + `changelist-3_61.png`.
- **Setup:** ✅ local text (#664).
- **Rung / tier:** PM · T1 primary for PM-specific overrides (it is the actual codeset).
- **Holds:** the PM-specific engine changes — the "*what changed*" relative to Brawl.
- **Obtainable here:** yes — grep the named CC codeset locally.
- **Ceiling / gotcha:** a code is Gecko/ASM — extracting a specific global **value** means
  **decoding the code**, not a plain grep; `changelist-3_61.png` is an image (not text-searchable).
  Online PMDT changelog host status is still to-verify (see source-data doc "To-verify").

### 7 · OpenSA / dantarion — ⛔ BLOCKED
- **What it is:** dantarion's OpenSA, Brawl moveset/action script browser.
- **Setup:** ⛔ **unreachable** — `opensa.dantarion.com` (http + https) and `dantarion.com`
  all returned connection failure (`000`) on 2026-08-05. Not a bot-block (a `403` would
  answer); the host does not respond. No local mirror.
- **Rung / tier:** Brawl · T1 for Brawl engine action/state data.
- **Holds:** Brawl engine action IDs, state script data, intangibility windows.
- **Obtainable here:** **none right now.** Partial substitutes: brawllib_rs covers much Brawl
  **scripted** data; SmashWiki Brawl covers action/state prose.
- **Action for the human:** if OpenSA data is needed, it likely requires a mirror / archive.org
  copy or an alternative host — flagged below.

### 8 · Smashboards / Liquipedia
- **What it is:** community forums / competitive wiki (frame-data threads, e.g. the getup-roll
  35f / intangible-frame data cited in provenance; Liquipedia competitive prose).
- **Setup:** 🧩 `smashboards.com` returned **403 to a scripted User-Agent** on 2026-08-05 —
  reachable by a human browser, not by automated fetch. (Liquipedia not separately probed;
  generally online.)
- **Rung / tier:** secondary · T2.
- **Holds:** community frame data + competitive prose used as secondary cross-checks.
- **Obtainable here:** **manual browser only** for Smashboards — cite by hand, don't script it.

### 9 · stage-bounds datamine (`scripts/datamine_stage_bounds.py`)
- **What it is:** a bespoke **pure-stdlib** reader for a stage `.pac`: LZ10-decompresses ARC
  children, walks MDL0 bone headers, prints boundary bones.
- **Setup:** ✅ in-repo, no brawllib needed. Needs a stage `.pac`.
- **Rung / tier:** reads the PM/Brawl stage `.pac` → **PM** · T1.
- **Holds:** stage blast (`Dead0N/Dead1N`), camera (`CamLimit`), spawn (`Player`), respawn
  (`Rebirth`) bounds. PM 3.6 FD blast = `(-246,246,188,-140)` = Melee's exact floats (#790,
  [[stage-bounds-datamine]]).
- **Obtainable here:** yes.
- **Ceiling / gotcha:** exists **because** brawllib_rs cannot read stage pacs (source 2's
  panic). This is the stage-geometry route.

### 10 · PM globals RAM-dump (Dolphin + Riivolution) — 🧩 the engine-globals route
- **What it is:** run a real PM 3.6 build in Dolphin (Riivolution-patched over a clean Brawl
  ISO) and read **engine-hardcoded globals** from RAM — the only primary for constants no
  offline datamine exposes (the #626/#637 smash charge-frame cap).
- **Setup:** 🧩 **partial** — Dolphin + built-in Riivolution done (#639); PM 3.6 codeset
  acquired + MD5-verified (#640); **still needs** a clean legal NTSC-U Brawl ISO (the user's
  own dump, MD5 vs Redump) **and** the extraction child of #638. Setup doc:
  `docs/pm-reference/pm-globals-dump-setup.md`.
- **Rung / tier:** PM (live retail build RAM) · T1 primary.
- **Holds:** any engine-hardcoded global — the category rukaidata/brawllib structurally cannot
  give (charge caps, engine constants).
- **Obtainable here:** **not yet** — gated on the legal Brawl ISO + the extraction step.
  This names the ceiling for the whole "engine-hardcoded globals" category.

---

## Cross-cutting obtainability ceilings

The categories that our local environment **cannot** reach today, and what each needs:

1. **Engine-hardcoded globals** (smash charge cap, non-scripted engine constants) — absent
   from rukaidata + brawllib_rs by design. Route: decode the PM codeset (source 6) **or**
   the Dolphin RAM-dump (source 10, blocked on a legal Brawl ISO).
2. **doldecomp/melee** — cited but **not cloned**; the local proxy is meleelight (a reimpl, not
   the decompiled retail source). A doldecomp citation is online-only and unpinned today.
3. **Brawl engine action/state data** — OpenSA host is **down**; no reachable primary right
   now. brawllib_rs (scripted) + SmashWiki Brawl (prose) partially cover it.
4. **CPU-AI weight tables** — runtime data **not in doldecomp source**; needs a Melee `GALE01`
   DOL/RAM dump we do not have (the #1223 case; parallels the PM globals ceiling).
5. **Smashboards** — automated fetch blocked (403); manual browser only.

## Reachability probe log (2026-08-05)

| Target | Result |
|---|---|
| `rukaidata.com/PM3.6/Mario/subactions/AttackS4S.html` | `200` |
| `www.ssbwiki.com/Project_M` | `200` |
| `opensa.dantarion.com` (http+https) / `dantarion.com` | `000` (connection failure) |
| `smashboards.com` | `403` (bot User-Agent blocked) |
| local clones: brawllib_rs `@e8dc833`, meleelight `@27af171`, Project-M-CC | present |
| local clone: doldecomp/melee | **absent** |
| pm-data `.pac`: `brawl-dump/DATA/files` (22), `pm36-sd` (1) | present |

## Blocked / flag-to-human

- **OpenSA / dantarion is down** (source 7) — if any Brawl action/state datum is needed from
  it, it needs a mirror or archive.org copy; not obtainable from the live host today.
- **doldecomp/melee is cited but not cloned** (source 4) — decide whether to clone + pin a SHA,
  or formally treat meleelight as the local proxy of record for those citations.
- **PM engine-globals RAM-dump is gated** on a legal Brawl ISO (source 10) — the user's action.

## Out of scope (per ticket)

- Deciding the source-priority standard / lineage ladder / PROVISIONAL token / FOUND split —
  that is the provenance-standard ARC ticket **#1240**, which this catalog feeds.
- Implementing any value change.
- Obtaining gated artifacts (a Melee ROM / DOL dump, a Brawl ISO) — this catalogs *whether and
  how* each dataset is obtainable, it does not obtain them.

## Refs

#1239 (this catalog) · #1223 (the CPU logic-vs-weight-tables decode that surfaced the
obtainable-vs-not gap) · #1240 (provenance-standard ARC — consumer) · CPU-fidelity epic #925 /
CPU epic #231 · ADR-0003 (provenance registry) · RULES cite-primary (#562) ·
`docs/pm-reference/where-to-find-source-data.md` (the decision-map companion) ·
`docs/pm-reference/pm-globals-dump-setup.md` · `docs/tooling-brawllib-rs-datamine-recipe.md`.
Memory: [[brawllib-datamine-env-live]], [[meleelight-engine-logic-source]],
[[rukaidata-engine-hardcoded-limit]], [[stage-bounds-datamine]], [[pm36-canonical-reference]].
