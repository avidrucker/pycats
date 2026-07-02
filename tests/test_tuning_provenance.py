"""ADR-0003 drift-guard (#233): the tuning-provenance registry stays in lock-step
with the live constants in `pycats.config`.

Three able-to-fail assertions:
  1. no drift        — every registry value equals the live config constant;
  2. no orphans      — the registry keyset equals the curated TUNING_CONSTANT_NAMES;
  3. derivation integrity — every `derivation` re-evaluates to its recorded value.

Each can fail: flip a `Provenance.value` (1), add/remove a name without its row (2),
or rot a `derivation` (3), and the corresponding test reds.
"""
from pycats import config
from pycats.combat.provenance import (
    TUNING_CONSTANT_NAMES,
    TUNING_PROVENANCE,
)


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
