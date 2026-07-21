# Respawn invincibility — PM 3.6 validation findings (#830)

> Research spike, **findings only — no ruling.** Ticket **#830** (child of umbrella **#539**), feeds DEV
> **#506** (slice 1 of epic **#482**). PM canon: Project M 3.6 (Melee-based). Date: 2026-07-21. Agent: banana.
>
> The two scope/value **decisions** this feeds (ship the interim model? solid vs blink?) are the owner's,
> recorded as an **ADR-0009 addendum** — see "Recommendation" (advisory only).

## TL;DR

| # | Question | Answer | Confidence |
|---|---|---|---|
| Q1 | Post-drop invincibility duration | **120 f (2 s)**, flat | **FOUND** (two sources agree) |
| Q2a | Start-timing structure | on-platform **intangible** → any action (or 300 f timeout) ends it → **120 f invincible** descent | **FOUND** (SmashWiki + engine) |
| Q2b | Does acting **truncate** the post-drop window? (the flagged gap) | **No** — the 120 f runs in full regardless of actions | **FOUND-by-engine** (Melee reimpl; PM `[inference]`) |
| Q3 | Render: solid tint vs blink? | **Blink/flicker** (periodic), not a solid fill; intangible & invincible render identically | **primary-reimpl** (Melee); PM `[inference]`; SmashWiki gap |

## Q1 — Duration: 120 f (2 s), flat

**FOUND.** Two independent sources agree:
- SmashWiki — Revival platform (T2), verbatim: *"After dropping down from the platform, the character
  has a further period of invincibility (2 seconds, or 120 frames)."*
- meleelight (Melee engine reimplementation, primary): `REBIRTHWAIT.js` sets
  `player[p].phys.invincibleTimer = 120` on **every** leave-path.

Ultimate scales the window down by time-spent-waiting (min 60 f); PM 3.6 is **Melee-based**, so the
flat **120 f** applies — Ultimate's scaling is **not** adopted. This confirms #480's value; #506's
`RESPAWN_*_FRAMES = int(2 * FPS) = 120` is correct.

## Q2 — Start-timing + truncation

**Structure (FOUND).** meleelight `physics.js::hurtBoxStateUpdate`: while `actionState` is
`REBIRTH`/`REBIRTHWAIT`, `hurtBoxState = 1` (**intangible**) — the on-platform phase. `REBIRTHWAIT.js`
`interrupt()` shows the fighter **leaves the platform on any action** — aerial, air-dodge (L/R),
double-jump, special, a stick tilt `|lsX|>0.3 || |lsY|>0.3`, or a **300 f** inaction timeout — and each
of those transitions sets `invincibleTimer = 120`. So: **intangible on platform → the leaving action
ends intangibility and starts the 120 f invincible descent.** Matches SmashWiki's *"intangible … disappears
as soon as the player moves or attacks."*

**Truncation — the flagged gap, now closed (FOUND-by-engine).** The category index noted *"no verbatim
that acting doesn't truncate it."* The engine settles it: `hurtBoxStateUpdate` decrements
`invincibleTimer` **unconditionally every frame** (`if (invincibleTimer > 0) { invincibleTimer--; }`),
and a full-tree grep found the **only** writes to `invincibleTimer` are the `= 120` grants in
`REBIRTHWAIT.js` and that `--`. **No code path zeroes or shortens it on acting/moving/attacking.**

> **Acting does NOT truncate the post-drop invincibility** — the 120 f runs in full, in real time, from
> the frame you leave the platform, whatever you do. What ends on action is the *on-platform
> intangibility*, not the descent invincibility. (The two phases behave **oppositely** w.r.t. action.)

Tier: Melee reimplementation → PM is `[inference]` (PM restored Melee behavior; strong). SmashWiki is
silent on this point, so the engine is the sole source; a PM-codeset cross-check (Project-M-CC, #664)
would upgrade it from `[inference]` to explicit.

## Q3 — Render: blink, not solid

**Blink/flicker (primary-reimpl; SmashWiki gap).**
- SmashWiki — Invincibility (T2): describes only the **hurtbox-view** cue (*"hurtboxes changing from
  their usual yellow color to a green color"*) — a debug overlay, **not** the character model. It gives
  **no** description of the respawn character's on-screen appearance. **Gap** in the secondary source.
- meleelight `render.js` (body-colour branch): the character draws its flashing colour when
  `intangibleTimer % 9 > 3 || invincibleTimer % 9 > 3` — i.e. the body **alternates** between an alt
  palette shade and its normal colour on a **~9-frame period** (≈5 on / 4 off). That is a **blink/flicker
  cadence, not a solid fill**. Note it renders **intangible and invincible identically** — no visual
  distinction between the two states.

So PM/Melee respawn invincibility is a **periodic flash**, matching the familiar "respawn flashing."
The exact *style* (meleelight swaps body colour; retail Melee flashes translucent) is a rendering
choice; the load-bearing finding is the **blink cadence**, not solid. Tier: Melee reimpl → PM
`[inference]`.

## Recommendation for #506 (advisory — owner decides via ADR-0009 addendum)

1. **Interim granted-at-spawn model (pre-revival-platform):** a **faithful stopgap** for the *post-drop*
   phase specifically — post-drop, PM likewise just counts 120 f down in real time regardless of action
   (Q2b), which is exactly what the interim model does. Its only infidelities are the **missing
   on-platform intangible phase** and the **re-anchor to platform-leave** — both already owned by slices
   2–3 of #482. Recommend: **accept** the interim model for slice 1, with a code comment that it models
   the post-drop window only.
2. **Solid vs blink:** PM renders a **blink** (Q3), so #506's "solid white tint for exactly N frames"
   is a **DIVERGENCE**. A faithful blink is **already scoped as deferred post-v1 work in epic #558**
   ("PM-faithful invincibility blink/flicker"). Recommend: ship slice 1 with a simple non-blink tint as
   an **acknowledged DIVERGENCE**, and defer the faithful flicker to **#558** — but this is the owner's
   scope call, not mine.

Both are **decisions**, deferred to the owner's ADR-0009 addendum. This spike reports; it does not rule.

## Sources + confidence

| Finding | Source | Tier | Confidence |
|---|---|---|---|
| 120 f duration | SmashWiki Revival platform + meleelight `REBIRTHWAIT.js` | T2 + reimpl | FOUND |
| intangible→invincible structure | SmashWiki + meleelight `hurtBoxStateUpdate` | T2 + reimpl | FOUND |
| acting does not truncate post-drop window | meleelight `physics.js` (unconditional decrement; grep of all writes) | reimpl | FOUND-by-engine; PM `[inference]` |
| blink (not solid) render | meleelight `render.js` (`% 9 > 3` toggle) | reimpl | strong; PM `[inference]`; SmashWiki gap |

Caveats: meleelight is a **Melee** reimplementation (PM→Melee is `[inference]`; PM restored much Melee
behavior) and is known to contain bugs — findings are read from code, not assumed. A Project-M-CC (#664)
override check would upgrade the engine-only findings (truncation, blink) to explicit-PM.

## Termination

Q1–Q4 answered with sources + confidence; the truncation-verbatim gap closed via engine evidence; a
written recommendation posted for the owner. Decisions left open for the ADR-0009 addendum. The #480
doc and category-index Respawn/Invincibility rows are annotated with these findings.
