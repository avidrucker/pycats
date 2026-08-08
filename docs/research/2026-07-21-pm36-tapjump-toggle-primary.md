# Does PM 3.6 expose a tap-jump ON/OFF toggle? — firming #864's `[inference]`

**Ticket:** #874 (research · `area:entities`) · firms one claim from #864's
`docs/research/2026-07-21-tapjump-vs-uptilt-access.md` (Q2)
**Date:** 2026-07-21 · **Agent:** banana
**Scope:** learn-and-report only. Does **not** amend #864's option matrix and does **not** rule #865.

**Question:** #864 established the tap-jump mechanic and flagged one claim as `[inference]` — that
**PM 3.6 *specifically* exposes a tap-jump on/off toggle**. Can a **verbatim PM-3.6 primary** be
pinned to upgrade it to FOUND, or (fallback) a **Brawl primary** it inherits?

**Answer in one line:** No PM-3.6-specific verbatim primary (an in-game controls screenshot, PM
manual, or PMDT changelog naming the toggle) is locatable on the accessible authoritative sources.
The **Brawl baseline is firmly pinned** — Brawl has a per-Name **Controls** menu whose options
include a tap-jump toggle — and PM 3.6, a Brawl mod running on Brawl's engine, inherits that screen.
**Rung (b) of the ticket's fallback ladder landed: Brawl-baseline primary + Brawl-inheritance
inference.** This matches the ticket's predicted likely outcome (the toggle is a Brawl-inherited
feature, not PM-specific).

---

## The fallback ladder (from #874) — which rung landed

| Rung | Outcome | Result |
|---|---|---|
| **(a)** PM-3.6 primary → **FOUND** | PM controls screen / manual / PMDT notes naming the toggle | **not located** |
| **(b)** Brawl baseline → pinned Brawl primary + inheritance inference | Brawl Controls menu has the toggle; PM inherits it | **✅ landed** |
| **(c)** Gap → **GUESS** | neither a PM nor a Brawl primary locatable | n/a — (b) is stronger |

## Sources & confidence

| Source | Kind | Names PM 3.6? | Used for |
|---|---|---|---|
| SmashWiki, *[Controls](https://www.ssbwiki.com/Controls)* | primary (canonical wiki) | no | the Brawl Controls menu: per-Name custom layouts, tap-jump toggle |
| SmashWiki, *[Tap jump](https://www.ssbwiki.com/Tap_jump)* | primary | **no** — says "Brawl onward" | the toggle exists Brawl-onward; up-tilt/up-air interference |
| SmashWiki, *[Up tilt](https://www.ssbwiki.com/Up_tilt)* | primary | no | disabling tap jump as the fix for the interference |
| SmashWiki, *[Project M](https://www.ssbwiki.com/Project_M)* / *[Project+](https://www.ssbwiki.com/Project+)* | primary | — | **negative:** neither page mentions controls / tap jump |
| [pmunofficial.com](https://pmunofficial.com/en/) (PMDT change documentation) | primary (PM changelog) | yes (PM 3.6) | **negative:** documents character/stage/mechanic changes; **no** controller-config entry |
| Smashboards / community threads | secondary | yes | corroborate PM players disabling tap jump via the per-Name Options/controls screen |

## The pinned Brawl baseline (verbatim)

SmashWiki *Controls*:
> "Controls is a special menu that debuted in *Super Smash Bros. Brawl* and appears in every game
> afterwards."
> "The menu allows players to adjust the default configuration of any compatible controller to a
> custom layout, than save this to a Name."
> "The controller will then automatically set to this custom configuration whenever that name is
> selected in-game."
> "Other options can be turned on and off in this mode, such as rumble and the ability to use **tap
> jump** and shake smash, as well as adjust control stick sensitivity."

SmashWiki *Tap jump*:
> "From *Super Smash Bros. Brawl* onward, tapping up to jump can be disabled in the Controls menu."
> "most players prefer disabling Tap Jump, as it can lead to accidental jumps when attempting to
> perform up tilts or up aerials."

SmashWiki *Up tilt*:
> "Turning off tap jump can help avoid the former problem, or the player can do some other action and
> hold up on the control stick before it ends."

## The inheritance inference (labeled)

**[inference]** PM 3.6 is a mod that runs on the *Super Smash Bros. Brawl* engine and boots through
Brawl's stock front-end (name registration + the per-Name Controls menu). SmashWiki says that menu
"appears in every game afterwards" — i.e. it is a Brawl-engine feature, not one PM would remove to
add. Two facts make the inheritance strong rather than bare:

1. **No evidence of removal.** PMDT's own change documentation (pmunofficial) enumerates PM 3.6's
   departures from Brawl (characters, stages, mechanics) and contains **no controller-config entry** —
   a change to or removal of the tap-jump toggle would be the kind of thing that changelog records.
2. **Community corroboration (secondary).** Project M players routinely describe disabling tap jump
   via the same per-Name Options/controls screen, consistent with the Brawl mechanic being present
   and unchanged.

What OFF changes (per the Brawl/Melee model and #864 Q2): stick-up stops being a jump input and
nothing else — up-tilt (grounded) and up-air (airborne) become stick-accessible; only the jump
*button* jumps. This is unchanged from #864's characterization.

## Effect on #864's claim

#864 Q2 tagged the PM-3.6 toggle `[inference]` with the note "no verbatim PM-3.6 primary … was
pinned." That gap is now **characterized, not closed**: rung (a) stays empty (no PM-specific
primary), but the claim is no longer bare reasoning — it rests on a **pinned Brawl baseline + a
labeled inheritance inference** backed by the changelog's silence and community corroboration. Per
[[pm-parity-cite-primary-not-inference]] the claim stays labeled inference (it is not a PM primary),
but it is now the **strongest form of inference** — baseline-pinned, not asserted.

**Follow-up (not applied here):** #864's `[inference]` note could be updated from "rests on
inheritance" to "rests on a pinned Brawl baseline + inheritance (no PM-3.6 primary locatable, #874)".
A one-line edit, filed separately if the maintainer wants it — this ticket reports, it does not amend
#864.

## Out of scope

Amending #864's findings doc / option matrix · ruling #865 (the Up+A decision) · implementing any
toggle (post-#865 DEV) · the broader PM input taxonomy (#476/#477).

## Refs

#864 (the `[inference]` flag) · #865 (consumer decision) · #476 (input-parity epic) · #477 +
[`docs/pm-reference/input-model.md`](../pm-reference/input-model.md) (taxonomy doc, annotated by this
ticket) · #616 (meleelight, Melee-lineage `tapJumpOff`) · SmashWiki *Controls* / *Tap jump* / *Up
tilt*. [[pm-parity-cite-primary-not-inference]] · [[grounded-speeds-projectplus-not-pm36]].
