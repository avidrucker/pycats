"""Guard: no banned word appears in the swept prose corpus (#1245).

The banned-word list is **not hardcoded here** — it is parsed from the table in
``docs/banned_words.md`` (the single source of truth). #1238's additions to that table
flow through automatically; this file names no banned word of its own, so it never has to
be exempted from its own scan.

Scope (#1245 slice — "guard + one slice, split the rest"): the swept set is the top-level
governance docs the fleet reads constantly. The wider living-docs corpus (docs/adr,
docs/pm-reference, docs/superpowers, code comments/docstrings) is cleaned by per-category
follow-up tickets, each of which appends its category to ``SWEPT`` here. The dated archive
(``docs/learnings/**`` TILs and dated ``docs/research/**`` findings) is exempt as a
point-in-time record, the same reason ``docs/research/test-suite-audit-findings.md`` is
preserved verbatim.

Exemptions for a line that must name a banned word (e.g. a rule that defines the ban):
  - single line — put the marker ``banned-words-ok`` anywhere on the line;
  - a block — bracket it with ``banned-words-ok:start`` / ``banned-words-ok:end`` marker
    lines (an HTML comment in markdown), and every line between is skipped.

Able-to-fail: ``test_detector_flags_a_parsed_term`` builds a sample line from a parsed term
and asserts the pattern matches, so a parser that returned nothing (which would make the
main assertion vacuously pass) is caught. Reintroduce a banned word into any swept file and
``test_no_banned_words_in_swept_corpus`` reds, naming the file + line.
"""

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_WORDLIST = _ROOT / "docs" / "banned_words.md"

# The swept corpus (paths relative to repo root). #1245 ships the governance-doc slice;
# a follow-up ticket appends its category here as it cleans it.
SWEPT = [
    "RULES.md",
    "README.md",
    "CLAUDE.md",
    "JUDGEMENT_CALLS.md",
]

_BLOCK_START = "banned-words-ok:start"
_BLOCK_END = "banned-words-ok:end"
_LINE_MARK = "banned-words-ok"


def _banned_terms():
    """Every banned term parsed from the first column of the ``docs/banned_words.md`` table.

    A cell like ``honest / honesty / honestly`` yields three terms; ``PR / pull request``
    yields ``PR`` and ``pull request``. Header (``Word``) and separator (``---``) rows are
    skipped."""
    terms = []
    for line in _WORDLIST.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        first = cells[0]
        if first.lower() == "word" or set(first) <= set("-: "):
            continue
        for variant in first.split("/"):
            v = variant.strip()
            if v:
                terms.append(v)
    return terms


def _pattern():
    """A case-insensitive matcher for any parsed term, bounded by non-word edges.

    Longer alternatives are tried first so ``pull request`` wins over a bare token, and the
    ``(?<!\\w)…(?!\\w)`` edges keep ``real`` from matching inside ``realise`` while still
    catching hyphenated forms like ``load-bearing`` and multi-word forms."""
    alts = sorted({re.escape(t) for t in _banned_terms()}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


def _hits(path):
    """Banned-word occurrences in one file as ``name:lineno: text`` strings, honoring the
    line and block exemption markers."""
    pat = _pattern()
    hits = []
    in_exempt_block = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _BLOCK_START in line:
            in_exempt_block = True
            continue
        if _BLOCK_END in line:
            in_exempt_block = False
            continue
        if in_exempt_block or _LINE_MARK in line:
            continue
        if pat.search(line):
            hits.append(f"{path.name}:{lineno}: {line.strip()}")
    return hits


def test_wordlist_parses_enough_terms():
    """A broken parser that returns few/no terms would make the main scan vacuously green."""
    assert len(_banned_terms()) >= 10, "banned-words table parse returned too few terms"


def test_detector_flags_a_parsed_term():
    """Able-to-fail proof: the detector matches a term drawn from the parsed list (the term
    is built at runtime, so this source file still names no banned word)."""
    term = _banned_terms()[0]
    assert _pattern().search(f"prefix {term} suffix"), f"detector failed to flag {term!r}"


@pytest.mark.parametrize("rel", SWEPT)
def test_no_banned_words_in_swept_corpus(rel):
    path = _ROOT / rel
    assert path.exists(), f"swept file missing: {rel}"
    hits = _hits(path)
    assert hits == [], (
        f"{len(hits)} banned-word occurrence(s) in {rel} (see docs/banned_words.md; mark a "
        "line that must name the word with `banned-words-ok`):\n" + "\n".join(hits)
    )
