from __future__ import annotations

import re

from repo_utils import REPO_ROOT

APP = REPO_ROOT / "src" / "www" / "spa" / "app.js"
GIVES_UP = "  } catch {\n    showNote(UNREADABLE_NOTE);\n    return;\n  }\n"


def _source() -> str:
    return APP.read_text(encoding="utf-8")


def _declared(function: str) -> str:
    found = re.search(
        rf"^(?:async )?function {function}\(\w*\) \{{\n(.*?)^\}}$", _source(), re.M | re.S)
    if found is None:
        raise AssertionError(f"app.js has no function {function}")
    return found.group(1)


def _note(name: str) -> str:
    found = re.search(rf'^const {name} = "([^"]*)";$', _source(), re.M)
    if found is None:
        raise AssertionError(f"app.js has no note {name}")
    return found.group(1)


def test_a_note_is_written_into_the_bars_counts() -> None:
    assert _declared("showNote") == '  document.getElementById("counts").textContent = note;\n'


def test_a_listing_that_cannot_be_read_says_the_wan_could_not_be_read() -> None:
    assert GIVES_UP in _declared("start")


def test_a_synthesis_that_cannot_be_read_says_the_wan_could_not_be_read() -> None:
    assert GIVES_UP in _declared("render")


def test_an_empty_listing_says_no_wan_is_synthesized() -> None:
    assert "  } else {\n    showNote(NOT_SYNTHESIZED_NOTE);\n  }\n" in _declared("start")


def test_the_unreadable_note_says_the_wan_could_not_be_read() -> None:
    assert _note("UNREADABLE_NOTE") == "The WAN could not be read"


def test_the_unsynthesized_note_says_no_wan_is_synthesized() -> None:
    assert _note("NOT_SYNTHESIZED_NOTE") == "No WAN synthesized yet"
