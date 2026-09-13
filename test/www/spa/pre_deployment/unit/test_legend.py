from __future__ import annotations

from repo_utils import REPO_ROOT

APP = REPO_ROOT / "src" / "www" / "spa" / "app.js"


def _app() -> str:
    return APP.read_text(encoding="utf-8")


def test_the_legend_calls_the_tenants_dot_a_site() -> None:
    assert 'label: "Site", tenant: true' in _app()


def test_the_legend_names_a_chosen_tenants_sites_after_it() -> None:
    assert "textContent = `${label} Site`;" in _app()


def test_the_count_line_counts_sites() -> None:
    assert "` SITES ${tally.tenant}`" in _app()


def test_nothing_on_the_map_says_location() -> None:
    assert "location" not in _app().lower()
