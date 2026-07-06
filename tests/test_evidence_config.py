"""Validates the Grounded-Claim Protocol per-project config (.claude/evidence.json).

Guards two things: the config is well-formed, and every path it names actually
exists — so the `grounded-claim` skill never routes an agent at a missing
map/registry. Design: docs/superpowers/specs/2026-07-05-grounded-claim-protocol-design.md.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".claude" / "evidence.json"

REQUIRED_KEYS = {"canon", "evidence_map", "value_registry", "governed_domains"}


def _load():
    return json.loads(CONFIG.read_text())


def test_config_exists_and_is_json():
    assert CONFIG.is_file(), f"{CONFIG} missing"
    _load()  # raises JSONDecodeError if malformed


def test_config_has_required_keys():
    cfg = _load()
    assert REQUIRED_KEYS <= set(cfg), f"missing keys: {REQUIRED_KEYS - set(cfg)}"


def test_config_paths_resolve():
    cfg = _load()
    for key in ("evidence_map", "value_registry"):
        p = REPO_ROOT / cfg[key]
        assert p.is_file(), f"{key} -> {cfg[key]} does not exist"


def test_governed_domains_nonempty_list():
    cfg = _load()
    assert isinstance(cfg["governed_domains"], list) and cfg["governed_domains"]
