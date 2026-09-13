from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from repo_utils import REPO_ROOT

SPA = REPO_ROOT / "src" / "www" / "spa"
POLICY = {
    "default-src": {"'none'"},
    "script-src": {"'self'", "https://accounts.google.com"},
    "connect-src": {"'self'", "https://api.10ulabs.com", "https://accounts.google.com"},
    "frame-src": {"https://accounts.google.com"},
    "style-src": {"'self'", "https://fonts.googleapis.com", "https://accounts.google.com"},
    "font-src": {"https://fonts.gstatic.com"},
    "img-src": {"'self'", "data:"},
    "base-uri": {"'none'"},
    "form-action": {"'none'"},
}
_API_BASE = re.compile(r'^const API_BASE = "([^"]+)";$', re.MULTILINE)


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.policies: list[str] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        named = {key: value or "" for key, value in attrs}
        if tag == "meta" and named.get("http-equiv", "").lower() == "content-security-policy":
            self.policies.append(named.get("content", ""))
        if tag == "script" and "src" in named:
            self.scripts.append(named["src"])
        if tag == "link" and named.get("rel") == "stylesheet":
            self.stylesheets.append(named["href"])


def _page() -> _Page:
    page = _Page()
    page.feed((SPA / "index.html").read_text(encoding="utf-8"))
    return page


def _directives(policy: str) -> dict[str, set[str]]:
    return {
        words[0]: set(words[1:])
        for directive in policy.split(";")
        if (words := directive.split())
    }


def _source_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme else "'self'"


def test_the_page_declares_one_content_security_policy() -> None:
    assert len(_page().policies) == 1


def test_every_directive_names_exactly_its_sources() -> None:
    assert _directives(_page().policies[0]) == POLICY


def test_every_script_the_page_loads_is_one_the_policy_admits() -> None:
    assert {_source_of(src) for src in _page().scripts} <= POLICY["script-src"]


def test_every_stylesheet_the_page_loads_is_one_the_policy_admits() -> None:
    assert {_source_of(href) for href in _page().stylesheets} <= POLICY["style-src"]


def test_the_api_the_page_fetches_is_one_the_policy_admits() -> None:
    api_base = _API_BASE.search((SPA / "app.js").read_text(encoding="utf-8"))
    assert api_base is not None and _source_of(api_base.group(1)) in POLICY["connect-src"]
