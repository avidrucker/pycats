# Decision Log

> Append-only ledger of ratified **game-design `decision:` tickets** — the chronological
> history [ADR-0001](adr/0001-record-architecture-decisions.md) recommended (via #56) but
> never built. **Newest-last.** See [ADR-0007](adr/0007-decision-ledger.md) for why this
> exists.
>
> **What belongs here:** a ratified `decision:` ticket — a game-design ruling the human
> designer made (a tuning direction, a surrogate-value pick, a divergence choice). This is
> the *index*; the full record lives wherever the `Record` column points.
>
> **What does NOT belong here:** architecture decisions (those are full-prose **ADRs** in
> [`docs/adr/`](adr/)) and per-value tuning provenance (those are `FOUND`/`TUNED` entries in
> [`pycats/combat/provenance.py`](../pycats/combat/provenance.py), ADR-0003). This ledger
> **complements** both.
>
> **Append-only rule:** never edit a row to reverse a decision; a reversal is a **new row**
> citing the superseded issue (mirrors ADR-0001's supersede rule). Append the row **in the
> same change that closes** the `decision:` ticket (RULES → *Closing work*).

| Date | Decision (issue #) | Area | Ruling | Record |
|---|---|---|---|---|
| 2026-07-07 | [#705](https://github.com/avidrucker/pycats/issues/705) | area:tracker | Establish this append-only Decision Log ledger (+ ADR-0007 + RULES wiring) | [ADR-0007](adr/0007-decision-ledger.md) |
| 2026-07-07 | [#704](https://github.com/avidrucker/pycats/issues/704) | area:combat | Approve near-miss + accidental-press + per-character CPU tuning as pycats-custom difficulty flavor (not PM parity) | [#704 ruling](https://github.com/avidrucker/pycats/issues/704#issuecomment-4910662301); `provenance.py` `TUNED` as each DEV lands (#702 follow-ups) |
| 2026-08-02 | [#1098](https://github.com/avidrucker/pycats/issues/1098) | area:combat | ROUNDS v1 format params: **point-tier above stocks** (stock = a within-point life, base 1/point, card-modifiable — a +stock card can't leak into match score); a point ends when a player loses **all** their stocks; **first-to-5** points (configurable, [#1131](https://github.com/avidrucker/pycats/issues/1131)); **loser-only** draft + both draft a starting card; **no card cap** in V1 (canonical cap 5 + loss condition deferred post-V1, [#1132](https://github.com/avidrucker/pycats/issues/1132)) | [#1098 ruling](https://github.com/avidrucker/pycats/issues/1098#issuecomment-5163402392) |
| 2026-08-03 | [#1101](https://github.com/avidrucker/pycats/issues/1101) | area:combat | ROUNDS v1 starter card set: **9 buildable cards** covering every live ADR-0013 seam — Phoenix (+stock) · Chase (+speed) · Springs (+jump) · Compact (−body) · Glass Cannon (+dmg/−weight) · Metal (+weight/−speed) · Bruiser (+KBG/−dmg) · Long Arms (+reach) · Floaty (−gravity); a natural mix of pure-upside + trade cards, **magnitudes by-feel** (no taming gate, [#1156](https://github.com/avidrucker/pycats/issues/1156)). **All families in V1**; two machinery-heavy families **slotted with shapes as riders**: Leech (%-per-second, gated on RESEARCH [#1111](https://github.com/avidrucker/pycats/issues/1111)) + Empower (on-block, gated on a new shield-event hook) | [#1101 ruling](https://github.com/avidrucker/pycats/issues/1101#issuecomment-5170067842) |
| 2026-08-07 | [#1297](https://github.com/avidrucker/pycats/issues/1297) | area:cross-cutting | `--dev` mode V1 shape: one `runtime_settings.dev_mode` via **3 doors** (env `PYCATS_DEV=1` / `--dev` arg / in-game **F1** debug screen); **backtick**=in-battle dev-HUD toggle (shipping-available), **F1**=debug screen; **minimal default HUD** (Lives+Damage%+label), rest → dev HUD; Pause unchanged, granular toggles move Options→F1. **V1:** dev-gate, HUD redesign, hitbox/hurtbox overlay dev-gated + removed from Options, overlay per-side split, seed display/set, `PYCATS_DEV_LOG` default-on, last-hit dmg/KB, instant-respawn (cheat), testcat/default ([#1292](https://github.com/avidrucker/pycats/issues/1292)). **post-V1:** velocity+timers, frame-step, live-speed, event-console. **scrap:** god-mode, spawn-tweaks. **spike:** free camera | [design doc](design/dev-mode-v1-rulings.md); [#1297 ruling](https://github.com/avidrucker/pycats/issues/1297#issuecomment-5223077513) |
| 2026-08-07 | [#1308](https://github.com/avidrucker/pycats/issues/1308) | area:display | Ratify a **throwaway camera-prototype experiment** to de-risk the fixed-vs-moving camera call (#1304 Q1): **human plays it live** for a **binary go/no-go** (no video); build **follow + zoom** (box · flat margin · zoom-to-fit + clamps · pan · lerp · on/off toggle), cut the per-count weight table + magnifying-glass bubble; **sourced world-bound hack** (~848/745/486 px, does not touch #789); scenarios neutral/launch/spread; **branch never merged unless the feel is approved**, then merged via a **productionization pass** (production KO decouple + goldens); **30-min hard cap**. Runs under [#1315](https://github.com/avidrucker/pycats/issues/1315) | [design doc](design/camera-prototype-experiment-spec.md) |
