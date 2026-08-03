# PM 3.6 buff magnitudes + durations — datamine findings

Findings doc for **#1115** (thread B of tracker #1107). Adds the **quantitative** layer that
#1106's catalog (`docs/research/fighter-buffs-findings.md`) deferred and #1108
(`docs/research/pm36-buff-primaries-findings.md`) did not cover: exact per-buff magnitudes and
durations, each tagged by evidence strength.

## Bottom line

- **No value below is a PM-3.6 *primary* number.** Item magnitudes are **Brawl-inherited** (SmashWiki
  Brawl figures used as a 3.6 proxy — PM 3.6 inherits Brawl item behavior unless a changelog overrides
  it, and no per-item override was found in #1108). Frame counts are **Melee-inherited** (from
  `meleelight`, a Melee engine). Tag every value accordingly before using it.
- **The PM 3.6 "Light / Medium / Heavy" super-armor tier numbers are a documented GAP** — they are in
  no primary this hunt could read. The mechanism is known (per-move PSA `tolerance`, not a global tier
  table); the tier *values* are not. Per the ticket's constraint, this is flagged here rather than
  filled with an invented number. See §3 and §5.
- **Many item magnitudes are also GAPs** — SmashWiki gives Brawl numbers for some items and only
  Melee/SSB4/Ultimate numbers (or prose) for others. Gaps are enumerated in §4, not guessed.

## Evidence tags

| Tag | Meaning |
|-----|---------|
| **Brawl-inherited** | Verbatim SmashWiki Brawl figure, used as the PM 3.6 proxy. The strongest tier available here — still **not** a PMDT primary. |
| **Melee-inherited** | Verbatim value from `meleelight` (a Melee engine) — a proxy for the 3.6 frame count, weaker than a Brawl item figure. |
| **weak-quote** | Number derived from a page's per-game table, not a single quotable sentence. |
| **GAP** | No usable number found in any source. Not guessed. |

## Sources

