"""Drift-guard: README's dev-command list stays in sync with the `Makefile` (#896).

#892 hand-synced README's "For contributors" command list to `make help`, but nothing
kept them from drifting apart again — the next `Makefile` target (exactly as #859 added
`run-cmd`) would pass every test while going undocumented in README, which is how
`run-cmd` and `goldens` ended up in `make help` but missing from README. This guard makes
that drift red, the same no-orphans discipline `tests/test_tuning_provenance.py` and
`tests/test_doc_landmarks.py` (#737) apply to the value layer and the mechanics router.

Two able-to-fail checks over the target *names* (presence, not prose quality):

  (a) completeness — every real `Makefile` target (its `.PHONY:` line, the SSOT) appears
                     as a `make <target>` reference in README. Adding a `.PHONY` target
                     without a README mention, or deleting the mention, reds this.
  (b) no-phantoms  — every `make <target>` README documents is a real `.PHONY` target.
                     Documenting a `make foo` the Makefile never defines reds this.

`help` is NOT special-cased: it is a real `.PHONY` target and README references `make help`
as the "authoritative one-line list" SSOT pointer, so it satisfies (a) exactly like every
other target — the intentional rule is "all `.PHONY` targets, help included, must appear."

The guard is static (regex over `Makefile` + `README.md`) — it never runs `make` or imports
pycats, so it stays fast and driver-free.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
README = REPO_ROOT / "README.md"

# The `.PHONY:` line is the Makefile's own declaration of its real targets — the SSOT the
# `help` recipe echoes and README mirrors. Example: `.PHONY: help test run run-cmd ...`.
_PHONY_LINE = re.compile(r"^\.PHONY:\s*(.+)$", re.MULTILINE)
# A documented dev command in README: `make <target>` (target = lowercase, digits, hyphens),
# e.g. `make test`, `make run-cmd`, `make goldens`. Trailing `ARGS=`/`WHAT=` don't matter —
# the capture is the target name only.
_MAKE_REF = re.compile(r"\bmake ([a-z][a-z0-9-]*)\b")


def _phony_targets() -> set[str]:
    text = MAKEFILE.read_text(encoding="utf-8")
    match = _PHONY_LINE.search(text)
    assert match is not None, "Makefile has no `.PHONY:` line to derive the target set from"
    return set(match.group(1).split())


def _readme_documented_targets() -> set[str]:
    return set(_MAKE_REF.findall(README.read_text(encoding="utf-8")))


def test_every_makefile_target_is_documented_in_readme():
    """(a) Every real `.PHONY` target has a `make <target>` mention in README."""
    targets = _phony_targets()
    documented = _readme_documented_targets()
    undocumented = targets - documented
    assert not undocumented, (
        f"Makefile targets missing a `make <target>` mention in README: "
        f"{sorted(undocumented)}. Document them in README §'For contributors' (or, if a "
        f"target was removed, drop it from the Makefile `.PHONY:` line)."
    )


def test_readme_documents_only_real_makefile_targets():
    """(b) Every `make <target>` README documents is a real `.PHONY` target."""
    targets = _phony_targets()
    documented = _readme_documented_targets()
    phantom = documented - targets
    assert not phantom, (
        f"README documents `make <target>` names the Makefile does not define: "
        f"{sorted(phantom)}. Add them to the Makefile `.PHONY:` line, or fix the README "
        f"reference (the Makefile `.PHONY:` line is the target SSOT)."
    )
