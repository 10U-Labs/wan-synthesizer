from __future__ import annotations

import re

from repo_utils import REPO_ROOT

APP = REPO_ROOT / "src" / "www" / "spa" / "app.js"
_SITE_WORDS = {"site", "sites"}


def _function_names() -> list[str]:
    return re.findall(r"\bfunction\s+(\w+)", APP.read_text(encoding="utf-8"))


def _bindings() -> list[str]:
    text = APP.read_text(encoding="utf-8")
    parameters = [
        name.strip()
        for listed in re.findall(r"\bfunction\s+\w+\(([^)]*)\)", text)
        for name in listed.split(",")
    ]
    walked = re.findall(r"\bfor\s*\(\s*const\s+(\w+)\s+of\b", text)
    return parameters + walked


def test_no_function_in_the_map_is_named_for_a_site() -> None:
    assert [name for name in _function_names() if "site" in name.lower()] == []


def test_no_parameter_or_loop_variable_in_the_map_is_a_site() -> None:
    assert [name for name in _bindings() if name in _SITE_WORDS] == []
