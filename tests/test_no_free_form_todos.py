"""Guard test for #50 — drive free-form ``#### TODO:`` source comments to zero.

This is the BDD "failing test" #50 lacked. Its definition of done — the count of
free-form TODO comments in ``pycats/`` reaching 0 — was checked by a human
re-running ``grep -rnE "#+ *TODO" pycats/``; nothing failed while the count was
> 0 and nothing caught a *new* free-form TODO sneaking in. This test encodes that
DoD as an assertion, mirroring #50's canonical grep.

INTENTIONALLY ``xfail(strict=True)``: while #50 is in progress the count is > 0,
so the assertion fails — ``xfail`` keeps the suite green while making the target
visible and enforced. It is **self-completing**: when #50 drives the count to 0
the assertion passes, ``strict=True`` turns that *unexpected pass* into a suite
FAILURE, and the agent landing the final #50 batch must **remove the xfail marker**
— leaving a permanent guard that fails CI on any future free-form TODO.

WHAT TO DO:
- **Do NOT delete this test.** It is the enforcing guard once #50 lands.
- **Do NOT add new ``#### TODO:`` comments to ``pycats/``.** A genuine deferred
  sub-problem goes in canonical ``@todo #N`` PDD form (issue-linked, lowercase) —
  those are *not* matched here and are allowed.
- When the count hits 0, delete only the ``@pytest.mark.xfail(...)`` line above
  the test (and update this note). See RULES.md → "The test must be able to fail".
"""
import pathlib
import re

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PYCATS = _REPO_ROOT / "pycats"

# #50's canonical DoD grep: ``grep -rnE "#+ *TODO" pycats/``. Matches free-form
# ``# TODO`` / ``## TODO`` / ``#### TODO:`` comments. Canonical PDD markers are
# lowercase ``@todo #N`` and are deliberately NOT matched.
_FREE_FORM_TODO = re.compile(r"#+ *TODO")


def _free_form_todos():
    """Every free-form TODO under pycats/ as ``relpath:lineno: text`` strings.

    Scans all files (not just ``*.py``) to mirror ``grep -r``; skips the
    ``__pycache__`` bytecode dir and any file that isn't UTF-8 text."""
    hits = []
    for path in sorted(_PYCATS.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _FREE_FORM_TODO.search(line):
                hits.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}: {line.strip()}")
    return hits


@pytest.mark.xfail(
    strict=True,
    reason="#50: 50 free-form TODOs remain — delete/convert per #50, then remove this marker",
)
def test_no_free_form_todos_in_pycats():
    hits = _free_form_todos()
    assert hits == [], (
        f"{len(hits)} free-form `#### TODO:` comment(s) in pycats/ (#50 wants 0):\n"
        + "\n".join(hits)
    )
