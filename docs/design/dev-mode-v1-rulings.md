# `--dev` mode V1 — ratified rulings (#1297)

- **Status:** Accepted
- **Date:** 2026-08-07
- **Decision ticket:** [#1297](https://github.com/avidrucker/pycats/issues/1297) (ARC/decision)
- **Research basis:** [`docs/research/2026-08-07-dev-mode-option-space.md`](../research/2026-08-07-dev-mode-option-space.md) (#1293)
- **Companion slice:** [#1292](https://github.com/avidrucker/pycats/issues/1292) (testcat/default on char-select)

Full record for the ratified `--dev`-mode shape. The research doc (#1293) enumerated
the option space; this doc records the human designer's ruling on each atomic option
(V1 / post-V1 / scrap / spike) plus the in-battle HUD redesign. Indexed in
[`docs/decisions-ledger.md`](../decisions-ledger.md).

## Structure (A1)

One process-wide `runtime_settings.dev_mode` flag, entered through **three doors**,
all setting the same flag (one owner):

1. Env var `PYCATS_DEV=1` (mirrors the existing `PYCATS_DEV_LOG` convention).
2. `--dev` CLI arg on `pycats.game` `parse_args`.
3. In-game **F1** key → a dedicated debug screen.

Rejected: comma-list sub-toggles (`--dev=hitboxes,...`) and env-only. A later
`--dev=<list>` value form is not foreclosed but is out of V1 scope.

## Keys

- **Backtick / tilde** — toggles the in-battle **dev HUD**. Available in the **shipping
  (non-dev) build for everyone**, matching "a single button press in regular gameplay."
- **F1** — opens the dedicated **debug screen** (dev-mode), which hosts the granular
  debug toggles.
- Free keys confirmed at ruling time: F1–F9, F12, backtick/tilde. Taken: F10/F11
  (fullscreen), `E`/`;` (cat-face cycle, #108), `P` (pause).

## In-battle HUD redesign

- **Default (dev-HUD-off) HUD — minimal:** Lives + Damage% + player label only.
  Everything else moves into the dev HUD. *This removes elements from the shipping
  default HUD (FPS, raw input string, jumps-remaining, shield-HP number) → the DEV
  ticket implementing it is player-visible and needs a human eyeball-OK before close.*
- **Dev HUD (backtick-on) contents:** the moved-out items (jumps-remaining, shield-HP,
  FPS, raw input string) **plus** FSM state + shield-attempting + movement status
  (the existing `show_dev_info` / movement rows) + input-history grid (PM notation) +
  last-hit damage/knockback readout (B13).
- **Pause menu:** unchanged (resume / options / quit).
- **Options menu:** stays player-facing; the granular debug toggles
  (`hitbox_overlay`, `movement_status`, `input_history`) are **removed from it** and
  live only in the F1 debug screen — one owner per toggle.
- **Persistence:** dev-HUD on/off state persists across pause (pausing does not reset it).

## Affordance dispositions

Numbering follows the #1293 findings table. Cost S≈hours, M≈a day, L≈multi-day.
"Cheat" = mutates sim state (must be explicit opt-in, never default-on, gated out of
golden/CI/`runner` runs, with an able-to-fail no-drift test).

| # | Affordance | Disposition | Note |
|---|---|---|---|
| A1/C1–C4 | dev-mode gate + keys + HUD redesign | **V1** | above |
| B1 | testcat/default selectable on char-select | **V1** | already filed as #1292 |
| B2 | hitbox/hurtbox overlay: **on in dev mode, off otherwise**, **removed from Options menu**; backtick master-toggles it within dev mode | **V1** | see reconciliation below |
| B10 | default-on `PYCATS_DEV_LOG` when dev mode is enabled | **V1** | S, reuses `dev_log.py` |
| B16 | overlay per-side split (hitbox-only / hurtbox-only) in the F1 screen | **V1** | S; F1 screen already in V1 |
| B8 | seed display/set in the live game | **V1** | M; seed plumbing is CLI-only today |
| B12 | instant-respawn / stock refill | **V1** | **cheat** — explicit opt-in + no-drift test |
| B13 | last-hit damage/knockback readout | **V1** | lives in the dev HUD |
| B4 | on-screen velocity + timers readout | post-V1 | M |
| B5 | frame-step / single-advance | post-V1 | M; top training-mode feature |
| B6 | live in-game speed toggle | post-V1 | M; reconcile with #933 |
| B9 | in-game battle event-log console | post-V1 | M–L; `watch.py --log` covers it out-of-game |
| B11 | god-mode / no-KO | **scrap** | won't-do |
| B15 | stage/spawn position tweaks | **scrap** | won't-do |
| B14 | free camera / zoom | **spike** | camera is fixed today (net-new pan/zoom, L); disposition set by the spike result |

### B2 reconciliation

Because the dev HUD (backtick) is shipping-available but the overlay is dev-mode-gated:
**outside dev mode**, backtick toggles only the text dev HUD (the overlay never shows);
**inside dev mode**, the overlay defaults on and backtick's master switch flips both the
text HUD and the overlay together. Granular per-side control lives in the F1 screen (B16).

## Constraints carried into V1

1. **Player-visible default-HUD change** (minimal HUD) → its DEV ticket needs a human
   eyeball-OK before `pmtools close`, even with a green suite.
2. **A sim cheat is in V1** (B12 instant-respawn) → V1 scope includes cheat gating
   (never default-on; inactive in golden/CI/`runner` runs) and an able-to-fail test
   proving no `pycats/sim/runner.py` snapshot drift.
3. **Sim determinism preserved** — every non-cheat V1 affordance is
   presentation/inspection-only.

## V1 slice list (feeds the epic tracker)

Filed one-at-a-time downstream of this doc; the dev-mode gate is the foundation the
rest depend on.

1. **dev-mode gate** — `--dev` flag + `PYCATS_DEV=1` + `runtime_settings.dev_mode`
   (F1 debug-screen entry may be its own slice). *Foundation — file/land first.*
2. **char-select: testcat/default under dev mode** — #1292 (re-based onto the gate).
3. **HUD redesign** — minimal default HUD + backtick dev-HUD toggle + dev-HUD contents.
4. **hitbox/hurtbox overlay dev-gating** — on in dev, off otherwise, removed from Options.
5. **F1 debug screen** — hosts granular toggles incl. overlay per-side split (B16).
6. **default-on `PYCATS_DEV_LOG`** under dev mode (B10).
7. **seed display/set** in the live game (B8).
8. **instant-respawn** cheat (B12) — explicit opt-in + no-drift test.
9. **last-hit damage/knockback** readout (B13) — if not folded into slice 3.

## Post-V1 (parked)

B4 (velocity+timers), B5 (frame-step), B6 (live-speed toggle), B9 (event-log console).

## Scrapped (won't-do)

B11 (god-mode), B15 (spawn tweaks).

## Spike (disposition pending result)

B14 (free camera / zoom) — the camera is fixed today; run an experiment, then rule V1 /
post-V1 / neither from the result.