- **SmashWiki** (`ssbwiki.com`) — per-item magnitudes/durations (Brawl figures where the page splits games).
- **`meleelight`** (`~/Documents/Study/JavaScript/meleelight/`, #616) — a JS Melee engine (5 fighters: marth/puff/falco/fox/falcon; **no items, no Lucario**). Source for intangibility/invincibility frame counts only.
- **`brawllib_rs`** (`~/Documents/Study/Rust/brawllib_rs/`, #614) — Rust PSA/`.pac` datamine. Models the armor *mechanism* and timer *slots*, but embeds no item magnitudes (those live in `item.pac` it does not carry).
- **`Project-M-CC`** (`~/Documents/Study/reference/Project-M-CC/`, #664) — the PM 3.6/3.6.1 Gecko codesets. Code **titles** are readable; the **magnitudes are assembled PPC/Gecko hex**, not plaintext-searchable. The named gameplay codes (armor, aura, dodges) live in the **3.61** codeset; the `codes-cc-3_6.txt` file is an 18-code cosmetic/clone subset with no gameplay codes. `changelist-3_61.png` is a binary image (unreadable).

---

## 1. Item magnitudes — Brawl-inherited (SmashWiki)

Each value carries a verbatim SmashWiki quote. All are **Brawl-inherited proxies**, not PM-3.6 primaries.

| Buff | Magnitude | Duration | Verbatim quote (SmashWiki) |
|------|-----------|----------|----------------------------|
| **Metal Box** | weight **4.5×**; fall-speed **2.0×** | **12 s** (shrinks as damage rises) | "4.5× in *Brawl*, *Smash 4*, and *Ultimate*" · "2.0× in *Melee* and *Brawl*" · "The effects last 12 seconds, but the time limit decreases as the fighter takes damage." |
| **Super Mushroom** | damage/knockback **1.56×** (listed chars **1.8×**) | **~10 s** | "1.56× from *Super Smash Bros. Brawl* onwards" · "The transformation lasts about ten seconds." (size/scale ×, and Brawl weight ×, are GAPs — see §4) |
| **Heart Container** | heal **100 percentage points** | instant | "Grab this and heal 100 percentage points of damage." |
| **Maxim Tomato** | heal **50%** | instant | "Beginning in *Super Smash Bros. Melee*, the Maxim Tomato heals 50% from a character's damage percentage." |
| **Superspicy Curry** | **1% per flame hit** | **13 s** | "for thirteen seconds" · "the flames deal only 1% per hit" |
| **Lightning** | others' attack power **0.7×** | GAP | "reducing their attack power to 0.7x." (shrink factor + duration are GAPs) |
| **Timer** | others slowed to **1/4 speed** | GAP | "slowed down to 1/4 of their normal speed" |
| **Warp Star** | **22% damage** (Melee figure, Brawl "same as Melee") | n/a | "an explosion that deals 22% damage and high knockback." (Brawl page: "acts the same as it did in *Melee*" — number not reprinted → weak-quote for Brawl) |
| **Screw Attack (item)** | up to **10 hits × 1%** | GAP | "up to ten hits for 1% damage each in *Super Smash Bros. Brawl* and *Super Smash Bros. 4*." |
| **Food** | top-end **9–12%**, majority **<6%** | instant | "The strongest food items recover only 9-12% of the player's health, with a majority often recovering below 6%." (per-game Brawl 1–12% range is table-derived → weak-quote) |

---

## 2. Intangibility / invincibility frame counts — Melee-inherited (meleelight)

`meleelight` cleanly separates `intangibleTimer` (intangibility) from `invincibleTimer` (invincibility),
decremented in `src/physics/physics.js`. These are **Melee frame counts** (60 fps), a proxy for the 3.6
values — not PM-3.6 primaries.

| Mechanic | Frames | File + symbol (meleelight `src/characters/`) |
|----------|:------:|----------------------------------------------|
| Air-dodge intangibility | **25** (marth/puff/fox/falcon), **26** (falco) | `marth/marthAttributes.js` `airdodgeIntangible : 25` · `falco/attributes.js` `airdodgeIntangible : 26` |
| Grounded dodges (roll B/F, spot N) | ESCAPEB/F **[4,20]**, ESCAPEN **[2,16]** | `marth/marthAttributes.js` `setIntangibility` table |
| Ledge grab (cliff catch) | **38** | `shared/moves/CLIFFCATCH.js` `intangibleTimer = 38` |
| Ledge getup / jump / attack (quick∕slow) | getup **30∕55**, jump **11∕18**, attack **20∕34** | `marth/moves/CLIFFGETUP*/CLIFFJUMP*/CLIFFATTACK*.js` |
| Tech (in place / roll) | **[1,20]**; wall/ceiling **14–15** | `marth/marthAttributes.js` `TECHN/TECHB/TECHF` · `shared/moves/WALLTECH.js`, `STOPCEIL.js` |
| Getup from knockdown (DOWNSTAND) | N **[1,22]**, B **[1,19]**, F **[6,14]** | `marth/marthAttributes.js` `setIntangibility` table |
| Respawn platform (rebirth) invincibility | **120** (= 2 s) | `shared/moves/REBIRTHWAIT.js` `invincibleTimer = 120` |
| Post-death respawn grace | **2** | `shared/moves/DEAD{LEFT,RIGHT,UP,DOWN}.js` `intangibleTimer = 2` |

`brawllib_rs` carries only the intangibility **state** enum (`HurtBoxState::Invincible /
IntangibleFlashing / …` in `src/script_ast/mod.rs`), not counts — per-move durations live in `.pac`
timers. GAP for counts there.

---

## 3. Super-armor knockback thresholds — GAP (mechanism known, tier numbers not)

The **Light / Medium / Heavy** tier *values* PM 3.6 standardized armor into are **in no readable
source**. What is known:

- **The mechanism is per-move, not a global tier table.** `brawllib_rs` exposes armor as a PSA event
  with a caller-supplied tolerance, in `src/script_ast/mod.rs`:
  > `/// Begins super armor or heavy armor. Set parameters to None and 0 to end the armor.`
  > `Armor { armor_type: ArmorType, tolerance: f32 }`
  with `ArmorType` = `None / SuperArmor(1) / HeavyArmorKnockbackBased(2) / HeavyArmorDamageBased(3)`
  (`impl ArmorType::new`), stored in `src/script_runner.rs` as `armor_type` + `armor_tolerance: f32`.
  So each armored move carries its **own** knockback/damage `tolerance`; a "Light/Medium/Heavy" number
  can only come from datamining a **specific move's PSA `tolerance`**, not from any tier constant.
- **`Project-M-CC`** has the code title `Subtractive Knockback Armor v1.1 [Magus]` (and a debug overlay
  code), but the body is assembled Gecko hex — the subtractive-armor magnitude is not plaintext.
- **`meleelight`** has no armor system.

This is the ticket's central GAP: the #1108-confirmed knockback-standardized armor rework is real, but
its tier numbers were not recoverable from the sources this hunt could read. See §5 for the follow-up.

---

## 4. GAPs — no usable number found (not guessed)

| Buff | Missing magnitude | What exists instead |
|------|-------------------|---------------------|
| **Bunny Hood** | jump-height ×, movement-speed ×, Brawl duration | Only Ultimate quantified (jump 2×, walk/run 2×); Melee duration "~12 s"; Brawl = prose only. Not in meleelight/brawllib/PM-CC (item.pac data). |
| **Super Star (Starman)** | Brawl invincibility duration | Only original SSB gives "invincible for ten seconds"; Melee/Brawl/SSB4 say "short period." |
| **Super Mushroom** | size/scale ×, Brawl weight × | Weight given only for Melee (1.6×) and SSB4/Ultimate (1.42×), not Brawl. |
| **Metal Box** | engine weight/fall/duration constants | `brawllib_rs` has only the timer slot `metal_block_remaining_time` (`src/script_runner.rs`); the magnitudes are item.pac PSA it doesn't embed. (The §1 SmashWiki figures stand as the Brawl proxy.) |
| **Lightning** | shrink factor, duration | Prose only ("shrink every other fighter to tiny size"; "After a set amount of time…"). |
| **Timer** | duration | No seconds stated for any game. |
| **Franklin Badge** | duration, reflect multiplier | Both entirely absent from the page. |
| **Screw Attack (item)** | jump-boost magnitude, duration | Only SSB4 prose "slightly boosts jump height"; no time value. |
| **Lucario aura** | damage-scaling min/max coefficients vs damage % | `brawllib_rs` has only `has_final_aura` (a Final-Smash bool); PM-CC's `Aura Effects Mod …` code governs visual intensity by KB, not the damage formula, and is hex-only. (Aura *meter* provenance is sibling thread C, #1116.) |

---

## 5. Follow-ups (each a downstream ticket, filed one at a time if wanted)

1. **Per-move armor-tolerance PSA datamine.** The §3 tier numbers require running a `.pac` datamine over
   the #1108-named infinite-armor whitelist moves (Ike Eruption, Bowser smashes, Ganon Flame Choke) and
   representative knockback-armored moves, reading each move's `tolerance: f32`. That needs actual PM 3.6
   `.pac` files fed to `brawllib_rs` (which embeds the mechanism but not the data). Blocked on obtaining
   the fighter `.pac` set.
2. **Item.pac magnitude datamine.** Metal Box / Bunny Hood / Starman / Super Mushroom engine constants
   live in `item.pac`. The §1/§4 GAPs would close by datamining `item.pac` directly (out of reach of the
   text codesets and the character-only brawllib source tree here).
3. **Catalog mark update** (trivial): once §1 values are accepted as the Brawl-inherited baseline, the
   #1106 catalog's magnitude follow-up (its "Open follow-ups" item 1) can be checked off. Deferred, not
   part of this ticket.

## Which #1106 catalog rows gain a magnitude

| Catalog row | Magnitude added here | Tag |
|-------------|----------------------|-----|
| Metal Box | 4.5× weight, 2.0× fall, 12 s | Brawl-inherited |
| Super Mushroom | 1.56× dmg (1.8× listed), ~10 s | Brawl-inherited |
| Heart Container | 100 pts | Brawl-inherited |
| Maxim Tomato | 50% | Brawl-inherited |
| Superspicy Curry | 13 s, 1%/hit | Brawl-inherited |
| Lightning | 0.7× others' attack | Brawl-inherited |
| Timer | 1/4 speed | Brawl-inherited |
| Warp Star | 22% | weak-quote (Brawl-by-reference) |
| Intangibility (state) | dodge 25f / ledge 38f / respawn 120f etc. | Melee-inherited |
| Super armor (tiers) | **GAP** — see §3 | — |
| Bunny Hood / Super Star / Franklin Badge / Screw Attack | **GAP** — see §4 | — |

## Refs

Parent: #1107 (tracker). Siblings: #1108 (primaries, closed), #1116 (aura-meter, post-v1). Seed:
#1106 (`docs/research/fighter-buffs-findings.md`). Canon baseline: PM 3.6
(`docs/project-m-parity.md`). Router: `docs/mechanics-index.md`.
