# Golden regen-review protocol (S4)

Three test modules honor `PYCATS_UPDATE_GOLDENS=1` and record a committed
baseline under `tests/golden/`:

| Module | Golden(s) | Sidecar? |
|---|---|---|
| `tests/test_golden.py` | sim per-frame snapshots — `combat`, `default`, `full_match`, `two_npc` (`<name>.json`) | yes — `<name>.summary.json` |
| `tests/test_golden_summary.py` | asserts those `.summary.json` sidecars stay in lock-step with the run | (the sidecars themselves) |
| `tests/test_screen_parity.py` | statechart screen-flow trace — `screen_parity.json` | no (single FSM-trace blob) |

The `test_golden.py` goldens compare a deterministic battle's per-frame snapshots
against `tests/golden/<name>.json`. They catch **any** divergence — but the raw
`.json` is a large, opaque blob, and `PYCATS_UPDATE_GOLDENS=1` re-records it with
**zero scrutiny**. That makes it easy to launder a regression into a new baseline
("tests failed → regen → green"). This protocol exists so a regen is **reviewed,
not rubber-stamped**. The reviewable sidecar layer below applies to the sim
goldens; `screen_parity.json` has no sidecar, so review its diff directly (the
transition sequence must change only where a screen/statechart change explains it).

## Two artifacts per golden

| File | Role | Reviewable? |
|---|---|---|
| `<name>.json` | byte-identical **detector** — fails on any per-frame difference | No (opaque) |
| `<name>.summary.json` | semantic **digest** — frames, phase/winner, attack-active frames, and per-player states / lives (start·end·min) / max-percent / **KO frames** | **Yes** (≈0.6 KB) |

`golden_util.check_or_update` keeps both in lock-step: it regenerates the sidecar
with the raw golden, and in check mode asserts the sidecar still matches the run —
so a behaviour change fails with the **small readable summary diff first**, before
the opaque byte comparison.

## When a regen is legitimate

A golden regen is only acceptable when **a code change you understand** changes
the simulation on purpose (e.g. a combat/physics/controller change). "The test is
red and I don't know why" is **never** a reason to regen — investigate first.

## Reviewer checklist — before accepting `PYCATS_UPDATE_GOLDENS=1`

1. **Identify the cause.** There must be a specific code change in the same diff
   that explains the golden change. No cause → it's a regression; stop.
2. **Read the sidecar diffs, not the blob.** `git diff tests/golden/*.summary.json`.
   For every changed field, confirm the code change explains it:
   - `frames` — match length changed (e.g. a faster KO ends the match sooner).
   - `players.<P>.ko_frames` / `lives_*` — stocks gained/lost. A KO **disappearing**
     or `lives_end` rising is a red flag (combat got weaker — likely a regression).
   - `percent_max` — damage output. Dropping toward 0 is a red flag.
   - `states` — a state no longer reached (e.g. `hurt`/`ko` gone) means combat
     stopped connecting — almost always a regression.
   - `winner` / `final_phase` — the match now resolves differently.
   - `attack_active_frames` — hitbox activity changed.
3. **Cross-check the raw goldens regenerated** (`git diff --stat tests/golden/*.json`)
   — every raw change should have a corresponding intended sidecar change (a
   position-only tweak can change the raw without the sidecar; that's fine and
   expected, e.g. a hitbox offset move).
4. **Explain it in the commit.** State which behaviour changed and why the goldens
   were regenerated — a *semantic* regen, not a blind one.
5. **Re-run the suite** after regen: `PYTHONPATH=. .venv/bin/python -m pytest -q`.

## Tuning-value changes interlock with the provenance drift-guard (ADR-0003 / #233)

A combat/physics tuning constant (`pycats/config.py`) is mirrored by a `Provenance`
row in `pycats/combat/provenance.py`. If a golden regen is justified by **changing a
tuning value**, the same diff must update that constant's `Provenance.value` (and its
`status` / `issue`), or `tests/test_tuning_provenance.py` reds. So a value change
forces both a reviewed golden regen (above) **and** a provenance update — never a
silent regen.

## How to regen

```
make goldens
```

This runs the three flag-honoring modules above with `PYCATS_UPDATE_GOLDENS=1`
(headless env supplied by the Makefile) and prints a review reminder. It rewrites
every `<name>.json`, its `.summary.json` sidecar (sim goldens), and
`screen_parity.json` in one command. Commit them together with the code change
that justifies them.

Equivalent raw invocation (if you can't use `make` — e.g. a partial regen of one
module):

```
PYCATS_UPDATE_GOLDENS=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/test_golden.py tests/test_golden_summary.py tests/test_screen_parity.py
```
