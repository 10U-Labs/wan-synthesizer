from __future__ import annotations

from repo_utils import REPO_ROOT

APP = REPO_ROOT / "src" / "www" / "spa" / "app.js"
BY_LABEL = "function byLabel(left, right) {\n  return left.label.localeCompare(right.label);\n}\n"
SORTED = "  const entries = syntheses.sort(byLabel).map(({ id, label }) => {\n"


def _source() -> str:
    return APP.read_text(encoding="utf-8")


def test_two_syntheses_are_ordered_by_their_labels() -> None:
    assert BY_LABEL in _source()


def test_the_tenants_are_listed_in_the_order_of_their_labels() -> None:
    assert SORTED in _source()
