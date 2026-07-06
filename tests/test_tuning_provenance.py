"""ADR-0003 drift-guard (#233): the tuning-provenance registry stays in lock-step
with the live constants in `pycats.config`.

Three able-to-fail assertions:
  1. no drift        — every registry value equals the live config constant;
  2. no orphans      — the registry keyset equals the curated TUNING_CONSTANT_NAMES;
  3. derivation integrity — every `derivation` re-evaluates to its recorded value.

Each can fail: flip a `Provenance.value` (1), add/remove a name without its row (2),
or rot a `derivation` (3), and the corresponding test reds.
"""
from pathlib import Path

from pycats import config
from pycats.combat.provenance import (
    TUNING_CONSTANT_NAMES,
    TUNING_PROVENANCE,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "docs" / "project-m-rules-by-category.md"
STATUS_TOKENS = ("FOUND", "GUESS", "TUNED", "DIVERGENCE")


def _config_namespace() -> dict[str, object]:
    """The public UPPER_SNAKE constants of config, for re-evaluating derivations
    (e.g. `round(3.1 * PX_PER_UNIT)` needs PX_PER_UNIT)."""
    return {name: getattr(config, name) for name in dir(config) if name.isupper()}


def test_no_drift_registry_value_matches_config():
    mismatches = []
    for name, prov in TUNING_PROVENANCE.items():
        live = getattr(config, name)
        if live != prov.value:
            mismatches.append(f"{name}: config={live!r} != provenance={prov.value!r}")
    assert mismatches == [], (
        "tuning constants drifted from their provenance rows (edit the constant AND "
        "its Provenance.value + status/issue in the same diff — ADR-0003):\n  "
        + "\n  ".join(mismatches)
    )


def test_no_orphans_registry_keyset_matches_curated_names():
    missing_row = TUNING_CONSTANT_NAMES - set(TUNING_PROVENANCE)
    missing_name = set(TUNING_PROVENANCE) - TUNING_CONSTANT_NAMES
    assert not missing_row and not missing_name, (
        "TUNING_CONSTANT_NAMES and the registry keyset disagree — every curated "
        "tuning constant needs exactly one Provenance row:\n"
        f"  curated names with no registry row: {sorted(missing_row)}\n"
        f"  registry rows not in curated names: {sorted(missing_name)}"
    )


def test_every_curated_constant_exists_in_config():
    absent = [name for name in TUNING_CONSTANT_NAMES if not hasattr(config, name)]
    assert absent == [], f"curated tuning names absent from config: {sorted(absent)}"


def test_derivation_integrity_reevaluates_to_value():
    ns = _config_namespace()
    bad = []
    for name, prov in TUNING_PROVENANCE.items():
        if prov.derivation is None:
            continue
        got = eval(prov.derivation, {"__builtins__": {"round": round}}, ns)  # noqa: S307
        if got != prov.value:
            bad.append(f"{name}: derivation {prov.derivation!r} -> {got!r} != {prov.value!r}")
    assert bad == [], (
        "a recorded derivation no longer yields its value (a derivation rotted):\n  "
        + "\n  ".join(bad)
    )


# --- #575 Tier-1: registry <-> by-category manifest status consistency (#635) ---
# The detective gate: a value the registry tags TUNED/DIVERGENCE/GUESS must not be
# described with a different status in the by-category manifest. Joined by the bare
# constant name in the manifest's `Constant` column (blank for compound/mechanic rows).


def _parse_manifest_table() -> tuple[list[str], list[dict[str, str]]]:
    """Parse the first markdown table of the by-category manifest into
    (header, rows) where each row is a dict keyed by column header."""
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in MANIFEST.read_text().splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row (|---|---|)
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    return (header or []), rows


def _leading_status(status_cell: str) -> str | None:
    """The status token a manifest Status cell starts with (e.g.
    'DIVERGENCE → aligning (#543)' -> 'DIVERGENCE')."""
    for tok in STATUS_TOKENS:
        if status_cell.startswith(tok):
            return tok
    return None


def test_manifest_has_constant_column():
    header, _ = _parse_manifest_table()
    assert "Constant" in header, (
        "the by-category manifest needs a `Constant` column so its rows can be "
        "joined to the provenance registry for the consistency gate (#635)"
    )


def test_manifest_status_matches_registry():
    _, rows = _parse_manifest_table()
    keyed = [r for r in rows if r.get("Constant", "").strip()]
    assert keyed, (
        "no manifest row names a Constant — the registry<->manifest gate would be "
        "vacuous; keep at least one 1:1 row keyed (#635)"
    )
    problems = []
    for r in keyed:
        key = r["Constant"].strip().strip("`").strip()
        if key not in TUNING_PROVENANCE:
            problems.append(f"{key}: Constant not in provenance registry")
            continue
        want = TUNING_PROVENANCE[key].status
        got = _leading_status(r["Status"])
        if got != want:
            problems.append(
                f"{key}: manifest Status {r['Status']!r} (-> {got}) != registry {want!r}"
            )
    assert problems == [], (
        "by-category manifest disagrees with the provenance registry — reconcile the "
        "Status columns (registry is the value source of truth; ADR-0003):\n  "
        + "\n  ".join(problems)
    )


# --- #643: status accessors + traceability guard (divergences view, #575 Q4) ---


def test_by_status_and_named_views():
    from pycats.combat.provenance import by_status, debt, divergences

    assert set(by_status("GUESS")) == {
        n for n, p in TUNING_PROVENANCE.items() if p.status == "GUESS"
    }
    assert set(by_status("DIVERGENCE", "GUESS")) == {
        n for n, p in TUNING_PROVENANCE.items() if p.status in ("DIVERGENCE", "GUESS")
    }
    # named views mean distinct things: departures vs unsourced debt
    assert divergences() == by_status("DIVERGENCE")
    assert debt() == by_status("GUESS")
    # TUNED is a settled design choice — never surfaced as a divergence or as debt
    assert all(p.status == "DIVERGENCE" for p in divergences().values())
    assert all(p.status == "GUESS" for p in debt().values())


def test_divergence_and_guess_carry_issue():
    untraceable = sorted(
        name
        for name, prov in TUNING_PROVENANCE.items()
        if prov.status in ("DIVERGENCE", "GUESS") and prov.issue is None
    )
    assert untraceable == [], (
        "every DIVERGENCE/GUESS constant must carry a tracking `issue` so the "
        f"departure/debt is traceable (backfill the issue field): {untraceable}"
    )
