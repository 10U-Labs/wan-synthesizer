from __future__ import annotations

from typing import NamedTuple

import pytest
from playwright.sync_api import (
    Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright,
)

SPA = "https://www.10ulabs.com/wan-synthesizer/"
ENGINES = ["chromium", "webkit"]
GOOGLE_BUTTON = "#google-button iframe"
GOOGLE_BUTTON_STYLES = "googleidentityservice_button_styles"
REFUSED_STYLE_ELEMENT = "style-src-elem"
WAIT_MILLISECONDS = 30000
RECORD_VIOLATIONS = (
    "window.violations = [];"
    " document.addEventListener('securitypolicyviolation',"
    " (event) => window.violations.push(event.effectiveDirective));"
)


class Card(NamedTuple):
    button_shown: bool
    styled: bool
    refused: list[str]


def _shown(button: Locator) -> bool:
    try:
        button.wait_for(state="visible", timeout=WAIT_MILLISECONDS)
    except PlaywrightTimeoutError:
        return False
    return True


def _card(page: Page) -> Card:
    page.add_init_script(RECORD_VIOLATIONS)
    page.goto(SPA, wait_until="load")
    shown = _shown(page.locator(GOOGLE_BUTTON))
    styled = bool(page.evaluate(f"!!document.getElementById('{GOOGLE_BUTTON_STYLES}')?.sheet"))
    return Card(shown, styled, list(page.evaluate("window.violations")))


@pytest.fixture(name="card", scope="module", params=ENGINES)
def card_fixture(request: pytest.FixtureRequest) -> Card:
    with sync_playwright() as playwright:
        browser = getattr(playwright, request.param).launch()
        try:
            return _card(browser.new_page())
        finally:
            browser.close()


def test_the_signed_out_card_shows_googles_sign_in_button(card: Card) -> None:
    assert card.button_shown is True


def test_googles_button_styles_apply_to_the_card(card: Card) -> None:
    assert card.styled is True


def test_the_page_refuses_no_style_element_it_loads(card: Card) -> None:
    assert REFUSED_STYLE_ELEMENT not in card.refused
