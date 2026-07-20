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

> ## ✅ Result (2026-07-19, #753) — FOUND
> The brawllib_rs dump was run against the PM 3.6 `.pac` (vanilla Brawl `-d` + PM 3.6 overlay `-m`).
> **Mario `Wait1` = 51 frames** (`subaction.frames.len()`, `iasa=None`). This is the **loop length**.
> The dump also confirms the mechanic split — `Wait1` 51 (the breathing loop) vs the fidget variants
> `Wait2` 150 / `Wait3` 95. Evidence + provenance in **Datamine result (#753)** below. This
> **supersedes** the interim author-chosen 120f (2.0 s) guess in Q4.

> ## 🔎 Refinement (2026-07-19, #567) — loop ≠ breath period
> The #753 result recorded 51 as the `Wait1` **loop** length and left one thing un-eyeballed (see the
> Loop-semantics caveat below): *how many breaths are in that loop?* During #567 implementation the
> `Wait1` animation was rendered to a GIF (`brawllib_rs` `gif_generator`, saved
> `repros/idle-breathing/mario_wait1.gif`) and its 51 frames analysed frame-by-frame: the body's
> vertical position completes **two** full rise/fall cycles per loop (centroid peaks at frames ~4 & ~26,
> troughs at ~13 & ~38). **So 51 frames = 2 breaths**, and the sin **breath period** #567 drives is
> **51 / 2 = 25.5 frames/breath** (~0.43 s @ 60fps) — NOT 51. Using 51 as the sin period would bob at
> half the real rate. In code this lives as a per-archetype map keyed on the loop length ÷ breaths-per-
> loop (`_IDLE_BREATH_PERIOD_FRAMES["nalio"]` in `render_battle.py`), so each future archetype records
> its own datamined `Wait1` loop + breath count.

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

