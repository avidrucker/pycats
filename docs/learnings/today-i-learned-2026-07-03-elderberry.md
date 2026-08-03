# TIL 2026-07-03 — ELDERBERRY

**Context:** A long multi-day session (2026-07-01 → 07-03) on two arcs: fixing + verifying the Nalio-vs-Birky feature-showcase demo (#355 spike, #395 audit → #397/#398/#411/#412/#419), then building the *user profiles & custom keybindings* epic (#438) from scratch — the rebindable `Keymap` (#439→#447→#455), persistence (#440), and the scoping spikes (#464/#465) that converged on one shared text-entry widget (#471). Most tickets went review → rewrite → TDD implementation.

---

## 1. Review your own ticket to READY *before* you build it

**What happened:** I ran `/issue-review-skill` on my own tickets before implementing. #440 scored **10/15 (NEEDS WORK)** and #471 **11/15** on the first pass — both because a decision was deferred ("decide with slice 3", "maybe space", "backspace as cell or key"). After a rewrite that *resolved* those decisions, each hit **15/15**, and the implementation had zero "wait, where does this go?" moments. The review's fold-in note for #440 — "apply a saved set by **wholesale replace**, not sequential rebinds" — is literally the thing that makes the key-swap test pass (sequential `rebind`s raise a transient `KeyBindingConflict` mid-load).

**What I learned:** A ticket I wrote is not automatically agent-ready. The review's value isn't catching *other people's* vagueness — it's forcing me to make the deferred decision on paper (storage location, serialization format, cell dispatch) instead of hitting it mid-TDD, where it costs a redesign.

**The rule:** **Score a ticket to READY and resolve every deferred decision before claiming it — the ambiguity you leave becomes a mid-build redesign.**

---

## 2. A scoping spike's best output is a shared foundation, not N per-feature designs

**What happened:** #463 (keybinding-set UI) and #441 (player profiles) both needed typed input, and the screen system has none. Two spikes (#464, #465) *both* landed on the same answer — a reusable on-screen keyboard — so instead of two text-entry designs I filed **one** widget (#471) that both consume, and #465 explicitly deferred its nickname entry to #464's decision. Building #471 then unblocked *two* features at once.

**What I learned:** When two fuzzy features share a hard sub-problem, the spike's job is to find the shared primitive and file it once — not to design each feature in isolation. The tell was that both spikes' hardest open question was identical.

**The rule:** **When multiple blocked features hinge on the same missing primitive, scope and file that primitive as one shared ticket; the consumers just wire it in.**

---

## 3. Split the pure model from the pygame surface, and land the core first

**What happened:** Every UI feature this session split the same way: `Keymap` model (#439) → `KeybindMenu` controller (#447) → Options screen (#455); `keybind_store` (#440) vs its UI (#463); `TextEntry` model (#471) vs its hosting (#463/#441). The pure model is fully red-green TDD-able and screenshot-independent; the render/wiring is a thin layer verified by a headless screenshot.

**What I learned:** "TDD as much as possible" on a pygame feature means drawing the seam at the pure model. Screens only receive `frame_input.pressed` (not raw events), which is exactly what let the capture flow live in a pure controller driven by synthetic pressed-sets — no display needed to test it.

**The rule:** **Draw the seam between the pure state model and the pygame render/wiring; TDD + land the model as its own unit, then verify the thin surface with a screenshot.**

---

## 4. A new capability with a byte-identical default keeps goldens/parity green

**What happened:** `Keymap` is a `dict` subclass, so it dropped into every `controls["attack"]` read with zero consumer changes and the sim goldens untouched. The nickname (#465 scope) is a *separate* `Player.nickname` field defaulting to `None` → renders "P1"/"P2" exactly as before. The `--demo-speed`/dwell/caption features are presentation-only — the sim never sees them.

**What I learned:** The render-parity oracle (`test_battle_screen_render.py`) and sim goldens flip on *any* default-path change. The way to add a feature without a golden regen is to make the opt-in path the only thing that differs and keep the no-feature default byte-identical.

**The rule:** **Add capability behind an opt-in whose *absence* is byte-identical to today — a `dict` subclass, a `None`-default field — and the goldens never move.**

---

## 5. Verify the domain before you trust the ticket's premise

**What happened:** The showcase "KO" beat looked like a mis-feature — so I checked, and the default cats are **jab-only** (no smash/launcher, `combat/charge.py`): a real combat KO is *impossible*, the only KO is a walk-off self-destruct (which #395 flagged). Separately, I nearly recommended overwriting `char_name` with the nickname — until `battle_screen.py:65` revealed `char_name` is **win-attribution identity**, not a display string, and the label colour keys off `char_name == "P1"`. So the nickname *has* to be a separate field with slot-based colour.

**What I learned:** Two would-be bugs were actually load-bearing facts. "This should KO" and "just rename char_name" were both wrong in ways only the code could tell me. Also: I confidently claimed specials/smashes "can't be scripted" in a research doc — wrong; `special` was already in the demo keymap and `ACTIONS` isn't enforced. A user pushback caught it.

**The rule:** **Before scoping around a premise ("this KOs", "this field is free", "that input can't be expressed"), confirm it in the code — a surprising constraint is usually a fact, not a bug.**

---

## 6. Assert a feature in its *meaningful window*, not "somewhere"

**What happened:** The showcase coverage test asserted `{ATTACK, JUMP, HIT, KO}` occurred *anywhere* in the 480-frame run — and stayed green while 5 of 7 beats misrepresented their captions (#395). The `--shots` screenshot tool made the mismatch visible; #397 rebuilt the test to bind each feature to *its caption's frame window*. Same shape elsewhere: caption windows are inclusive-inclusive, so a beat's `end` equal to the next beat's `start` double-renders both captions (#419).

**What I learned:** "the event happened" is a far weaker oracle than "the event happened *when/where it was supposed to*." A HIT anywhere + a shield state anywhere independently satisfied "hit while shielding" though no hit ever touched a shield.

**The rule:** **A coverage assertion must bind the feature to its context (its frame window, its caption), not merely its existence — "happens somewhere" is not coverage.**

---

## 7. Run the whole suite — it catches self-inflicted structural breaks the new test can't

**What happened:** Wiring the keybind sub-mode into `OptionsMenu`, my first edit wedged the new `_update_keybind` method *between* `update()`'s cooldown-return and its nav/activate body — orphaning the nav code into the new method. My keybind tests passed; **15 existing options tests went red**. Restructuring `_update_keybind` into a proper standalone method fixed it.

**What I learned:** A new-feature test suite can't see damage to the code it displaced. Only the full suite does.

**The rule:** **Run the full suite (not just the feature's tests) after any edit that restructures an existing method — the regression lives in the code you moved, not the code you added.**

---

## What landed (this session)

| Area | Tickets |
|---|---|
| Showcase demo | #397 (window-bound test), #398 (re-choreograph), #411 (`--shots` tool), #412 (dwell-on-payoff), #419 (caption double-render) |
| Keybindings | #439 (`Keymap`), #447 (`KeybindMenu`), #455 (Options keybind screen), #440 (`keybind_store`), #471 (`TextEntry` widget) |
| Research/spikes | #355, #376-era research; #422 (demoable-features audit), #464/#465 (profiles/keybindings UI scope) |
| Filed + scoped for follow-on | epic #438; #441/#442/#463/#478/#479 (profiles line) |

## Open threads

- **Consolidated ADR** for the `profiles/` persistence contract + module map, recommended *before* #478/#463/#479 land so they share one contract (not yet written).
- The lessons above reinforce existing patterns (RULES → Fixing bugs / model-screen split / golden-safety); none filed as a new RULES.md entry this commit.
