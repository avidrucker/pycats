"""Up-to-date + able-to-fail guard for the generated docs/parity-status.md (#607).

parity_report.py renders the parity-light report (Axis C of #451) as a pure
function of the pycats/combat/provenance.py registry (Axis B, #233). This test is
the "derived-from-B, no hand-stamping" guarantee:

  - the committed report matches a fresh regen (up-to-date), via the SAME compare
    path `parity_report --check` uses (parity_report.check());
  - it is able-to-fail — flipping a registry status makes the committed report no
    longer match (the revert-check);
  - the report is a pure function of registry *content*, not dict *ordering*.
"""

from dataclasses import replace

import parity_report
from pycats.combat import provenance


def test_committed_report_is_up_to_date():
    # Same compare path as `python parity_report.py --check`.
    assert parity_report.check(), "docs/parity-status.md is stale — regenerate with `python parity_report.py`"


def test_one_row_per_registry_entry():
    text = parity_report.render_report()
    for name in provenance.TUNING_PROVENANCE:
        assert f"| `{name}` |" in text, f"{name} missing a row in the report"
    # No extra constant rows beyond the registry.
    row_count = text.count("| `")
    assert row_count == len(provenance.TUNING_PROVENANCE)


def _rows_by_section(text):
    """Return {circle: [constant names in table order]} parsed from the report."""
    sections, current = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line.split()[1]  # the circle glyph
            sections[current] = []
        elif current and line.startswith("| `"):
            sections[current].append(line.split("`")[1])
    return sections


def test_rows_sorted_by_name_within_each_group():
    sections = _rows_by_section(parity_report.render_report())
    for circle, names in sections.items():
        assert names == sorted(names), f"{circle} group not alphabetically sorted: {names}"


def test_report_is_stable_under_registry_reorder(monkeypatch):
    baseline = parity_report.render_report()
    # Same content, reversed insertion order — a pure ordering change.
    reordered = dict(reversed(list(provenance.TUNING_PROVENANCE.items())))
    monkeypatch.setattr(provenance, "TUNING_PROVENANCE", reordered)
    assert parity_report.render_report() == baseline, "report changed under a content-preserving reorder"


def test_able_to_fail_on_status_flip(monkeypatch):
    # Precondition: the committed report is currently up to date.
    assert parity_report.check()
    # Flip one FOUND row to TUNED (🟢 -> 🟡): the committed report must no longer match.
    registry = dict(provenance.TUNING_PROVENANCE)
    assert registry["GRAVITY"].status == "FOUND"
    registry["GRAVITY"] = replace(registry["GRAVITY"], status="TUNED")
    monkeypatch.setattr(provenance, "TUNING_PROVENANCE", registry)
    assert not parity_report.check(), "check() should red when a registry status changes (report not able-to-fail)"
