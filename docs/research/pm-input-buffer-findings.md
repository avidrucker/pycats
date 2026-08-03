# PM / Brawl / Melee input-buffer behavior for mid-move attack re-presses — findings (#1093)

> **Ticket:** #1093 (research, area:combat / combat:cpu) · **blocks #1087** · relates #1079 (Q2) / #1089 · child of #925
> **Question:** does an input buffer exist in Melee / Brawl / PM 3.6, what is its window,
> and does it apply to an **attack/special re-press pressed while a move is still running**
> (the #1087 case)? If PM buffers such a press and fires it at the move's IASA, the V1
> **hard-drop** guard (#1079 Q2 / #1087) is a divergence and should instead be **buffer-to-IASA**.
> **Research only — no code or value change** (RULES: research never produces a spec).

## TL;DR

**pycats targets PM 3.6** ([[pm36-canonical-reference]]). **PM 3.6 has no input buffer by
default** — a mid-move attack re-press is **not** remembered and does **not** fire at IASA; the
player must press again once the character is actionable. So the V1 **hard-drop** guard (#1087:
ignore an attack press while a move is active) is **FAITHFUL to PM 3.6's default behavior**.

The **buffer-to-IASA** branch (#1089) corresponds to PM's **optional** *Input Assistance* mode
(a 3-frame buffer, **off by default**) — not the parity baseline. It is a genuine opt-in feature
to emulate later (if ever), not a correction required for default-PM parity.

## Per-game buffer table

| Game | Buffer by default? | Window | Mid-move attack re-press → | Basis |
|---|---|---|---|---|
| **Melee** | No ("save for a select few") | ~0 (inputs read live per frame) | **Dropped** — next action is read live on the actionable frame | SmashWiki *Buffer* (secondary); meleelight `InputBuffer` = per-frame history, not an action queue |
| **Brawl** | **Yes**, universal | **10 frames** at the end of most moves/animations | **Buffered** if the press lands in the last ≤10f before actionable → fires at IASA | SmashWiki *Buffer* (secondary); PM codeset `li r3,10` @ `0x8085B784` (primary datamine) |
| **PM 3.6** | **No** (opt-in only) | **0** default · **3f** with *Input Assistance* | **Dropped** (default); buffered ≤3f if Input Assistance on | SmashWiki *Project M* (secondary); PM codeset "Damage Gauge Toggles 3-Frame Buffer" `li r3,3`/`li r3,0` @ `0x8085B784` (primary datamine) |

## 1. Melee — no general input buffer

**SmashWiki, *Buffer* (secondary, the repo's citable tier):**

> "Much like its predecessor, *Super Smash Bros. Melee* does not buffer inputs in general, save
> for a select few."

The exceptions are stick/shield edge cases (e.g. C-stick out-of-shield), **not** attack/special
re-presses during a move.

**meleelight (local Melee reimpl, `~/Documents/Study/JavaScript/meleelight/`, #616) —
corroborating engine logic.** Its `InputBuffer` type is a rolling array of raw per-frame
controller snapshots, used for edge-detection (was-A-pressed-this-frame), **not** an action queue
that carries a move across an animation:

```js
// src/input/input.js
export type InputBuffer = Array<Input>;   // Input = one frame's raw a/b/x/y/stick state
```

**Interpretation (labeled):** Melee reads inputs live on the actionable frame; a re-press during
a committed move is not queued. An attack pressed mid-move only acts if the character happens to
be actionable that frame.

## 2. Brawl — universal 10-frame buffer (applies to attacks)

**SmashWiki, *Buffer* (secondary):**

> "When the player is performing an animation, there is a window of 10 frames at the end of most
> moves and animations where the player can buffer any action, including attacks, jumps, and
> dodges."

This is the one case where a **mid-move attack re-press IS buffered**: a press in the last ≤10
frames before the move becomes actionable is remembered and executes on the first actionable
frame (IASA). (Numerous per-move exceptions exist — jump first-frame, aerials out of non-tumble
hitstun, ledge options, grab aerials — but attacks are in scope by default.)

**PM codeset (primary datamine, `~/Documents/Study/reference/Project-M-CC/`, #664) —
mechanism + base value.** Two optional Gecko codes both hook the same engine address
`0x8085B784` (the buffer-window computation). The handicap-scale code's fallback preserves the
Brawl base value:

```
Buffer Scale = Handicap Scale [Y.S., Phantom Wings]
* C285B784 00000006   ; C2 hook @ 0x8085B784
* 807F002C 3C809018   ; lwz r3,0x2C(r31) ; lis r4,0x9018
* 806300F4 60840FDC   ; lwz r3,0xF4(r3)  ; r4 = 0x90180FDC (per-player handicap)
* 1C63005C 7C83202E   ; mulli r3,r3,0x5C ; lwzx r4,r3,r4
* 3860000A 2C040064   ; li r3,10         ; cmpwi r4,100   <-- base buffer = 10 frames
* 40800008 7C641BD6   ; bge +8           ; divw r3,r4,r3  (scale down by handicap)
* 60000000 00000000
```

`3860000A` = `li r3, 10` establishes the **10-frame** base at the buffer address — the
Brawl-inherited value PM starts from before overriding it (§3).

## 3. PM 3.6 — no buffer by default; 3-frame opt-in (*Input Assistance*)

**SmashWiki, *Project M* (secondary):**

> "No buffering by default, though players can turn on *Input Assistance* to implement a
> three-frame buffering window for helping newer players master advanced techniques."

> "Online matches instead have a different Buffer option that replaces handicaps, from 1 to 30,
> with these numbers being the respective amount of buffer frames."

**PM codeset (primary datamine) — the override mechanism.** PM replaces Brawl's buffer at the
same `0x8085B784` with a value that is **0 or 3** frames, gated on a toggle:

```
Damage Gauge Toggles 3-Frame Buffer [InternetExplorer]
* C285B784 00000004   ; C2 hook @ 0x8085B784
* 3C609017 6063F36C   ; r3 = 0x9017F36C (the toggle byte)
* 88630000 2C030001   ; lbz r3,0(r3) ; cmpwi r3,1
* 38600000 40820008   ; li r3,0      ; bne +8       <-- toggle off → 0-frame buffer
* 38600003 00000000   ; li r3,3                     <-- toggle on  → 3-frame buffer
```

`li r3,0` (default branch) / `li r3,3` (toggle-on branch) confirms PM's buffer window is **0 or
3 frames**, overriding Brawl's 10 — matching the SmashWiki "no buffer by default / 3f Input
Assistance" statement.

**Caveat (faithful labeling):** these are optional Gecko codes present in the codeset *text*;
the codeset alone does not prove which toggle ships *active* in retail. The retail-default claim
("no buffer") rests on the SmashWiki *Project M* secondary; the codeset **corroborates the
mechanism and the concrete window values** (0 / 3, not 10). The two agree.

## 4. Mid-move applicability (the exact #1087 case)

- **Melee / PM 3.6 default:** an attack/special pressed **while a move is running** is **not
  buffered**. It is dropped; the next action requires a live press once the character is
  actionable. ← matches #1087 hard-drop.
- **Brawl (and PM Input Assistance, ≤3f):** a press in the last ≤10f (≤3f) before actionable
  **is** buffered and fires at IASA.

pycats's *current* bug is neither of these: a mid-move re-press **restarts** the move to frame 1
(`MoveClock.start()` resetting `_frame=0`). No game does that — every game either drops the press
(Melee / PM default) or buffers it to IASA (Brawl / PM assist). Both #1087 (hard-drop) and #1089
(buffer-to-IASA) correctly kill the restart; they differ only in what happens to a **late** press.

## 5. Verdict for #1087

**Hard-drop is FAITHFUL to PM 3.6's default behavior.** PM 3.6 default has no input buffer, so a
mid-move attack re-press is dropped — exactly what the V1 engine guard does. No divergence for the
default parity target.

**#1089 (buffer-to-IASA) is optional, not required.** It maps to PM's opt-in *Input Assistance*
(3-frame buffer), which is off by default. It is a feature to emulate later if desired, not a
correction the baseline needs.

**Residual gap (already scoped elsewhere, not a buffer issue):** even with no buffer, PM reads
inputs **live on the IASA frame** — a press exactly on/after IASA still triggers the next action.
pycats has no per-move IASA field yet, so V1 gates on move-complete instead (the hard-drop floor).
Closing that boundary is the **IASA-aware interrupt** already scoped to #1089 / #1071 — an
IASA-liveness refinement, distinct from buffering. Hard-drop until move-complete is the faithful
V1 approximation of PM-default no-buffer.

## Sources

- **SmashWiki — *Buffer*** (secondary, citable): https://www.ssbwiki.com/Buffer — Melee "does not
  buffer inputs in general, save for a select few"; Brawl "window of 10 frames at the end of most
  moves and animations … any action, including attacks".
- **SmashWiki — *Project M*** (secondary): https://www.ssbwiki.com/Project_M — "No buffering by
  default, though players can turn on *Input Assistance* to implement a three-frame buffering
  window"; online Buffer option 1–30 frames.
- **PM 3.6.1 codeset (primary datamine, #664):**
  `~/Documents/Study/reference/Project-M-CC/[Text Codesets]/codes-cc-3_61.txt` — "Damage Gauge
  Toggles 3-Frame Buffer" (`li r3,3`/`li r3,0` @ `0x8085B784`); "Buffer Scale = Handicap Scale"
  (`li r3,10` base @ `0x8085B784`).
- **meleelight (local Melee reimpl, #616):**
  `~/Documents/Study/JavaScript/meleelight/src/input/input.js` — `InputBuffer = Array<Input>`
  (per-frame history, not an action queue). Corroborates "no action buffering" (interpretation).

## Refs

Blocks #1087 (engine hard-drop). Spec/ruling #1079 (Q2). Post-V1 buffer branch #1089. Canon
#1060 (fireball 49f / IASA 40). Research basis #1071. Epic #925. Sourcing map:
[`../pm-reference/where-to-find-source-data.md`](../pm-reference/where-to-find-source-data.md).
Memory: [[pm36-canonical-reference]], [[rukaidata-engine-hardcoded-limit]],
[[meleelight-engine-logic-source]].
