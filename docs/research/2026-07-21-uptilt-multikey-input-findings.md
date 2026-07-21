# Up + A multi-key input — does holding Up and pressing A fire the up-tilt?

**Ticket:** #845 (research · `area:combat`) · surfaced from #841 (Gnok tilts, u-tilt bound to grounded up-A)
**Date:** 2026-07-21 · **Agent:** DRAGONFRUIT
**Question:** When Up and the A (attack) button are pressed/held together on the ground, does the input register as `direction="up"` + attack and fire the **up-tilt** — or is it read as a jump / up-smash / neutral jab? And what disambiguates an up-**tilt** from an up-**smash**?

**Answer in one line:** The up-tilt fires **only when Up is already held** as A is pressed. A **simultaneous** Up + A (both pressed the same frame) with a jump available fires a **jump**, not the up-tilt — tap-jump is always on and the jump branch consumes the fresh up-press before move-select is reached. Tilt-vs-smash is decided by **separate dedicated keys** (attack `V` vs smash `B`), not by any timing/stick-flick threshold.

---

## Seam under test

The already-tested layer is `combat/move_select.py :: resolve_move_key` — a pure map from `(direction, on_ground, is_special, is_smash)` to a move key; `("up", ground, …) -> "utilt"` is unit-tested. What was **not** tested is the layer below it, `entities/fighter_input.py :: FighterInput.handle_actions`, which turns a held/pressed key set into an action and only *sometimes* reaches move-select.

`handle_actions` runs its branches in order:

1. **Smash charge** (mid-charge only)
2. **Double-tap dash** (arms/starts a dash; never consumes the frame)
3. **Jump** — `jump_pressed = self._pressed(pressed, "up")`; if a jump is available and state allows, sets `vel.y = jump_vel` and **`return False`** (early exit)
4. Dodge / shield
5. **Attack / Special / Smash** (move-select seam) — reads `direction` from `_move_direction(held)`

The jump branch (3) sits **before** the attack branch (5) and reads the **fresh-press** set (`pressed`), while the attack branch reads the **held** set for its direction. That ordering is the whole finding.

## Live control bindings (`app.py`)

| Action | P1 | P2 |
|---|---|---|
| up | `W` | `↑` |
| attack | `V` | `/` |
| smash | `B` | `'` |
| special | `C` | `.` |
| shield | `X` | `,` |

Tap-jump is unconditional: `up` **is** the jump input (there is no tap-jump toggle). Smash is a **dedicated key**, not a stick-flick.

## Q1 — Registration: does Up + A resolve to the up-tilt?

**Only via the held-Up path.** Measured at the `handle_actions` seam on a grounded fighter whose up-A maps to `utilt` (nalio; the seam is character-independent):

| Input (grounded) | Result |
|---|---|
| Up **held** (from a prior frame) + A freshly pressed | **utilt** ✓ (no jump) |
| Up + A **both fresh, same frame**, jump available | **Jump** (spends a jump, `vel.y < 0`); no attack starts |
| A held + Up freshly pressed | Jump (up is fresh) |
| Up + A both fresh, **0 jumps remaining** | **utilt** (jump guard fails → falls through) |
| A alone (neutral) | jab ✓ |

Root cause: on a fresh up-press the jump branch fires and `return`s before the attack branch. Up-select in the attack branch reads `held`, so once Up has persisted one frame (no longer "fresh") the jump branch skips it and the attack branch sees `direction="up"` → utilt.

## Q2 — Tilt vs smash disambiguation

**Separate dedicated keys, no timing threshold.** `is_smash = self._pressed(pressed, "smash") and on_ground` — up-**tilt** is Up + `V` (attack); up-**smash** is Up + `B` (smash). There is no flick-window or tap-vs-hold heuristic distinguishing them, so there is no tilt/smash ambiguity to characterize. (The sim keymaps bind no `smash` key at all, so sim-driven fighters never smash — `_pressed` is binding-tolerant.) The up-**smash** input inherits the *same* jump-eats-fresh-up gap: a simultaneous Up + `B` with a jump available also jumps first.

## Q3 — Order / timing sensitivity

Order is decisive, and it is a **fresh-vs-held** distinction, not a millisecond window:

- **Up-then-A** (Up held ≥1 frame, then A): up-tilt. ✓
- **Simultaneous** (same frame): jump (unless no jump is available).
- **A-then-Up**: the fresh up-press jumps; A is stale by then anyway.

"Held vs tapped" only matters for the up-press: a *tapped* (single-frame) up that coincides with A jumps; a *held* up that precedes A tilts.

## Q4 — Live-loop fire

The measurements above drive the real `handle_actions` seam (not `resolve_move_key` in isolation), so they reflect the live per-frame input path, past the `game.py` import-time dispatch blindspot. **A human playtest is still required** to confirm the on-screen feel — specifically whether a player *intending* an up-tilt reliably lands in the held-Up path or keeps jumping. Confirmed by the human test below.

## Automated test

`tests/test_uptilt_multikey_input.py` pins all of the above as characterization tests (able-to-fail: perturbing `_move_direction`'s up-detection turns the two utilt-expecting cases red — utilt → jab — verified by revert-check):

- `test_up_held_then_a_fires_the_up_tilt` — the working path.
- `test_up_and_a_same_frame_jumps_instead_of_up_tilt` — the gotcha.
- `test_up_and_a_same_frame_tilts_when_no_jump_is_left` — the 0-jumps corner.
- `test_neutral_a_still_fires_the_jab` — harness baseline.

## Human test — DONE (2026-07-21)

Playtest: pick a fighter with an up-tilt (Gnok, after #841 merged), stand grounded, and try to throw an up-tilt with Up + A.

- **Result: confirmed.** The human ran it and reported the characterized behaviour matches on-screen — Up-held-then-A produces the up-tilt; a simultaneous Up + A jumps. No new discrepancy vs the sim characterization.
- **Caveat noted:** the hitbox is only present for the move's brief active window (a tilt's ~4–6 active frames ≈ 0.07–0.10 s), so the box is hard to *see* during a live playtest — the confirmation is of the input/behaviour, not a frame-by-frame visual read. Making the boxes visible (a debug hitbox/hurtbox overlay and/or frame-step) would ease future eyeball checks — tracked as an observability idea, not filed here.

## Assessment & downstream (filed after this doc)

The held-Up path works; move-select is wired correctly. The open question is a **design fork**, not a wiring bug: with tap-jump permanently on, a grounded simultaneous Up + A jumps instead of up-tilting. That is arguably faithful to tap-jump-on Melee/PM, but there is no tap-jump toggle and no jump-squat A→up-tilt buffer, so the up-tilt is harder to access than a player expects.

Downstream tickets filed (the human ruled to pursue the design fork, research-first):

- **#864 (research):** characterize how PM/Melee resolve grounded Up+A with tap-jump on, whether PM has a tap-jump toggle, jump-squat buffering, and a pycats option matrix — produces `docs/research/2026-07-21-tapjump-vs-uptilt-access.md`.
- **#865 (decision, blocked on #864):** rule on whether/how pycats changes grounded Up+A to favour the up-tilt. Blocked until #864's findings land; a downstream DEV follows the ruling.

The held-Up path itself showed **no defect** in the human test, so no DEV fix ticket is warranted on registration grounds — only the design decision above.

## Out of scope

Fixing the tap-jump/up-tilt interaction (that is the contingent ARCHITECT/DEV work). Other multi-key combos beyond the directional-A tilt path.
