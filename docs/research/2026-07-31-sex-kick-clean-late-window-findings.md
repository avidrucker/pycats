# Findings — how a lingering "sex kick" aerial (clean/late windows) works in PM 3.6

> **Ticket:** #889 (RESEARCH, `area:combat`). **Date:** 2026-07-31. **Agent:** GRAPE.
> **Canon:** Project M 3.6 (Brawl fallback). **Status:** FOUND (primary-grounded).
> Part of the parity doc set — front door: [`../project-m-parity.md`](../project-m-parity.md).
> **Pairs with #879** ([`2026-07-28-same-move-window-rehit-findings.md`](./2026-07-28-same-move-window-rehit-findings.md)),
> which grounds the **hit-count** half (one hit per target across clean+late). This doc
> covers what #879 deferred: the clean/late **timing + power-falloff** semantics.
> Feeds **#890** (blocked — audit what pycats implements) and **#893** (the "no sex kick
> in V1?" scope decision).

## Question

In PM 3.6, how does a lingering "sex kick" aerial — one move with an early **clean**
hitbox and a later **late** hitbox of reduced power — work exactly? Specifically:
(1) the clean/late **window structure** and how it is authored; (2) the **power falloff**
across the two windows (damage / angle / knockback); (3) the **hit count** (deferred to
#879); (4) canonical **exemplars** and the term's origin.

## Answer (short)

A sex kick is **one subaction** whose hitbox is authored on a single **set** (`set_id`),
created early with strong values and then **overwritten** part-way through the move with a
weaker set of values, with **no `DeleteAllHitBoxes` between** the two. The overwrite keeps
the set non-empty, so the engine does **not** re-arm the re-hit flag — the target takes
**one** hit, the clean *or* the late, never both (this is the #879 result — cited, not
re-derived).

The **falloff is per-move, not a fixed formula.** Damage always drops (clean > late).
Angle and knockback (base `bkb`, growth `kbg`) *may* also change — from unchanged (Mario
nair) to a full launcher→poke transition (Mario bair). The **late** hit very often lands
at the **Sakurai angle** (trajectory `361`), the shallow "auto-angle" that keeps a
lingering hit from launching for a KO.

## Primary evidence — three canonical sex kicks, datamined from PM 3.6

Dumped from the actual PM 3.6 `.pac` data via `brawllib_rs`'s `high_level_frame_data`
example (`@ e8dc833`, run 2026-07-31; command in "How this was produced" below). Values
are per-**active-frame** hitbox arguments; frame index is brawllib's **0-based
high-level frame index** (see the frame-convention note).

| Move (subaction) | Clean window | Late window | What changes clean → late |
|---|---|---|---|
| **Mario nair** (`AttackAirN`) | f2–6 · dmg **12** · ang **361** (Sakurai) · kbg 100 · bkb 20 | f6–29 · dmg **9** · ang **361** · kbg 100 · bkb 20 | **damage only** (12 → 9) |
| **Kirby nair** (`AttackAirN`) | f2–6 · dmg **12** · ang 55 · kbg 100 · bkb **15** | f6–28 · dmg **9** · ang 55 · kbg 100 · bkb **0** | damage (12 → 9) **+ base knockback** (15 → 0) |
| **Mario bair** (`AttackAirB`) | f5–8 · dmg **11** · ang **28** · kbg **65** · bkb **43** | f8–16 · dmg **9** · ang **361** (Sakurai) · kbg **100** · bkb **20** | damage **+ angle** (28° → Sakurai) **+ knockback** (KO launcher → weak poke) |

(Active-hitbox frame ranges, 0-based; the transition frame — where both the clean and late
argument-sets appear — is f6 for both nairs and f8 for bair. Mario nair lingers longest
(f2–29); Mario bair's window is shortest (f5–16), fitting its role as a committal KO aerial.)

Reading the three together:

- **Same `set_id` (0) across both windows in every case**, and on the **transition frame**
  both the old (clean) and new (late) argument-sets appear — the signature of an
  **overwrite**, not a delete→recreate. This is the exact condition #879 shows leaves
  `empty_set == false` → no re-hit → **one hit**.
- **Damage always falls**, by a small amount (12 → 9, 11 → 9). The clean hit is the
  "fresh" / stronger hit; the late hit is the "stale" / weaker lingering hit.
- **Angle & knockback behaviour is not uniform:**
  - *Mario nair* — the archetypal sex kick — changes **only damage**. Both windows are the
    same shallow Sakurai-angle (361) push. It is a spacing/combo tool, not a KO move, in
    either window.
  - *Kirby nair* keeps the angle (55°) but zeroes the base knockback late (15 → 0), so the
    late hit is a near-set-knockback linking poke.
  - *Mario bair* is the strong case: the **clean** hit is a **28° KO launcher** (high base
    `bkb 43`, low growth `kbg 65`), and the **late** hit collapses to a **Sakurai-angle
    (361)** weak poke (`bkb 20`, `kbg 100`). This is the community "clean bair KOs, late
    bair doesn't" — and it is exactly the structure #879 matched `_NALIO_BAIR` to.

### How the clean/late split is authored (data layer)

The two windows are two `CreateHitBox` events **on the same `set_id`, in the same
subaction**, the second overwriting the first. The per-hitbox arguments that carry the
power values are, verbatim (`brawllib_rs` `src/script_ast/mod.rs`, `HitBoxArguments`,
`@ e8dc833`, read 2026-07-31):

```rust
pub struct HitBoxArguments {
    ...
    pub set_id: u8,        // the "set" — shared across a sex kick's clean+late windows
    pub damage: FloatValue,
    pub trajectory: i32,   // launch angle; 361 = the Sakurai auto-angle
    pub wdsk: i16,         // weight-dependent set knockback
    pub kbg: i16,          // knockback growth
    pub bkb: i16,          // base knockback
    ...
}
```

Because the second `CreateHitBox` reuses `set_id` while the set is still populated, #879's
`brawllib_rs` `script_runner.rs` rule (`empty_set` → `hitbox_sets_rehit[set_id] = true`)
does **not** fire → the set does not re-hit. See #879 for that mechanism; this doc does not
re-derive it.

### The Sakurai angle (trajectory 361) — what the late hit usually becomes

`361` is not a literal 361°; it is the sentinel for the **Sakurai angle**, resolved at
hit time from the knockback the victim would take. Verbatim from the `meleelight` engine
(`src/physics/hitDetection.js`, `@` local #616 clone, read 2026-07-31):

```js
if (trajectory == 361) {
    if (knockback < 32.1) {
        if (reverse) { trajectory = 180; } else { trajectory = 0; }   // low KB: ~horizontal
    } else if (knockback >= 32.1) {
        if (reverse) { trajectory = 136; } else { trajectory = 44; }  // high KB: ~44° up-and-away
    }
    ...
}
```

So a Sakurai-angle late hit sends **near-horizontal at low knockback** and **~44° up** once
knockback is high — the behaviour that makes a lingering hit safe (weak drag at low %,
gentle launch at high %) rather than a KO. brawllib parses the same `361` sentinel into its
hitbox `trajectory` field (`HitBoxArguments.trajectory: i32`, above); it is a real,
frequently-used authored value, not a datamine artifact.

## Hit count — deferred to #879 (cited, not re-derived)

Across the clean + late windows a sex kick hits a given target **once** — the clean hit
*or* the late hit. The mechanism (per-attacker hit-list; re-hit only on set empty→create or
explicit rehit; overwrite ≠ re-hit) is grounded in
[#879](./2026-07-28-same-move-window-rehit-findings.md)
(`brawllib_rs` `script_runner.rs` + rukaidata Kirby scripts + `meleelight`
`hitDetection.js`). The datamine above **independently corroborates** the "overwrite, same
set, no delete between" precondition for all three moves.

## Exemplars & the term

- **Canonical sex kicks** (strong early / weak lingering aerial, one continuous hitbox):
  Mario **nair** and **bair** (datamined above), Kirby **nair** (datamined above),
  and — by the same overwrite structure — many Brawl/PM aerials inherited from the Melee
  lineage (Fox/Falcon nair are the community-canonical Melee originals). In PM 3.6 the
  structure is the one shown here: one subaction, one `set_id`, a mid-move overwrite to
  weaker values.
- **Term origin** — "sex kick" is **community terminology** (SmashWiki-documented),
  originating in the Melee community for lingering-hitbox aerials whose hitbox stays out
  and weakens over time; it is descriptive slang, not an in-data label. *Evidence level:
  community lore, not datamine-groundable* — flagged as such rather than asserted as canon.

## Frame-convention note

Frame indices here are `brawllib_rs` **high-level active-frame** indices (0-based), i.e.
the frames on which the hitbox is actually live. #879's Kirby citations came through
rukaidata's **script-event** frames (the frame a `CreateHitBox` fires), which can differ by
±1–2 from the active-frame index. The **damage values match exactly** (12 → 9); only the
frame labels differ by convention. Where this doc and #879 both cite Kirby `AttackAirN`,
treat the *damage/set* facts as authoritative and the *frame numbers* as convention-dependent.

## Falsifiable restatement

- **FALSE if:** a PM 3.6 sex kick's clean and late windows carry **different `set_id`s**,
  or a `DeleteAllHitBoxes` sits between them — either would make it a re-hitting multi-hit,
  not a one-hit sex kick. The three datamined moves all show one `set_id` (0) and an
  overwrite with no between-window delete.
- **FALSE if:** the clean hit is not stronger than the late hit (damage or knockback). All
  three show clean damage ≥ late damage; Mario bair shows the clean hit as the strict KO
  launcher.
- **Model claim (holds):** the falloff is **per-move** — damage always drops; angle/`bkb`/
  `kbg` change only for some moves — so there is **no single "sex-kick falloff constant"**
  to hardcode; each move authors its own clean and late argument-sets.

## How this was produced (repeatable)

```
cd ~/Documents/Study/Rust/brawllib_rs && . ~/.cargo/env
cargo run --release --example high_level_frame_data -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \
  -f Mario -a AttackAirN -l subaction        # also: -a AttackAirB; -f Kirby -a AttackAirN
```

(`-m` is the **parent** of `projectm/` — brawllib resolves `<mod>/projectm/pf/fighter`.)
Per-frame hitbox arguments (`set_id`, `damage`, `trajectory`, `wdsk`, `kbg`, `bkb`) are in
each `HighLevelFrame`'s `hit_boxes`. Same pipeline as the #614 datamine env
(memory `brawllib-datamine-env-live`).

## Evidence map

Add a row to [`../project-m-rules-by-category.md`](../project-m-rules-by-category.md) →
Hit-resolution (distinct from #879's re-hit row): *"Sex-kick clean/late power falloff — one
subaction, one `set_id`, mid-move overwrite to weaker values; damage always drops, angle/
knockback change per-move (Mario nair: damage only; Kirby nair: +bkb; Mario bair: +angle+KB,
KO→poke); late hit often at the Sakurai angle (361)"* — **FOUND**, source `brawllib_rs`
`high_level_frame_data` datamine of Mario `AttackAirN`/`AttackAirB` + Kirby `AttackAirN`
(`@ e8dc833`) + `meleelight` `hitDetection.js` (Sakurai-angle resolution); hit-count via #879.

## Next steps (downstream — NOT filed by this ticket)

1. **#890** (blocked on this) — audit what pycats implements against this model: do the
   shipped sex kicks (`_BIRKY_NAIR`, `_BIRKY_UTILT`, `_NALIO_BAIR`) reproduce a clean/late
   **power falloff** at all, and if so which profile (damage-only vs +angle/+KB)? This doc
   is the canon yardstick.
2. **#893** (blocked on #889/#890) — the "should V1 have **no** special sex-kick mechanic"
   scope decision. This doc quantifies what a faithful sex kick *is* (per-move falloff +
   one-hit), so the human can weigh "simplify to a single flat hitbox" against it.
