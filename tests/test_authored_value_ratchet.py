"""Authored-value ratchet (#1151): authored + undeclared may only fall.

For every area, this reds when either the AUTHORED bucket (GUESS + PLACEHOLDER) or
the UNDECLARED bucket grows above ``tests/authored_value_baseline.json`` — the two
buckets are gated **independently** (design §6 Q3, ratified in #1125:
``docs/research/authored-value-ratchet-findings.md``). ``sourced`` and ``decided``
are reported by the census but never gated. A drop is progress and passes.

A deliberate rise is recorded by re-blessing the baseline:
``PYCATS_UPDATE_AUTHORED_BASELINE=1`` regenerates the file — a reviewable one-file
diff under author ≠ reviewer, mirroring ``PYCATS_UPDATE_GOLDENS`` (``make goldens``).

Able-to-fail (revert-check): add a ``GUESS``/``PLACEHOLDER`` status entry to any
fighter's status map (or a new ``GUESS`` scalar to ``provenance.py``) → the authored
count rises above baseline → this reds. A status token is metadata the sim ignores,
so the demonstration moves no golden.
"""

from __future__ import annotations

import json
import os
from dataclasses import fields
from pathlib import Path

from pycats.combat import value_status_census as vsc

BASELINE_PATH = Path(__file__).parent / "authored_value_baseline.json"

_REBLESS = os.environ.get("PYCATS_UPDATE_AUTHORED_BASELINE") == "1"

_COMMENT = (
    "Authored-value ratchet baseline (#1151). Per-area gated counts: `guess` + "
    "`placeholder` = the authored bucket, and `undeclared` = authored value-slots "
    "with no status entry. The ratchet (tests/test_authored_value_ratchet.py) reds "
    "when either the authored sum or undeclared grows above these. Regenerate with "
    "PYCATS_UPDATE_AUTHORED_BASELINE=1 (author != reviewer); a bump is a reviewable "
    "one-file diff. sourced/decided are NOT gated and are not stored here."
)


def _current_components() -> dict[str, dict]:
    """The gated per-area components of the live census (TOTAL excluded — derived)."""
    data = vsc.census()
    return {
        area: {
            "guess": b["authored"]["guess"],
            "placeholder": b["authored"]["placeholder"],
            "undeclared": b["undeclared"],
        }
        for area, b in data.items()
        if area != "TOTAL"
    }


def _write_baseline(components: dict[str, dict]) -> None:
    doc = {"_comment": _COMMENT, "areas": components}
    BASELINE_PATH.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_field_partition_covers_every_field() -> None:
    """Every field of each status-carrying dataclass is classified value / non-value.

    Drift guard: adding a field to Circle/Hitbox/MoveData/VelocityPhase/LandingSpawn
    without deciding whether it is an authored value slot reds here — so the
    undeclared denominator cannot silently drift as the schema grows.
    """
    for cls in vsc.STATUS_CARRIERS:
        all_names = {f.name for f in fields(cls)}
        value = vsc.VALUE_FIELDS[cls]
        non_value = vsc.NON_VALUE_FIELDS[cls]
        missing = all_names - (value | non_value)
        unknown = (value | non_value) - all_names
        assert not missing, (
            f"{cls.__name__}: unclassified field(s) {sorted(missing)} — add to VALUE_FIELDS or NON_VALUE_FIELDS"
        )
        assert not unknown, f"{cls.__name__}: classified name(s) {sorted(unknown)} are not real fields"
        assert not (value & non_value), (
            f"{cls.__name__}: field(s) {sorted(value & non_value)} in BOTH value and non-value"
        )


def test_authored_value_ratchet() -> None:
    """authored (GUESS+PLACEHOLDER) and undeclared may only fall, per area."""
    components = _current_components()

    if _REBLESS:
        _write_baseline(components)
        return

    assert BASELINE_PATH.exists(), (
        f"baseline missing: {BASELINE_PATH}\nRun with PYCATS_UPDATE_AUTHORED_BASELINE=1 to record it."
    )
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["areas"]

    problems: list[str] = []
    for area, cur in components.items():
        cur_authored = cur["guess"] + cur["placeholder"]
        base = baseline.get(area)
        if base is None:
            # A newly-added area (e.g. a new cat's JSON) carrying authored/undeclared
            # debt is growth — re-bless to acknowledge it.
            if cur_authored or cur["undeclared"]:
                problems.append(
                    f"{area}: NEW area — authored={cur_authored}, undeclared={cur['undeclared']} (re-bless to record)"
                )
            continue
        base_authored = base["guess"] + base["placeholder"]
        if cur_authored > base_authored:
            problems.append(f"{area}: authored {base_authored} → {cur_authored} (+{cur_authored - base_authored})")
        cur_undeclared, base_undeclared = cur["undeclared"], base["undeclared"]
        if cur_undeclared > base_undeclared:
            problems.append(
                f"{area}: undeclared {base_undeclared} → {cur_undeclared} (+{cur_undeclared - base_undeclared})"
            )

    assert not problems, (
        "authored/undeclared value count grew above the baseline.\n"
        "If intended, re-bless: PYCATS_UPDATE_AUTHORED_BASELINE=1 (author != reviewer).\n"
        + "\n".join(problems)
        + "\n\n"
        + vsc.format_table(vsc.census())
    )
