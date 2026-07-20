"""Validates the verify-claims per-project config (.claude/ledger.json).

Guards that the config is well-formed and carries the pycats-ratified shape, so the
`verify-claims` skill mints IDs and resolves the ledger consistently. The ledger DATA
(`claims-data/`) is gitignored and absent in CI, so this asserts config SHAPE only —
never that the ledger directory exists. Skill: avidrucker/claude-config verify-claims
(config home #19). Ratified in the 2026-07-15 grill; migrated to the 7-key schema
(topics/testDir in, evidenceDir out) in #757.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".claude" / "ledger.json"

# The verify-claims 7-key schema (evidenceDir was retired, topics + testDir added
# in the migration, #757). agentScoped is nullable/optional, so it stays out of the
# required set.
REQUIRED_KEYS = {"enabled", "dir", "prefix", "topics", "testDir", "overloadedTerms"}


def _load():
    return json.loads(CONFIG.read_text())


def test_config_exists_and_is_json():
    assert CONFIG.is_file(), f"{CONFIG} missing"
    _load()  # raises JSONDecodeError if malformed


def test_config_has_required_keys():
    cfg = _load()
    assert REQUIRED_KEYS <= set(cfg), f"missing keys: {REQUIRED_KEYS - set(cfg)}"


def test_prefix_is_the_pycats_tag():
    # PYC = first three letters of "pycats", uppercased (the ratified project tag).
    assert _load()["prefix"] == "PYC"


def test_dir_is_claims_data():
    assert _load()["dir"] == "claims-data"


def test_enabled_is_true():
    assert _load()["enabled"] is True


def test_overloaded_terms_is_nonempty_list():
    terms = _load()["overloadedTerms"]
    assert isinstance(terms, list) and terms


def test_evidence_dir_key_is_retired():
    # `evidenceDir` was the old frozen-evidence-dir model; the 7-key migration
    # (#757) removed it. Guard against a regression that re-adds it.
    assert "evidenceDir" not in _load()
