# Ledge grabs-left dots render while standing on the platform top (getup climb) — findings (#906)

**Role:** RESEARCH · area:combat · combat:ledge. Reproduce + spec; no code change here.
**As-of:** repo @8837713 (2026-08-01). Repro harness: `repros/ledge_bar_on_platform_906.py` (gitignored).

## TL;DR

The above-head indicator that appears "while standing on the platform, not hanging" is the
**grabs-left dots (#657)** — the anti-plank regrab counter's `LEDGE_REGRAB_INTANGIBLE_CUTOFF+1-n`
dots — **not** the INTANG burst bar (#683) and **not** a residual HANG bar (#348, removed by #475).

It is a **display/spec** issue, **not** a state-detection false positive. The fighter is genuinely
in the `ledge_getup` state (it grabbed the ledge, then pressed up), but during that 16-frame climb
window (`LEDGE_GETUP_FRAMES`) the body is snapped to `getup_topleft` — feet on the lip, visually
standing on the stage top — while the dots keep rendering. `grabs_left_dots`' active predicate keys
only on `ledge_regrab_count ≥ 1` and does not exclude the getup-climb window.

## Questions answered

### Q1 — state vs display: state false-positive, or a stale display flag?

**Neither the "false grab while grounded" nor a "stale/uncleared timer" framing is right — it's a
display predicate that is too broad.** Two facts pin this:

- The auto-grab guard in `Player._try_ledge_grab` (`pycats/entities/player.py`) requires
  `not self.fighter.on_ground and self.fighter.vel.y >= 0`. A fighter standing on the platform top
  (`on_ground == True`) **cannot** trip a grab, so there is no grounded state false-positive.
- The repro's DISPLAY_BUG probe — *grounded (`on_ground`) AND off any ledge (`grabbed_ledge is None`)
  AND a ledge indicator live* — fired **0 times** across all 9 levels. Once the getup climb ends and
  physics resumes, `_handle_landing` (`pycats/entities/fighter.py`) fires (airborne→grounded) and
  resets `ledge_regrab_count = 0`, so the dots do **not** linger into a genuine idle stand.

The window where the indicator shows over a visually-standing body is exactly the `ledge_getup`
climb: `grabbed_ledge` is still set (engine still considers it on the ledge), but `rect` is at
`getup_topleft` and `_step_physics` is skipped, so the sprite is drawn on top of the platform.

### Q2 — which indicator, and what drives it

**The grabs-left dots**, `grabs_left_dots(p)` in `pycats/systems/status_model.py`:

```
count = p.fighter.ledge_regrab_count
if count < 1 or count > LEDGE_REGRAB_INTANGIBLE_CUTOFF: return 0
return LEDGE_REGRAB_INTANGIBLE_CUTOFF + 1 - count      # first grab -> 5 dots
```

Driver: `ledge_regrab_count`, incremented on each auto-grab (`_try_ledge_grab`) and reset **only** in
three places (`pycats/entities/fighter.py`): `_handle_landing` (physics land), on receiving a hit, and
on KO/respawn. **A ledge getup resets it via none of these** — the getup completes inside
`Player._drive_ledge_hang` by clearing `grabbed_ledge` when `ledge_getup_timer == 0`, without touching
`ledge_regrab_count`. The reset happens one frame later, when the first post-getup physics step detects
the landing.

Ruled out:
- **INTANG burst bar (#683)** — the `ledge_intangible` source (`ledge_intangible_timer > 0`). On the
  up-press, `_drive_ledge_hang` sets `ledge_intangible_timer = 0` and `intangible = False`, so the
  INTANG bar is off for the entire getup. (Confirmed: no `intang_t > 0` in any flagged frame.)
- **LOCKOUT** — `ledge_regrab_lockout_timer` is armed only on a *drop* (down/away), not a getup.
- **Residual HANG bar (#348)** — removed when #475 dropped the hang timeout; not in `STATUS_SOURCES`.

### Q3 — intended spec for the ledge indicators (so "standing on the platform" is excluded)

| Indicator | Source predicate (current) | Should be visible when… |
|---|---|---|
| Grabs-left dots (#657) | `1 ≤ ledge_regrab_count ≤ 5` | The fighter is **hanging** on a ledge (an active regrab chain the player can still spend). It should **not** show once the fighter has committed to the stage via getup — a getup reaches the stage, which is the same event (`landing`) that resets the anti-plank count. |
| INTANG burst bar (#683) | `ledge_intangible_timer > 0` | Only during the hang (already correct; zeroed on up-press). |
| LOCKOUT (#357) | `ledge_regrab_lockout_timer > 0` | After a *drop*, suppressing regrab (already correct). |

The gap: the dots' predicate covers the `ledge_getup` climb window, which is visually a stand on the
stage. PM's anti-plank counter resets on landing on the stage; a neutral getup **is** reaching the
stage, so the count (and thus the dots) should clear at getup, not one frame after physics resumes.

### Q4 — deterministic repro

`repros/ledge_bar_on_platform_906.py` replays watch.py's leveled CPU sim (nalio vs birky, seed 7,
levels 1–9) and, per frame per player, reads the live ledge state + indicator sources.

Run:
```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
  <main-venv-python> repros/ledge_bar_on_platform_906.py
```

Pinned occurrences (seed 7): **Lv3 P2 (birky) frames 751–782**, Lv5 P1 frames 875–890, Lv8 P2
frames 606–621. Cleanest single pin — **seed 7, Lv3, frame 751, P2**:
`state=ledge_getup, dots=5, ledge_regrab_count=1, ledge_getup_timer=16, on_ground=False, rect.y=366`
(platform-top y). The dots render for all 16 climb frames. Totals: 64 GETUP_ON_TOP frames, 0
DISPLAY_BUG frames.

## Root-cause layer & recommended fix direction (for a follow-up DEV ticket)

**Layer: display + spec.** Two candidate fixes; the choice is a small semantic call for the DEV/human:

1. **Display-only (narrowest):** make `grabs_left_dots` return 0 during the getup climb — e.g. gate on
   `p.state != "ledge_getup"` (or, more precisely, "hanging" = `grabbed_ledge is not None and
   ledge_getup_timer == 0`). Leaves the anti-plank count semantics untouched; the dots simply stop
   drawing once the fighter starts climbing.
2. **State/timing (aligns the model):** reset `ledge_regrab_count = 0` when the getup commits (the
   up-press in `_drive_ledge_hang`) or completes (`ledge_getup_timer == 0`), so the anti-plank chain
   ends the moment the fighter reaches the stage — matching PM's "reset on landing". This also turns
   the dots off, and additionally makes a grab→getup→jump→regrab count as a fresh chain (grab 1), which
   is the PM-consistent behavior. **Semantic note for the human:** confirm this is the intended
   anti-plank reset point before adopting (2).

Recommendation: (2) is the more model-faithful fix (it corrects *when* the anti-plank count clears, of
which the dots are just the readout), but it changes a gameplay-facing count; (1) is a zero-risk
display patch if the count-reset timing is deliberately post-getup. Either way the regression test is
"at seed 7 / Lv3 / frame 751, P2 shows 0 grabs-left dots while `state == ledge_getup`" — able-to-fail
(red on current `main`, which shows 5).

## Refs

Surfaced during the #902 CPU ledge-getup demo. Indicator: grabs-left dots #657/#658; anti-plank
counter #656; INTANG burst #683; LOCKOUT #357; hang-timeout removal #475; status registry #513/#522;
ledge state #14; ledge epic #751.
