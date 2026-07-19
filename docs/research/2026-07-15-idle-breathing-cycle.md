# Idle "breathing" cycle duration — is PM/Brawl's Wait1 loop length datamineable?

**Ticket:** #741 (RESEARCH, informs DEV #567) · **Date:** 2026-07-15 · **Agent:** CHERRY
> ## ⚠ Correction (2026-07-19, #752)
> **The original verdict below was wrong on one point and is retracted here.** It framed the `Wait1`
> loop length as "NOT obtainable" and lumped it with the air-dodge velocity (#215/#192) as "the same
> wall." **That comparison is withdrawn:** the air-dodge force is an *engine global* genuinely absent
> from the `.pac`, whereas an animation's frame-count is **scripted CHR0 data inside the `.pac`** —
> the category `brawllib_rs` is built to read.
> **Corrected status:** the `Wait1` length **is datamineable via `brawllib_rs`**, which exposes
> `subaction.frames.len()` per subaction (verified in the local clone
> `~/Documents/Study/Rust/brawllib_rs/`, #614: `HighLevelSubaction { frames: Vec<HighLevelFrame> }`
> in `high_level_fighter.rs`; `examples/first_active_frames.rs` records `length: subaction.frames.len()`).
> So #567's period is **`FOUND`-pending a brawllib_rs run**, NOT a forever-`PLACEHOLDER`/engine-locked
> value. The only gate is the usual datamine gate: run the Rust tool + supply the PM 3.6 `.pac` files
> (extraction tracked in the dump ticket — see Downstream). Everything else below — the web-search
> dead-ends (rukaidata's HTML shows no length), Q1–Q3, the framerate bridge — **remains accurate.**

**Verdict in one line (original — superseded by the Correction above):** The idle-wait mechanic and
its *existence* are web-datamineable, and the **precise `Wait1` loop length is not on the web
frame-data sites** pycats uses (rukaidata's HTML never prints it) — but it **is** readable from the
`.pac` via `brawllib_rs` (`subaction.frames.len()`), so #567's period is **`FOUND`-pending a
brawllib_rs run**, not an author-chosen PLACEHOLDER.

---

## Q1 — Does PM/Brawl have a canonical idle "wait" animation with a defined loop length?

**Yes, structurally — with a clear split between the continuous breathing loop and the fidgets.**

- Brawl idle animations are internally named **"Wait"** (Melee onward). SmashWiki (*Idle pose*)
  distinguishes two things: the **regular standing animation** that "play[s] at regular intervals"
  (the continuous breathing loop — what #567 emulates), versus **idle poses / fidgets** that "play
  at random if a character stands still for a length of time" and "play at random intervals."
  > "Idle poses are minor, mainly nonconsequential animations that play at random if a character
  > stands still for a length of time." — SmashWiki, *Idle pose*
- The animation-code / subaction mapping (OpenSA, *Subactions (Brawl)*): **2 = Wait1, 3 = Wait2,
  4 = Wait3**; subaction `0x1` is always Wait2. So **Wait1 is the base continuous standing loop**;
  **Wait2/Wait3 are the fidget variants**.
- Per-character Wait subaction pages exist on rukaidata (e.g. `Brawl/Mario/subactions/Wait1.html`),
  confirming Wait1 is a real, per-character animation.

**What is NOT available:** SmashWiki does **not** state the fidget **timeout** (how long a character
stands still before a fidget plays) — only "for a length of time." And rukaidata does **not** state
the **Wait1 loop length in frames** (see Q2). *[Inference, labelled as such: Wait2/Wait3 are the
random fidgets and Wait1 is the loop; this reading is consistent across the OpenSA code map and the
SmashWiki regular-vs-random split, but neither source spells out "Wait1 = the breathing loop" in
those exact words.]*

## Q2 — Is the Wait1 length datamineable from the sources pycats uses?

**Partially. The mechanic/script is web-datamineable; the raw animation length is NOT.**

- **Datamineable (web):** the Wait1 **subaction script** — its scripted events — is on rukaidata and
  OpenSA. But those pages expose scripted metadata (IASA, hitbox-active frames), **not** the raw
  animation duration. Confirmed by direct inspection this session:
  - `Brawl/Mario/subactions/Wait1.html` — Stats show only `IASA: None`, `Subaction Index: 0x0`.
    **No "Animation length" field, no frame count, no loop count.**
  - `Brawl/Mario/subactions/AttackS3S.html` (a scripted attack, as a control) — shows `IASA: 25`
    and `Hitboxes active: 5-7`, but **still no total animation length**. So rukaidata never surfaces
    the CHR0 frame count for *any* subaction — this is not a Wait-only gap.
- **NOT web-datamineable (the actual length):** a CHR0 animation's total `FrameCount` lives in the
  character's model motion file (`FitMotionEtc.pac`), readable via **BrawlBox** or **brawllib_rs**
  reading the game's own files. BrawlBox supports the CHR0 animation format; extracting Mario's
  Wait1 `FrameCount` requires opening that `.pac`, which is a **local asset dump, not a web lookup**.

**NOT the air-dodge wall (retraction — this paragraph is corrected by #752).** The original draft
compared this to the air-dodge velocity (#215/#192) as "the same wall." **That is wrong and is
withdrawn.** Air-dodge force is an *engine global* genuinely absent from the `.pac`, so no `.pac`
reader can ever get it. Wait1's length is the opposite case: it is a **plain animation frame-count
inside the `.pac`'s CHR0**, which `brawllib_rs` reads directly. It is a **web** gap (rukaidata's HTML
doesn't print it), not a *datamining* gap — it is on the datamineable side of the line, alongside
move/hitbox data.

**To upgrade `PLACEHOLDER`/`TUNED` → `FOUND` later:** open `FitMotionEtc.pac` for the Mario
archetype in BrawlBox (or brawllib_rs), read the **Wait1 CHR0 `FrameCount`**, and cite it. That is
the only path to a sourced number, and nobody has run it yet.

## Q3 — pycats today

- **Framerate:** `pycats/config.py` → `FPS = 60` (`config.py`, header + `FPS = 60`). Brawl also runs
  at 60fps (1 frame = 1/60 s). So the **framerate bridge is 1:1** (see Q4).
- **No idle-anim dataset field:** `FighterData` (`pycats/combat/data.py`) carries per-move attack
  timing (`moves: dict[str, MoveData]` with startup/active/recovery frames) and body sizes
  (`stand_size`/`crouch_size`/`prone_size`), but **no idle / wait / breathing animation-length
  field**. So `IDLE_BREATH_PERIOD_FRAMES` (proposed in #567) would be a **new** render constant, not
  a value already in the dataset.

## Q4 — Recommendation for #567 (framed, not decided)

**Period provenance: `FOUND`-pending a brawllib_rs run (see the Correction at top).** The `Wait1`
length is not on the *web* sites, but it **is** datamineable from the `.pac` via `brawllib_rs`
(`subaction.frames.len()`). Until that dump lands, #567 may ship the **interim author-chosen** period
below (`PLACEHOLDER`), to be **replaced by the `FOUND` value** once dumped — it is not a permanent
author-choice.

**Framerate bridge (the mandatory sub-step):** Brawl 60fps ↔ pycats 60fps = **1:1**. Once the `Wait1`
`frames.len()` of `N` is dumped, it maps directly to `IDLE_BREATH_PERIOD_FRAMES = N` with no scaling.
We do **not** have `N` yet — it comes from the dump ticket (Downstream).

**Recommended author-chosen default (owner ratifies by eye):**
- Start at **`IDLE_BREATH_PERIOD_FRAMES = 120`** (2.0 s @ 60fps) — one full slow breath per ~2 s.
- Acceptable range **90–180 frames (1.5–3.0 s)**; slower reads calmer, faster reads more alive.
- Rationale is **game-feel, not sourced**: subtle idle breathing loops read best slow; ~2 s is a
  common, unobtrusive resting cadence. Tune by eye against the ±1px amplitude and bump if
  imperceptible. *(This range is a starting point for playtest, explicitly `PLACEHOLDER`.)*

**Amplitude — out of scope here, one open question surfaced for #567:**
- Amplitude in px stays #567's author-chosen render constant (±1px, fallback ±2px). This spike does
  not set it.
- **Open design question (owner-flagged, unresolved):** should the bob amplitude **scale with the
  character's height** (taller cat → larger px bob)? The owner is not convinced either way. Left
  **OPEN** for #567 to decide; not decided here. *(Ducking is moot — breathing is idle-only, so a
  crouching/ducking cat does not breathe.)* No perceptible-amplitude figure was recoverable from the
  web sources to inform this (same Q2 wall).

---

## Sources
- SmashWiki — *Idle pose*: https://www.ssbwiki.com/Idle_pose
- OpenSA (Dantarion) — *Subactions (Brawl)* (Wait1/2/3 = codes 2/3/4): http://opensa.dantarion.com/wiki/Subactions_(Brawl)
- rukaidata — *Brawl/Mario/subactions/Wait1* (no animation-length field): https://rukaidata.com/Brawl/Mario/subactions/Wait1.html
- rukaidata — *Brawl/Mario/subactions/AttackS3S* (control: no length field on any subaction): https://rukaidata.com/Brawl/Mario/subactions/AttackS3S.html
- SmashWiki — *Frame* (Brawl = 60fps, 1 frame = 1/60 s): https://www.ssbwiki.com/Frame
- In-repo: `pycats/config.py` (`FPS = 60`); `pycats/combat/data.py` (`FighterData`, no idle-anim field).

## Provenance tier
- **Wait1 loop length:** `FOUND`-pending — **datamineable via `brawllib_rs`**
  (`subaction.frames.len()` on the `Wait1` subaction; clone #614), **NOT** engine-locked. Not on the
  web frame-data sites, but readable from the PM 3.6 `.pac`; becomes `FOUND` when the dump ticket runs.
- **Framerate bridge:** `FOUND` — Brawl 60fps (SmashWiki *Frame*) ↔ pycats `FPS = 60` (`config.py`),
  1:1.
- **Recommended `IDLE_BREATH_PERIOD_FRAMES = 120` (range 90–180):** `PLACEHOLDER` author-choice for
  playtest, not sourced.

## Downstream (file one-at-a-time, not in this ticket)
1. Edit #567 to pin `IDLE_BREATH_PERIOD_FRAMES = 120` (PLACEHOLDER) with a comment pointing here.
2. **Dump ticket (filed next, one-at-a-time):** run the `brawllib_rs` `high_level_frame_data`
   example against the PM 3.6 `.pac` (recipe: `docs/tooling-brawllib-rs-datamine-recipe.md`) to read
   the `Wait1` subaction `frames.len()`, record it `FOUND`, and replace the interim period in #567.
   This is a brawllib_rs move/animation datamine — **not** the air-dodge engine-global path; the
   #215/#192 comparison is retracted (see the Correction).
3. #567 owner-decision: amplitude-scales-with-height (OPEN).
