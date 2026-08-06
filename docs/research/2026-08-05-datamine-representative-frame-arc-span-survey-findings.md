# Representative-frame arc-span survey — findings (#1217)

**Ticket:** #1217 (`enhancement` · `area:combat` · child of #1206). **Date:** 2026-08-05. **Agent:** grape.

**Asked:** `propose()` (#1210) reduces a *moving* datamined hitbox to one static `Circle` via a
`strategy` — `FIRST_ACTIVE` / `MID_WINDOW` / `WINDOW_AVERAGE`
(`pycats.combat.datamine_proposer.RepresentativeFrame`), defaulting `FIRST_ACTIVE` **provisionally**.
Which rule best represents a moving box is an empirical, eyeball question. Before building the
comparison, this survey grounds **which moves actually discriminate the three strategies** (a box that
barely moves can't), so the comparison isn't overfit to a near-static box.

**Answer (short):** Discriminating moves are **smashes, aerials, and tilts** whose hitbox *sweeps
relative to the body*. **Specials are the worst discriminators** (near-fixed or linearly-tracking
boxes), and **high frame-count is not movement**. The comparison set chosen from the survey is **jab
(static baseline) + u-smash + fair + d-smash** — three distinct sweep *shapes*.

Data source: Mario's PM 3.6 `.pac` data via the brawllib `hitbox_dump` recipe
(`docs/tooling-brawllib-rs-datamine-recipe.md`); **nalio is the PM-Mario archetype**, so this is
nalio's moveset. Every number below is regenerable from the committed fixtures + the survey command
in the last section — no value is asserted from memory.

---

## The two metrics

These are defined here and filed for the glossary in **#1248**.

- **arc-span** — how far a hitbox travels **relative to the fighter's body** across the frames it is
  live. Concretely: take the box's centre on each active frame (pycats px, offset from the body via
  `units.u()`), and measure the diagonal of the smallest rectangle enclosing all those centres. It is
  **not** player/stage translation — brawllib renders subactions *in place*, so a move whose player
  slides far can have a near-zero arc-span, and a standing move can have a large one (see the
  dash-attack proof below).
- **representative-frame divergence** (short: **max-diverge**) — how far apart the three strategies'
  chosen circles land, in px: the larger of the FIRST_ACTIVE→MID_WINDOW and FIRST_ACTIVE→WINDOW_AVERAGE
  distances. Near-zero ⇒ the choice of strategy is immaterial for that box (nothing to eyeball); large
  ⇒ the box is a strong test of which rule best represents it.

### Box-local sweep ≠ player translation (the proof)

`dash-attack` (`AttackDash`) translates the *character* the most of any move (it is why #1153 saw its
reference GIF zoom out furthest), yet its hitbox `id1` is pinned at `dx=+0, dy=−12` for all 20 active
frames — **arc-span 0.0**. If the datamined position included stage-translation, dash-attack would top
the arc-span chart; it sits at the bottom. So the metric captures the box moving around the body, which
is exactly what `RepresentativeFrame` reduces.

---

## Ranked survey (25 subactions with hitboxes, 62 hitbox ids)

Top movers and the notable tails (full table regenerable — see last section):

| move | subaction · id | frames | arc-span px | max-diverge px | sweep shape |
|---|---|---|---|---|---|
| **u-smash** | AttackHi4 · 0 | 4 | **134.5** | 122.3 | up-and-over (front→overhead→fwd) |
| **d-smash** | AttackLw4 · 0 | 4 | **133.0** | 133.0 | bidirectional (front↔back) |
| u-air | AttackAirHi · 1 | 6 | 88.6 | 69.1 | overhead arc |
| u-smash | AttackHi4 · 1 | 4 | 88.2 | 81.0 | up arc |
| u-tilt | AttackHi3 · 2 | 7 | 77.9 | 73.0 | rising arc |
| d-smash | AttackLw4 · 1 | 4 | 74.0 | 74.0 | bidirectional |
| **fair** | AttackAirF · 1 | 7 | 68.8 | 47.0 | monotonic down-sweep |
| u-tilt | AttackHi3 · 1 | 7 | 47.1 | 43.1 | rising arc |
| up-B (super jump punch) | SpecialHi · 1 | 13 | 30.1 | **4.2** | near-linear rise |
| tornado | SpecialLw · 0 | 26 | 27.0 | **2.0** | near-fixed |
| cape | SpecialS · 0–2 | 3 | 0.0 | 0.0 | fixed |
| dash-attack | AttackDash · 1 | 20 | 0.0 | 0.0 | fixed (see proof above) |
| jab | Attack11 · 0 | 2 | 5.4 | 5.4 | ~static (baseline) |

### Findings

1. **Specials are the worst discriminators.** Mario's specials have near-fixed or linearly-tracking
   boxes: up-B moves 30px but diverges only 4px (it rises steadily, so the sampled representatives stay
   close); tornado ~0; cape 0. The ticket's illustrative "multi-frame special" would have been a poor
   choice — the strategies nearly coincide.
2. **High frame-count is not movement.** tornado (26 frames), nair (28), dair (21) have long active
   windows but tiny arc-spans — sustained/fixed boxes, not sweeps.
3. **The movers are smashes, aerials, and tilts** — arcs that carry the box around the body.
4. **Sweep *shape* matters as much as magnitude for the comparison.** A bidirectional sweep (d-smash)
   is where `WINDOW_AVERAGE` visibly fails: averaging a front-then-back sweep lands the single circle at
   the body centre (`dx≈+3`), a spot the hitbox never occupied. A monotonic sweep (fair) cleanly
   separates all three rules. An up-and-over arc (u-smash) is the largest sweep.

---

## Chosen comparison set

| move | subaction | role in the comparison |
|---|---|---|
| jab | Attack11 | static baseline — the three strategies ~coincide (control) |
| u-smash | AttackHi4 | largest sweep; up-and-over arc |
| fair | AttackAirF | monotonic down-sweep; cleanly separates the three rules |
| d-smash | AttackLw4 | bidirectional; the `WINDOW_AVERAGE`-failure case |

Selected with Avi (2026-08-05) for **shape diversity**, not just magnitude — so the eyeball pick isn't
overfit to one arc shape.

---

## Comparison tooling

`scripts/compare_representative_frames.py` renders, per move, a two-panel animated GIF:

```
[ reference GIF ] | [ FIRST_ACTIVE col | MID_WINDOW col | WINDOW_AVERAGE col ]
  brawllib render |   each: faint full box arc + that strategy's static circles
```

**Two panels, not one overlay (build decision, #1217):** the reference GIF is a per-subaction camera
render with no fixed world→px *position* scale (#120/#195/#1153), so compositing pycats-px circles onto
it would need a hand-tuned align. The three strategies all live in one pycats-px space, so the plot
panel is **exact** and needs no alignment — the approximation is avoided by not compositing the two
spaces. The GIF frame count equals the datamine frame count 1:1, so the plot highlights the box active
on the same frame the GIF is showing (both panels move together). Splitting the three strategies into
three columns (rather than three overlapping colours in one plot) is what makes it legible.

Dependencies: pygame-ce (declared runtime) draws the plot; imageio (declared dev dep) reads/writes the
GIFs. No new dependency. The tool is comparison tooling only — it never writes cat data. Its pure
geometry (that the plot equals `propose()` exactly) is covered by
`tests/test_compare_representative_frames.py` (able-to-fail).

---

## Status / next step

**Superseded approach (2026-08-05, #1217 close).** The reduce-a-moving-box-to-one-circle-then-compare-3
premise was set aside after Avi reviewed the four comparison artifacts: none of the three strategies
reads as "correctly representing all the frames" because any single circle is a lossy sample of a sweep.
The replacement direction verifies authored data against the datamine **directly** — an interactive
per-frame overlay of a cat's authored (windowed) hitbox circles vs the datamined per-frame boxes (ground
truth), so the check is "does the authored data cover every frame's box" rather than "which single-frame
reduction is least bad." That work is a **separate DEV ticket** (the datamine-vs-authored QA viewer,
child of #1206); this survey + tooling is **kept on the shelf** in case the representative-frame default
question returns.

`propose()`'s default therefore **stays `FIRST_ACTIVE` (provisional)** — it remains only an editor seed a
human tweaks (#782/#310); the QA viewer, not a pinned strategy, is how "correct" gets judged. The two
metrics coined here (**arc-span**, **max-diverge**) are filed for the glossary in **#1248**.

This doc records the survey + the (shelved) comparison tooling + the option space.

## Reproduce

```bash
# 1. datamine any Mario subaction's hitboxes (gated env — see the recipe)
scripts/datamine_hitboxes.sh Mario AttackHi4 tests/fixtures/datamine/mario_attackhi4_hitboxes.json

# 2. render its fixed-scale reference GIF (gated env; #1157)
#    cd ~/Documents/Study/Rust/brawllib_rs && . ~/.cargo/env
#    cargo run --release --example gif_generator_fixed -- -d <brawl> -m <pm36> \
#      -f Mario -a AttackHi4 -o <out_dir>

# 3. build the two-panel comparison (declared deps only)
python scripts/compare_representative_frames.py \
  --gif  repros/rep-frame-compare/gifs/output_Mario_AttackHi4.gif \
  --datamine tests/fixtures/datamine/mario_attackhi4_hitboxes.json \
  --move "u-smash (AttackHi4)" \
  --out  repros/rep-frame-compare/compare_AttackHi4.gif
```

The full 62-id ranked table is regenerable by running `propose()` + `_active_boxes` over every
`Mario Attack*/Special*` dump (the survey loop archived in this ticket's scratch).
