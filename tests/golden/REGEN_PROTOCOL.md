# Golden regen-review protocol (S4)

The golden tests (`tests/test_golden.py`) compare a deterministic battle's
per-frame snapshots against a committed baseline in `tests/golden/<name>.json`.
They catch **any** divergence — but the raw `.json` is a large, opaque blob, and
`PYCATS_UPDATE_GOLDENS=1` re-records it with **zero scrutiny**. That makes it easy
to launder a regression into a new baseline ("tests failed → regen → green").
This protocol exists so a regen is **reviewed, not rubber-stamped**.

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

## How to regen

```
PYCATS_UPDATE_GOLDENS=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=. .venv/bin/python -m pytest tests/test_golden.py -q
```

This rewrites both `<name>.json` and `<name>.summary.json`. Commit them together
with the code change that justifies them.