**Period provenance: `FOUND` = 51-frame loop, 2 breaths (datamined #753, GIF-refined #567).** Mario
`Wait1` = **51 frames** (`subaction.frames.len()` via brawllib_rs against the PM 3.6 `.pac`). That 51
is the **loop** length; the loop contains **2 breaths** (GIF-verified, see the #567 Refinement banner),
so the `sin` **breath period** is `51 / 2`. At the 1:1 framerate bridge:

    # render_battle.py — per-archetype, loop ÷ breaths-per-loop
    _IDLE_BREATH_PERIOD_FRAMES = {"nalio": 51 / 2}   # = 25.5 f/breath (~0.43 s @ 60fps) — FOUND #753/#567

**Framerate bridge:** Brawl 60fps ↔ pycats 60fps = **1:1**, so the dumped `frames.len()` maps directly
with no scaling.

**Superseded — the earlier author-chosen guess.** The pre-dump draft recommended `120` (2.0 s) as an
interim `PLACEHOLDER`. The datamined loop is **51f (0.85 s)** — ~2.4× faster — so **use 51**, not 120.
(#567 remains free to deviate for game-feel, but that would be an owner decision *away from* the
faithful value, recorded as `TUNED`, not the default.)

**Amplitude — out of scope here, one open question surfaced for #567:**
- Amplitude in px stays #567's author-chosen render constant (±1px, fallback ±2px). This spike does
  not set it.
- **Open design question (owner-flagged, unresolved):** should the bob amplitude **scale with the
  character's height** (taller cat → larger px bob)? The owner is not convinced either way. Left
  **OPEN** for #567 to decide; not decided here. *(Ducking is moot — breathing is idle-only, so a
  crouching/ducking cat does not breathe.)* No perceptible-amplitude figure was recoverable from the
  web sources to inform this (same Q2 wall).

---

## Datamine result (#753)

Run 2026-07-19 (CHERRY) via a throwaway `examples/wait_lengths.rs` in the brawllib_rs clone
(`~/Documents/Study/Rust/brawllib_rs/`, #614), which prints each subaction's `frames.len()`:

    cargo run --release --example wait_lengths -- \
      -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (extracted ISO)
      -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay (#640 staged)
      -f Mario

Mario `Wait*` subaction lengths (the idle family):

| Subaction | Frames | Role |
|---|---|---|
| **`Wait1`** | **51** | **the base standing/breathing loop → the #567 value** |
| `Wait2` | 150 | fidget variant (random idle pose) |
| `Wait3` | 95 | fidget variant (random idle pose) |
| `SquatWait` | 131 | crouch idle (not #567 — idle only) |
| `CliffWait` | 101 | ledge-hang idle |
| `DownWaitU` / `DownWaitD` | 71 / 71 | downed idle |

**Provenance:** source = `brawllib_rs` (clone #614) reading PM 3.6 `.pac` (`FitMario*` under the
`-m` overlay over the `-d` vanilla dump); field = `HighLevelSubaction.frames.len()` for `Wait1`;
value = **51 frames**; tier = **`FOUND`**.

**Loop-semantics caveat — RESOLVED by the #567 Refinement above.** 51 is the `Wait1` animation's
full frame count (`iasa=None` → it plays to the end, then the idle system loops it / occasionally
swaps to `Wait2`/`Wait3`). The open question — one visual breath per loop, or a sub-cycle — was
settled by rendering the loop to a GIF and analysing it frame-by-frame: **the loop contains 2
breaths**, so #567's `sin` period is **51 / 2 = 25.5 f/breath**, not 51. Do NOT map one `Wait1` loop
to one `sin` period. See **🔎 Refinement (2026-07-19, #567)** at the top.

## Sources
- SmashWiki — *Idle pose*: https://www.ssbwiki.com/Idle_pose
- OpenSA (Dantarion) — *Subactions (Brawl)* (Wait1/2/3 = codes 2/3/4): http://opensa.dantarion.com/wiki/Subactions_(Brawl)
- rukaidata — *Brawl/Mario/subactions/Wait1* (no animation-length field): https://rukaidata.com/Brawl/Mario/subactions/Wait1.html
- rukaidata — *Brawl/Mario/subactions/AttackS3S* (control: no length field on any subaction): https://rukaidata.com/Brawl/Mario/subactions/AttackS3S.html
- SmashWiki — *Frame* (Brawl = 60fps, 1 frame = 1/60 s): https://www.ssbwiki.com/Frame
- In-repo: `pycats/config.py` (`FPS = 60`); `pycats/combat/data.py` (`FighterData`, no idle-anim field).

## Provenance tier
- **Wait1 loop length:** **`FOUND` = 51 frames** (Mario `Wait1`, `subaction.frames.len()` via
  brawllib_rs against the PM 3.6 `.pac`, #753). Datamined, NOT engine-locked, NOT web-only.
- **Breaths per loop:** **`FOUND` = 2** (GIF frame-analysis of the same `Wait1`, #567). → breath period
  = loop ÷ breaths = **51 / 2 = 25.5 f/breath**.
- **Framerate bridge:** `FOUND` — Brawl 60fps (SmashWiki *Frame*) ↔ pycats `FPS = 60` (`config.py`),
  1:1.
- **Breath period for #567:** **`FOUND` = 25.5 f/breath** (Mario `Wait1` loop 51 ÷ 2 breaths, #753/#567).
  The earlier `120` (range 90–180) was an interim author guess — superseded; and the raw `51` is the
  *loop*, not the breath period.

## Downstream (file one-at-a-time, not in this ticket)
1. ✅ **Done (#567):** the per-archetype `_IDLE_BREATH_PERIOD_FRAMES` map in `render_battle.py` pins
   Nalio at `51 / 2` (loop ÷ breaths), with a comment pointing here.
2. ✅ **Done (#753):** the brawllib_rs dump — Mario `Wait1` = 51 frames. See **Datamine result (#753)**.
3. #567 owner-decision: amplitude-scales-with-height (OPEN).
