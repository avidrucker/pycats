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

## Coverage — what the goldens lock, and what they don't

The golden suite locks a **narrow slice** of behaviour on purpose (more goldens = more
regen/review surface). This section makes that slice — and its gaps — visible at a glance, so a
gap becomes a *candidate* future golden rather than an invisible blind spot. Adding a golden for
any gap below is a separate decision (file its own ticket); this is an inventory, not a to-do.

Read the golden-vs-unit-test column as the D2 ruling generalised (#1008): a golden is the right
tool for an **emergent multi-frame trajectory** (the sim drifting over hundreds of frames); a
focused **unit test** is the right tool for a mechanic you can assert in isolation. Most gaps
below are already served by a unit test — they are gaps *in the golden suite*, not in coverage.

### What each golden scenario actually locks (from the committed digests)

| Scenario | Fighters | Locks | Notably absent |
|---|---|---|---|
| `default` | nalio vs nalio | 200f of ground/air movement (`idle/walk/jump/fall`), a few attack-active frames, `shield`; no damage, no KO, ends `in_play`. | any damage/hurt/ko; specials; defensive rolls/dodges. |
| `combat` | nalio vs birky | The full damage arc: nalio `smash_charge → attack`, birky `hurt → ko` (KO at frame 600, `percent_max` ≈ 85), **one** stock lost. | match completion (still ends `in_play`, `winner 0`); specials; grabs. |
| `two_npc` | testcat vs testcat (AI) | The dual-controller path + emergent movement; incidentally reaches `ledge_hang` and a small `hurt` (10%). | a **playable-cat** guarantee — `testcat` is a scaffold, not an archetype. |
| `test_golden_summary` | — (synthetic) | `summarize()` logic itself (no committed file). | nothing sim-level; it guards the digest, not behaviour. |
| `screen_parity` | — (screen FSM) | The screen-flow transition sequence over `main_menu/options/char_select/playing/pause/win_screen`. | anything sim/render — it's an FSM trace, no sidecar. |

Union of fighter states any golden locks: `idle, walk, jump, fall, attack, shield, smash_charge,
hurt, ko, crouch, ledge_hang`.

### Character gaps

| Gap | Golden or unit test? |
|---|---|
| **`narz` and `gnok`** — implemented, selectable archetypes (`ARCHETYPE_ROSTER` in `pycats/characters/roster.py`) with **no golden at all**. | Golden candidate: a per-cat combat/movement scenario would lock each one's emergent arc. Lower urgency while movesets are still settling. |
| **Archetype-specific movesets** — each cat's specials/tilts/smashes beyond nalio's fsmash (in `combat`) go unexercised by any golden. | Mixed: per-move hitbox shape is already unit-tested (`test_multi_hitbox.py`, `test_move_rect_symmetry.py`); a golden only earns its keep for the *multi-frame* result (a specific move's KO/launch arc). |
| **`testcat` ≠ a real cat** — `two_npc` locks controller behaviour on the scaffold fighter, not a shipping archetype. | Not a character-coverage guarantee; if a playable-cat AI arc matters, that's a new golden with real archetypes. |

### Mechanic gaps (no golden locks these today)

| Mechanic | In the sim? | Golden or unit test? |
|---|---|---|
| **Specials** (neutral/side/up/down B) — the `special` state never appears in any digest. | Yes (`move_select.py`, `provenance.py`). | Unit tests exist (`test_up_b_recovery.py`, `test_projectile.py`); a golden fits only for a full recovery/special *trajectory*. |
| **Ledge & recovery** beyond a single `ledge_hang`: no `ledge_grab → ledge_getup`, no offstage recovery arc, no `ledge_intangible`/regrab-lockout, no `grabbed_ledge`. | Yes (`tangibility.py`; the `ledge_*` states). | Well covered by unit tests (`test_ledge_hang.py`, `test_ledge_regrab_cutoff.py`, `test_up_b_recovery.py`, `test_ai_recovery.py`); a recovery-arc golden would be the strongest single addition. |
| **Grab / throw** — grab tangibility exists but no golden runs a grab→throw. | Yes (`tangibility.py`). | Unit test first (`test_grabs_left_dots.py`); golden only if a throw's launch arc needs locking. |
| **Dash / run / dash-dance** — `dash`/`run` states never in a digest. | Yes (`dash_*` states). | Unit tests already own it (`test_dash.py`, `test_double_tap_dash.py`, `test_wavedash.py`) — not a golden need. |
| **Defensive options** (roll, spot-dodge, air-dodge) — `dodge` states never in a digest. | Yes. | Unit tests own it (`test_dodge_mechanics.py`, `test_spot_dodge_input_order.py`, `test_air_dodge_*`); a golden adds little. |
| **Multi-hit, clank, projectile resolution** — referenced in `combat/data.py`/`move_clock.py` but no golden locks the resolved outcome. | Yes. | Unit tests exist (`test_multi_hitbox.py`, `test_clank.py`, `test_projectile.py`); golden only for an emergent interaction across frames. |
| **Match completion** — all three sim goldens end `in_play` with `winner 0` (combat loses just one of birky's stocks); no golden reaches `match_over`/a decided `winner`. | Yes. | Golden candidate: a short scenario that KOs all stocks would lock the end-of-match phase/winner transition — currently untested at the sim-golden level. |

### State-combination gaps

No golden exercises: `shield → shieldstun → shield-break`; hitlag/hitstun interplay through a
`clank`; or an intangibility window (`air_dodge`/`roll`/ledge) actually **negating** an incoming
hit. Each is a focused-unit-test shape (assert the specific interaction), not a golden — a golden
would only lock them incidentally inside a larger scripted fight.

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
