"""Drift-guard for the mechanics router `docs/mechanics-index.md` (#737, Wave 2 of #724).

The router indexes every pycats-invented / PM-divergent mechanic (promoted from the #605
inventory) with a *structured* landmark column — `pkg/mod.py::Symbol` refs — plus an owner
column. This guard keeps the router from silently rotting, the way
`tests/test_tuning_provenance.py` keeps the value layer honest. Three able-to-fail checks:

  (a) resolution   — every `pkg/mod.py::Symbol` in the router is defined at module scope
                     (AST, no import); a rename/move/delete reds it.
  (b) completeness — no divergence silently drops out of the index:
                       - value rows: every DIVERGENCE/TUNED constant in the provenance
                         registry appears as a `pycats/config.py::NAME` landmark
                         (machine-anchored to provenance.py — drift-proof);
                       - architectural rows: every curated #605 mechanic anchor (§X.Y) has
                         a row.
  (c) owner/doc    — every backticked file path (.md/.py/.json) in the router names a file
                     that exists on disk.

Each can fail independently: rename a referenced symbol (a); add a TUNED constant to
provenance without a router row, or delete a router row (b); point a path at a missing
file (c). The guard is static (AST + regex over the doc) — it never imports pycats.
"""

import ast
import re
from pathlib import Path

from pycats.combat.provenance import TUNING_PROVENANCE

REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTER = REPO_ROOT / "docs" / "mechanics-index.md"

# `pkg/mod.py::Symbol` landmark refs (structured landmark column).
_LANDMARK = re.compile(r"`([A-Za-z0-9_./]+\.py)::([A-Za-z_][A-Za-z0-9_]*)`")
# backticked file paths WITHOUT `::` — owner/doc columns and refs.
_FILEPATH = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:md|py|json))`")
# #605 section anchors present as router rows.
_ANCHOR = re.compile(r"§(\d+\.\d+)")

# The architectural mechanics the router must index — the ### entries of
# docs/research/2026-07-07-custom-mechanics-inventory.md (§§1,3,4,5,6; §2 is the value
# layer, guarded separately below). Curated on purpose: deleting a router row without
# editing this set reds (b), the same no-orphans discipline as TUNING_CONSTANT_NAMES.
EXPECTED_ARCH_ANCHORS = {
    "1.1",
    "1.2",
    "1.3",
    "1.4",  # render / status feedback
    "3.1",
    "3.2",
    "3.3",  # input / move selection
    "4.1",  # physics / state routing
    "5.1",
    "5.2",
    "5.3",  # tests / oracles
    "6.1",  # tooling
}

# Symbols the AST legitimately can't resolve at module scope, each with a reason.
# Empty by construction today — every indexed landmark is a real module-scope def / class /
# assignment. Add `("pkg/mod.py", "Symbol"): "reason"` ONLY with a written justification;
# an allowlist entry is a documented exception, never a silent skip.
ALLOWLIST: dict[tuple[str, str], str] = {}


def _router_text() -> str:
    assert ROUTER.exists(), f"router doc missing: {ROUTER.relative_to(REPO_ROOT)} — #737 ships it alongside this guard"
    return ROUTER.read_text()


def _module_scope_names(path: Path) -> set[str]:
    """Names bound at module scope: def / async def / class / assignment targets."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_a_landmarks_resolve_at_module_scope():
    unresolved = []
    for module, symbol in _LANDMARK.findall(_router_text()):
        if (module, symbol) in ALLOWLIST:
            continue
        modpath = REPO_ROOT / module
        if not modpath.exists():
            unresolved.append(f"{module}::{symbol} — module file not found")
        elif symbol not in _module_scope_names(modpath):
            unresolved.append(f"{module}::{symbol} — symbol not defined at module scope")
    assert unresolved == [], (
        "router landmark(s) no longer resolve — a rename/move/delete drifted the pointer; "
        "fix the router row or add a justified ALLOWLIST entry:\n  " + "\n  ".join(unresolved)
    )


def test_b_value_divergences_are_all_indexed():
    text = _router_text()
    registered = {name for name, prov in TUNING_PROVENANCE.items() if prov.status in ("DIVERGENCE", "TUNED")}
    indexed = {sym for mod, sym in _LANDMARK.findall(text) if mod == "pycats/config.py"}
    missing = registered - indexed
    orphan = indexed - registered
    assert not missing, (
        "value divergence(s) registered DIVERGENCE/TUNED in provenance.py but missing a "
        f"router row (add one): {sorted(missing)}"
    )
    assert not orphan, (
        "router lists config constant(s) that aren't DIVERGENCE/TUNED in provenance.py "
        f"(remove or reclassify the row): {sorted(orphan)}"
    )


def test_b_architectural_mechanics_are_all_indexed():
    present = set(_ANCHOR.findall(_router_text()))
    missing = EXPECTED_ARCH_ANCHORS - present
    assert not missing, (
        "architectural mechanic(s) from the #605 inventory dropped out of the router "
        f"(restore the row for anchor §): {sorted(missing)}"
    )


def test_c_owner_and_doc_paths_exist():
    missing = [rel for rel in sorted(set(_FILEPATH.findall(_router_text()))) if not (REPO_ROOT / rel).exists()]
    assert missing == [], f"router references file path(s) that don't exist (moved/deleted — fix): {missing}"
