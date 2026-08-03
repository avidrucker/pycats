"""
tests/test_1036_hurt_labels.py

#1036 — hurt-box letters round-trip through save->load, mirroring the
`Hitbox.label` contract (#1029/#1030) on the hurt side. Each hurt `Circle`
carries an optional `label`; the serializer stays lenient exactly like
`Hitbox.label`:

  - an UNLABELED circle keeps the old bare-triple `[dx, dy, r]` shape, so
    existing `<char>.json` files don't churn at once (golden-safe);
  - a LABELED circle serializes as a labeled entry `{"circle": [dx, dy, r],
    "label": "A"}` — NOT a parallel `labels` list (which would reintroduce the
    index-coupling #1024 fixed).

The loader accepts BOTH forms (bare triple -> `label=None`; labeled dict ->
`label` adopted), so old and new files both hydrate.

Able-to-fail: without the `Circle.label` field and the serde changes,
`Circle(..., label=...)` raises `TypeError` and the shape assertions fail.
"""

import json

from pycats.combat.data import (
    Circle,
    Hurtbox,
    _hurtbox_from_json,
    _hurtbox_to_json,
)


def _through_json(doc: dict) -> dict:
    return json.loads(json.dumps(doc))


def test_circle_carries_optional_label_defaulting_none():
    assert Circle(1, 2, 3).label is None
    assert Circle(1, 2, 3, label="A").label == "A"


def test_labeled_hurt_circle_roundtrips_through_json():
    # A gap (A, then C) proves the loader adopts the stored letter verbatim
    # rather than re-ranking by position.
    hb = Hurtbox(circles=(Circle(10, 20, 8, label="A"), Circle(12, 22, 9, label="C")))
    assert _hurtbox_from_json(_through_json(_hurtbox_to_json(hb))) == hb


def test_labeled_circle_serializes_as_labeled_entry():
    hb = Hurtbox(circles=(Circle(10, 20, 8, label="A"),))
    assert _hurtbox_to_json(hb) == {"circles": [{"circle": [10, 20, 8], "label": "A"}]}


def test_unlabeled_circle_keeps_bare_triple_shape():
    # Golden-safe: label absent -> old shape, so existing files stay byte-equal.
    hb = Hurtbox(circles=(Circle(10, 20, 8),))
    assert _hurtbox_to_json(hb) == {"circles": [[10, 20, 8]]}


def test_loader_accepts_old_bare_triples_label_none():
    hb = _hurtbox_from_json({"circles": [[10, 20, 8]]})
    assert hb == Hurtbox(circles=(Circle(10, 20, 8),))
    assert hb.circles[0].label is None


def test_mixed_labeled_and_bare_roundtrips():
    hb = Hurtbox(circles=(Circle(10, 20, 8, label="A"), Circle(1, 2, 3)))
    assert _hurtbox_from_json(_through_json(_hurtbox_to_json(hb))) == hb
