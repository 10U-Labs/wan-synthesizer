from __future__ import annotations

import re

from repo_utils import REPO_ROOT

SPA = REPO_ROOT / "src" / "www" / "spa"
INACTIVITY_LIMIT_MINUTES = 15
_ENDING = "endSession("


def _app_js() -> str:
    return (SPA / "app.js").read_text(encoding="utf-8")


def _index_html() -> str:
    return (SPA / "index.html").read_text(encoding="utf-8")


def _number(name: str) -> int:
    match = re.search(rf"^const {name} = (\d+);$", _app_js(), re.M)
    if match is None:
        raise AssertionError(f"app.js declares no {name}")
    return int(match.group(1))


def _body_of(function: str) -> str:
    match = re.search(rf"^function {function}\([^)]*\) \{{\n(.*?)^\}}$", _app_js(), re.M | re.S)
    if match is None:
        raise AssertionError(f"app.js declares no {function}")
    return match.group(1)


def _listened(target: str) -> list[str]:
    return re.findall(
        rf'getElementById\("{target}"\)\.addEventListener\("click", ([^)]+\))', _app_js())


def test_the_page_carries_a_sign_out_control_inside_the_app() -> None:
    assert re.search(r'<div id="app" hidden>.*<button id="sign-out"', _index_html(), re.S)


def test_the_control_signs_out() -> None:
    assert _listened("sign-out") == ["signOut)"]


def test_signing_out_ends_the_session() -> None:
    assert f"{_ENDING}SIGN_IN_NOTES.out);" in _body_of("signOut")


def test_signing_out_stops_google_choosing_the_account_again() -> None:
    assert "google.accounts.id.disableAutoSelect();" in _body_of("signOut")


def test_the_tokens_expiry_is_read_from_its_payload() -> None:
    assert re.search(r"JSON\.parse\(atob\(.*token\.split\(\"\.\"\)\[1\]", _body_of("tokenExpiry"))


def test_the_session_ends_at_the_tokens_expiry() -> None:
    assert f"setTimeout(() => {_ENDING}SIGN_IN_NOTES.expired), " in _body_of("watchSession")


def test_a_token_without_a_readable_expiry_ends_the_session_at_once() -> None:
    assert f"{_ENDING}SIGN_IN_NOTES[401]);\n    return;" in _body_of("watchSession")


def test_the_inactivity_limit_is_fifteen_minutes() -> None:
    assert _number("INACTIVITY_LIMIT_MINUTES") == INACTIVITY_LIMIT_MINUTES


def test_the_session_ends_after_the_inactivity_limit() -> None:
    assert (f"setTimeout(() => {_ENDING}SIGN_IN_NOTES.idle), "
            "INACTIVITY_LIMIT_MINUTES * 60 * 1000)") in _body_of("touch")


def test_every_interaction_restarts_the_inactivity_timer() -> None:
    assert re.search(
        r'for \(const type of ACTIVITY_EVENTS\) \{\n\s*document\.addEventListener\(type, touch',
        _app_js())


def test_the_interactions_watched_are_pointer_key_and_scroll() -> None:
    match = re.search(r"^const ACTIVITY_EVENTS = \[([^\]]+)\];$", _app_js(), re.M)
    assert sorted(re.findall(r'"(\w+)"', str(match and match.group(1)))) == [
        "keydown", "pointerdown", "pointermove", "wheel"]


def test_being_turned_away_ends_the_session_the_same_way() -> None:
    assert _body_of("turnedAway").strip() == f"{_ENDING}SIGN_IN_NOTES[status]);"


def test_the_token_is_dropped_in_one_place_alone() -> None:
    assert _app_js().count("idToken = null;") == 1


def test_ending_the_session_stops_both_timers() -> None:
    assert "stopWatching();" in _body_of("endSession")


def test_the_idle_note_names_the_limit() -> None:
    assert "${INACTIVITY_LIMIT_MINUTES} minutes" in _app_js()
