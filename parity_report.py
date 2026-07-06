# parity_report.py
"""Render the PM parity-light report (Axis C of #451) from the provenance registry.

The at-a-glance parity view — 🟢 / 🟡 / 🔴 — is a pure function of the
`pycats.combat.provenance` registry (Axis B, #233), never hand-typed in source
(the #448 "green rot" pre-mortem). Each `Provenance.status` maps to a circle:

    FOUND            -> 🟢  (PM-valid, checked)
    TUNED / GUESS    -> 🟡  (inferred / good-enough)
    DIVERGENCE       -> 🔴  (intentional departure)
    (unknown/absent) -> 🔴  (defensive; the registry's no-orphans guard makes this not occur)

Usage:
    python parity_report.py           # (re)write docs/parity-status.md
    python parity_report.py --check    # exit non-zero if the committed file is stale

The committed report + its up-to-date test (tests/test_parity_status_report.py,
which reuses check() below) are the "derived-from-B, no hand-stamping" guarantee.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pycats.combat import provenance

REPORT_PATH = Path(__file__).resolve().parent / "docs" / "parity-status.md"

# status -> circle. Unknown status is treated defensively as 🔴 (see module docstring).
_CIRCLE = {"FOUND": "🟢", "TUNED": "🟡", "GUESS": "🟡", "DIVERGENCE": "🔴"}

# Circle groups in render order, with their section headings.
_GROUPS = (
    ("🟢", "Sourced — FOUND (PM-valid, checked)"),
    ("🟡", "Inferred — TUNED / GUESS (good-enough / unsourced)"),
    ("🔴", "Divergence — intentional departure from canon"),
)


def _circle_for(status: str) -> str:
    return _CIRCLE.get(status, "🔴")


def _cell(text: str) -> str:
    # A literal pipe would break the markdown table cell.
    return text.replace("|", "\\|")


def render_report() -> str:
    """Build the full parity-status.md text — a pure function of the live registry.

    Rows are grouped by circle (🟢, then 🟡, then 🔴) and, within each group,
    sorted by constant name (alphabetical) so the report depends on registry
    *content*, not dict insertion *order*.
    """
    registry = provenance.TUNING_PROVENANCE
    counts = {"🟢": 0, "🟡": 0, "🔴": 0}
    for prov in registry.values():
        counts[_circle_for(prov.status)] += 1

    lines: list[str] = [
        "# PM parity status — Axis C parity light",
        "",
        "> **Generated file — do not hand-edit.** Regenerate with `python parity_report.py`",
        "> (drift-check: `python parity_report.py --check`). Circles are computed from the",
        "> `pycats/combat/provenance.py` registry (#233): 🟢 FOUND · 🟡 TUNED/GUESS · 🔴 DIVERGENCE.",
        "> Legend: [docs/parity-labeling-legend.md](parity-labeling-legend.md) (#452). Design: #448 (Pass C of #451).",
        "",
        f"**Summary:** {counts['🟢']} 🟢 / {counts['🟡']} 🟡 / {counts['🔴']} 🔴  ({len(registry)} constants)",
        "",
    ]

    for circle, heading in _GROUPS:
        group = sorted(
            ((name, prov) for name, prov in registry.items() if _circle_for(prov.status) == circle),
            key=lambda item: item[0],
        )
        lines.append(f"## {circle} {heading}")
        lines.append("")
        if not group:
            lines.append("_none_")
            lines.append("")
            continue
        lines.append("| Constant | Value | Status | ○ | Source |")
        lines.append("|---|---|---|---|---|")
        for name, prov in group:
            lines.append(f"| `{name}` | {_cell(str(prov.value))} | {prov.status} | {circle} | {_cell(prov.source)} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def check() -> bool:
    """True iff the committed report matches a fresh regen. Missing file -> False.

    This is the single compare path shared by `--check` and the up-to-date test.
    """
    if not REPORT_PATH.exists():
        return False
    return REPORT_PATH.read_text(encoding="utf-8") == render_report()


def write_report() -> None:
    REPORT_PATH.write_text(render_report(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render/verify the PM parity-light report from the provenance registry."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in-memory and exit non-zero if the committed docs/parity-status.md differs",
    )
    args = parser.parse_args(argv)

    if args.check:
        if check():
            print("parity-status.md is up to date.")
            return 0
        print(
            "parity-status.md is STALE — run `python parity_report.py` to regenerate.",
            file=sys.stderr,
        )
        return 1

    write_report()
    print(f"wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
