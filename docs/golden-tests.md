# Golden tests — onboarding + glossary

New to pycats goldens (or staring at a red `test_golden_*` for the first time)? Start here.
This is the plain-English **onboarding home** for the golden system. Two companion docs go
deeper: [`tests/golden/REGEN_PROTOCOL.md`](../tests/golden/REGEN_PROTOCOL.md) owns the
**regen review procedure**, and [`docs/research/golden-system-findings.md`](./research/golden-system-findings.md)
(from #992) is the fuller write-up + the option space that spawned the tooling work.

## The one-sentence version

A **golden test** runs a fixed, deterministic simulation, records exactly what happened, and
on every later run re-runs the same sim and checks that *exactly* the same thing happened. If
a code change moves the sim, the golden fails — that's either a regression you just caught, or
a change you meant to make and must now re-record on purpose.

Nothing about a golden is random or wall-clock-dependent: same inputs → same frames → same
recorded bytes. That determinism is what makes a byte-for-byte comparison a valid regression
detector (see `CONTEXT.md` for the headless/determinism contract).

## Glossary — the five terms that trip people up

| Term | Plain meaning |
|---|---|
| **golden** | A committed recording of a deterministic run that later runs are compared against. Umbrella term for the whole scheme. |
| **oracle** | The byte-exact file `tests/golden/<name>.json` — the full per-frame recording (every fighter's position/velocity/state/percent/lives, every active hitbox). It's a large **opaque blob** and it fails on *any* difference, however tiny. It's the detector, not the thing you read. |
| **digest / summary sidecar** | The tiny companion file `tests/golden/<name>.summary.json` — a readable semantic summary of the *same* run (frame count, final phase, winner, attack-active frame count, and per-fighter states / lives start·end·min / max percent / KO frames). ~0.6 KB of pretty JSON that git-diffs cleanly. **This is the human-facing layer** — you read the digest diff, not the blob. |
| **re-baseline / regen / record mode** | Re-recording the goldens so the *current* behaviour becomes the new expected behaviour. Triggered by `PYCATS_UPDATE_GOLDENS=1` (usually via `make goldens`). It overwrites the files and passes **unconditionally** — so it will happily bless a regression if you don't review the diff (that's why the regen protocol exists). |
| **check vs record mode** | The two modes of `check_or_update`. **Check mode** (default) compares this run against the committed files and fails on a mismatch. **Record mode** (`PYCATS_UPDATE_GOLDENS=1`) overwrites the committed files and passes. |

## The two files per scenario

Each sim golden scenario saves **two** files under `tests/golden/`:

- `<name>.json` — the **oracle** (big, opaque, byte-exact).
- `<name>.summary.json` — the **digest** (tiny, readable).

When something changes, read the *summary* diff first (a few readable lines like
`percent_max 88.14 → 85.14, KO frame 601 → 600`). The blob is only there to catch what the
summary is too coarse to notice (a 1px position shift, say).

## The engine: `check_or_update`

Every golden test ends with one call — `check_or_update(name, snaps)` in
[`tests/golden_util.py`](../tests/golden_util.py). In **check mode** it:

1. Computes the summary of this run and asserts it equals the committed `<name>.summary.json`
   — so a behaviour change fails **first** with a small readable diff naming the field that moved.
2. Then asserts the full serialized run equals the committed `<name>.json`, reporting the
   **first differing frame** on a mismatch.
3. Tells you to record it if either committed file is missing.

In **record mode** (`PYCATS_UPDATE_GOLDENS=1`) it does not compare — it overwrites both files
and passes.

Two helpers back it: `serialize(snaps)` turns the per-frame snapshots into one deterministic
JSON string (the oracle content); `summarize(snaps)` distils the semantic digest, reading each
fighter row **by name** (`PlayerSnap(*row)`) so the snapshot tuple can grow new trailing fields
without breaking the summary.

## The scenarios (`tests/test_golden.py`)

| Scenario | What it exercises | Who plays |
|---|---|---|
| `default` | 200 frames of the scripted default timeline — general movement/idle. | Nalio vs Nalio |
| `combat` | A scripted combat script + 240-frame tail: jabs rack damage, then a fully-charged forward-smash lands a real side-blast KO — exercises `hurt` and `ko`. | Nalio vs Birky |
| `two_npc` | 600 frames with **both** fighters AI-driven (attacker vs follower) — locks the dual-controller path; seeded RNG for determinism. | AttackerController vs FollowerController |

Each also asserts a couple of inline non-vacuity guards (e.g. combat checks `hurt`/`ko` are
actually reached) so a golden can't quietly degrade into "nothing happened."

## The other two golden-bearing modules

- **`tests/test_golden_summary.py`** — unit tests for `summarize()` itself (frame counting,
  state dedupe, KO-frame + lives-arc detection, attack-frame counting). No committed file; it
  guards the digest logic the review protocol relies on.
- **`tests/test_screen_parity.py`** — a different kind of golden: it records the **screen-flow
  transition sequence** as `tests/golden/screen_parity.json`. This is a small FSM-trace blob,
  **not** a pixel/render test and **not** a per-frame sim snapshot, and it has **no** summary
  sidecar (review its diff directly). Naming trap: a render-only or default-flip change
  generally does *not* touch it; a change to the menu/screen graph does.

## Regenerating goldens (the short version)

When a code change legitimately moves the sim, re-record — but **reviewed, not rubber-stamped**:

```bash
make goldens                        # sets PYCATS_UPDATE_GOLDENS=1 for the 3 golden modules, then prints the review steps
git diff tests/golden/*.summary.json   # read the readable sidecar diffs, not the blob
```

For every changed summary field, confirm a specific code change in the *same* diff explains it.
Red flags (usually a laundered regression): a KO **disappearing**, `lives_end` rising,
`percent_max` dropping toward 0, or a state like `hurt`/`ko` no longer reached. There's also a
hard interlock (ADR-0003/#233): a regen justified by a combat **tuning constant** must update
that constant's `Provenance` row (`pycats/combat/provenance.py`) or
`tests/test_tuning_provenance.py` reds. The full checklist is
[`tests/golden/REGEN_PROTOCOL.md`](../tests/golden/REGEN_PROTOCOL.md).

## What a failure looks like

- **Behaviour change** → the summary assertion fires first with a small readable diff naming
  the field that moved. This is the fast, legible signal.
- **Sub-semantic change** (e.g. a 1px drift the summary doesn't track) → the raw `<name>.json`
  comparison fires with "first divergence at frame N" + a truncated dump.
- **Missing file** → "Golden file missing … run with PYCATS_UPDATE_GOLDENS=1 to record it."

> A red golden means the goldens *changed*, not that anything is *fixed* or *broken* on its own.
> Trace each changed field to an intended code change before you regen — "tests failed → regen →
> green" is exactly how a regression gets laundered into the baseline.
