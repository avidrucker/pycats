# Open-source Melee / Brawl / Project M implementations — code sources for porting engine values (#224)

> Companion to [`research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md):
> that doc catalogs **data** sources (wikis, framedata sites); this one catalogs **code**
> sources — decompilations, faithful reimplementations, datamine tools, and mod/codesets
> whose source can be *inspected* to recover engine values and models.
>
> Motivation: the air-dodge magnitude (#215) couldn't be sourced from rukaidata/SmashWiki
> (engine-hardcoded), but fell straight out of open-source code — the Melee decomp gave the
> model and `meleelight` gave the literal `escapeair_force = 3.1`. The archetype epic (#117)
> and the remaining `GUESSED_VALUES` rows (#192, #218) will keep needing this, so the sources
> are catalogued here once.
>
> Method: each repo verified live via `gh repo view` (language / license / last-push / stars /
> archived). Date: 2026-06-29. Agent: DRAGONFRUIT. Area: `area:combat`.

## ⚖ Legal / licensing caveat (read first)

These are decompilations and mods of Nintendo's copyrighted games; **almost none carry an OSI
license** (the "License" column below is `none` nearly everywhere). Use them to **understand
mechanics and read numeric values/models** — pycats then writes its *own* implementation. This
is exactly how #215 worked: we read that Melee sets `self_vel = escapeair_force × (cosθ,sinθ)`
with `escapeair_force = 3.1`, then implemented pycats' own `_start_dodge`. **Port values and
models, not source code.** Treat anything here as reference, not a code dependency.

## TL;DR — where to look for X

| You need… | Go to | Notes |
|---|---|---|
| An **engine-hardcoded constant** (air-dodge speed, friction model, deadzones, per-frame decay) | a **decompilation** (`doldecomp/melee` or `doldecomp/brawl`) for the *model* + a **reimplementation** (`meleelight`) for the *literal* | NOT in rukaidata/SmashWiki (see [`rukaidata-engine-hardcoded-limit`]). Cross-check vs PlCo.dat (Magus SSBM Data Sheet). |
| **Per-move framedata / hitboxes** (size, position, damage, BKB, KBG, angle) | **rukaidata** (PM3.6 / Project+) | Spatial values × `PX_PER_UNIT≈5.4`. This is the PM-native move source (how `nalio_cat.py` was authored). |
| **Character attributes** (walk/dash/air/gravity/fall/traction/weight) | **rukaidata** attributes table + SmashWiki PM pages | e.g. Mario PM traction 0.06 (#218). |
| A **clean JSON framedata pipeline** | `pfirsich/meleeDat2Json` + `meleeFrameDataExtractor` (Melee) | Best pure-JSON tooling, but Melee-only. |

**Key structural finding:** there is **no standalone Project M / Project+ decompilation** —
PM/Project+ is **Brawl + a custom ASM/Gecko codeset**, not its own codebase. So for
PM-faithful engine values:
- values PM **inherited from Melee unchanged** → `doldecomp/melee` + `meleelight` (cleanest, readable);
- the Brawl **engine base** → `doldecomp/brawl`;
- PM-**specific deltas** → the Project+ codeset/build projects (ASM) + rukaidata PM3.6 (move data).

---

## 1. Decompilations — the engine model (C)

Reverse-engineered, matching C source of the actual game. The authoritative source for *how*
a mechanic works and which hardcoded constants it reads.

| Repo | Game | Lang | License | Last push | ★ | Exposes / use |
|---|---|---|---|---|---|---|
| ⭐ [`doldecomp/melee`](https://github.com/doldecomp/melee) | Melee | C | none | 2026-06 (active) | 927 | The engine model. e.g. `src/melee/ft/chara/ftCommon/ftCo_EscapeAir.c` = air dodge (used in #215). Fighter common-data field names/offsets in `types.h`. |
| ⭐ [`doldecomp/brawl`](https://github.com/doldecomp/brawl) | Brawl | C | none | 2026-06 (active, WIP) | 68 | Brawl engine = **PM's foundation**. Use for PM-faithful Brawl-engine behaviour the Melee decomp doesn't cover. |

## 2. Faithful reimplementations — physics as readable literals

Clean re-codings of the engine in a high-level language, so constants appear as plain literals.

| Repo | Game | Lang | License | Last push | ★ | Exposes / use |
|---|---|---|---|---|---|---|
| ⭐ [`schmooblidon/meleelight`](https://github.com/schmooblidon/meleelight) | Melee | JS | none | 2023-08 | 412 | Browser Melee. **Source of `escapeair_force = 3.1`** (#215): `src/characters/shared/moves/ESCAPEAIR.js`. Many physics constants as literals. |
| [`xavierloeraflores/meleelight-ts`](https://github.com/xavierloeraflores/meleelight-ts) | Melee | TS | none | 2026-05 (active) | 0 | TypeScript port of meleelight — more recently maintained; same values, typed. |

## 3. Datamine tools / framedata extractors

Parse the game's data files into structured framedata/hitboxes. **Spatial move data only** —
NOT engine-hardcoded constants (those live in code/PlCo.dat, not the per-character `.dat`/`.pac`).

| Repo | Game | Lang | License | Last push | ★ | Exposes / use |
|---|---|---|---|---|---|---|
| ⭐ [`rukai/rukaidata`](https://github.com/rukai/rukaidata) (`brawllib_rs`) | PM / Brawl | Rust | none | 2025-10 | 9 | Powers [rukaidata.com](https://rukaidata.com); per-subaction hitboxes + attributes for **PM3.6 / Project+**. The PM-native move/hitbox source. |
| [`pfirsich/meleeDat2Json`](https://github.com/pfirsich/meleeDat2Json) | Melee | Python | none | 2024-05 | 8 | `.dat` → JSON character/move dump. |
| [`pfirsich/meleeFrameDataExtractor`](https://github.com/pfirsich/meleeFrameDataExtractor) | Melee | Python | none | 2021-01 (stale) | 14 | JSON framedata (powers meleeframedata.com). |
| [`altf4/libmelee`](https://github.com/altf4/libmelee) | Melee | Python | none | 2026-01 (**archived**) | 255 | Slippi/Dolphin AI API + `framedata`. Values "sanitised for bots" — cross-check, don't treat as binary-exact. |

## 4. Mods / codesets / tools — constants & offsets via ASM/Gecko

Modify the live game; their source/code-libraries name PlCo.dat offsets and engine constants.
Most relevant when you need a *file offset* or a Gecko code's documented default.

| Repo | Game | Lang | License | Last push | ★ | Exposes / use |
|---|---|---|---|---|---|---|
| [`akaneia/m-ex`](https://github.com/akaneia/m-ex) (MexTK) | Melee | Asm/C | none | 2026-06 (active) | 40 | Melee extension toolkit; `include/fighter.h` mirrors fighter/common-data structs. |
| [`UnclePunch/Training-Mode`](https://github.com/UnclePunch/Training-Mode) | Melee | Asm/C | none | 2024-07 | 355 | 20XX-style training mod; shows how code reads `PLCO_FTCOMMON` common data. |
| [`AltimorTASDK/ssbm-1.03`](https://github.com/AltimorTASDK/ssbm-1.03) | Melee | C++ | none | 2026-05 (active) | 26 | SSBM 1.03 build/disasm; `GALP01.map` has labelled symbols (`Interrupt_AS_EscapeAir_Airdodge`, `plco`). |
| [`AltimorTASDK/ucf`](https://github.com/AltimorTASDK/ucf) · [`AltimorTASDK/lab`](https://github.com/AltimorTASDK/lab) | Melee | C++ | none | 2023 / 2022 | 6 / 10 | Universal Controller Fix; training/research mod (`src/display/actions.cpp` references `plco->angle_*`). |
| [`RighteousRyan1/ExternalMeleeTool`](https://github.com/RighteousRyan1/ExternalMeleeTool) | Melee | C# | none | 2026-04 (active) | 3 | C# struct mirror of fighter common data (`escapeair_force` etc.) — readable field layout. |
| [`Achilles1515/20XX-Melee-Hack-Pack`](https://github.com/Achilles1515/20XX-Melee-Hack-Pack) · [`DRGN-DRC/20XX-HACK-PACK`](https://github.com/DRGN-DRC/20XX-HACK-PACK) | Melee | Python/Asm | none | 2019 / 2023 | 132 / 80 | Gecko code libraries; codes document PlCo.dat offsets + original/replacement values. |
| [`AeonSSB/PM-PORTING-BUILD-PROJECT`](https://github.com/AeonSSB/PM-PORTING-BUILD-PROJECT) · [`FunctionDJ/project-plus-assets`](https://github.com/FunctionDJ/project-plus-assets) | **PM / Project+** | Asm | none | 2026 / 2021 | 2 / 5 | The closest thing to "PM source": Project+ porting/build + an asset mirror. PM = Brawl + this codeset. |

## Liveness summary (2026)

- **Actively pushed in 2026:** `doldecomp/melee`, `doldecomp/brawl`, `akaneia/m-ex`,
  `AltimorTASDK/ssbm-1.03`, `xavierloeraflores/meleelight-ts`, `RighteousRyan1/ExternalMeleeTool`,
  `AeonSSB/PM-PORTING-BUILD-PROJECT`.
- **Inspectable but stale (>1y):** `schmooblidon/meleelight` (2023), `meleeFrameDataExtractor`
  (2021), the 20XX packs (2019/2023), `ucf`/`lab` (2022–23).
- **Archived (read-only but intact):** `altf4/libmelee`.
- **Gone / dead:** none of the catalogued sources were missing or deleted.

## Cross-refs
Companion to `research-120-smash-units-and-sources.md`. Arose from #215 (air-dodge magnitude).
Serves #117 (archetype epic), #192 / #218 (remaining air-dodge values + traction). See the
`rukaidata-engine-hardcoded-limit` finding for *why* engine constants need these code sources
rather than the wikis.
