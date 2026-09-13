from __future__ import annotations

import re

from repo_utils import REPO_ROOT

INDEX = REPO_ROOT / "src" / "www" / "spa" / "index.html"
PROGRAM = "WAN Synthesizer"
_NAMED_IN = ("title", "h1", "strong")


def _text_of(tag: str) -> list[str]:
    return re.findall(rf"<{tag}[^>]*>([^<]*)</{tag}>", INDEX.read_text(encoding="utf-8"))


def test_the_tab_the_sign_in_card_and_the_bar_name_the_program() -> None:
    assert [_text_of(tag) for tag in _NAMED_IN] == [[PROGRAM]] * len(_NAMED_IN)


def test_nothing_on_the_page_says_graph() -> None:
    assert "graph" not in INDEX.read_text(encoding="utf-8").lower()
