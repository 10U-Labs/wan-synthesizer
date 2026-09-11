from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from assert_resource_names_agree import (
    OPENAPI,
    SPA,
    SYNTHESIZER,
    TENANTS,
    disagreements,
    documented_collections,
    documented_inputs,
    fetched_collections,
    main,
    named_strings,
    published_keys,
)

_ROUTE = "/wan-synthesizer/tenants/{tenant}"
_TENANTS_SOURCE = '''_WAN_COLLECTIONS = (
    "sites",
    "wan-pops",
)
_INPUTS = frozenset({
    "locations",
    "forced-circuits",
})
_LIMIT = 5
_SEEN = {}
_SEEN["kind"] = "site"
'''
_SYNTHESIZER_SOURCE = '''CONFIG_RESOURCES = (
    "forced-circuits",
)


def _build_wan(payload, other):
    nothing = {}
    apart = {"count": len(payload)}
    helped = {"rows": rows(payload)}
    deep = {"rows": one.two.three(payload)}
    elsewhere = {"rows": other.sites(payload)}
    numbered = {1: published.sites(payload)}
    return {
        "sites": published.sites(payload),
        "wan-pops": published.wan_pops(payload),
    }, nothing, apart, helped, deep, elsewhere, numbered
'''
_SPA_SOURCE = """
async function render(tenantId) {
  const sites = await getJSON(`${API_BASE}/tenants/${tenantId}/sites`);
  const pops = await getJSON(`${API_BASE}/tenants/${tenantId}/wan-pops`);
}
"""


def _spec() -> dict[str, Any]:
    return {
        "paths": {
            f"{_ROUTE}/sites": {"get": {}},
            f"{_ROUTE}/wan-pops": {"get": {}},
            f"{_ROUTE}/locations": {"get": {}, "put": {}},
            f"{_ROUTE}/forced-circuits": {"get": {}, "put": {}},
            f"{_ROUTE}/wan": {"get": {}, "post": {}},
            f"{_ROUTE}": {"delete": {}},
            "/wan-synthesizer/carriers": {"get": {}},
        }
    }


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _agreeing_repo(root: Path, spec: dict[str, Any] | None = None) -> Path:
    _write(root, OPENAPI, json.dumps(spec if spec is not None else _spec()))
    _write(root, TENANTS, _TENANTS_SOURCE)
    _write(root, SYNTHESIZER, _SYNTHESIZER_SOURCE)
    _write(root, SPA, _SPA_SOURCE)
    return root


def _without(route: str) -> dict[str, Any]:
    spec = _spec()
    del spec["paths"][f"{_ROUTE}/{route}"]
    return spec


def test_documented_collections_are_the_routes_served_but_not_written(tmp_path: Path) -> None:
    assert documented_collections(_agreeing_repo(tmp_path)) == frozenset({"sites", "wan-pops"})


def test_documented_inputs_are_the_routes_a_caller_can_write(tmp_path: Path) -> None:
    assert documented_inputs(_agreeing_repo(tmp_path)) == frozenset(
        {"locations", "forced-circuits"}
    )


def test_named_strings_reads_every_string_of_a_tuple() -> None:
    assert named_strings(_TENANTS_SOURCE, "_WAN_COLLECTIONS") == frozenset({"sites", "wan-pops"})


def test_named_strings_reads_every_string_of_a_frozenset() -> None:
    assert named_strings(_TENANTS_SOURCE, "_INPUTS") == frozenset(
        {"locations", "forced-circuits"}
    )


def test_named_strings_holds_no_constant_that_is_not_a_string() -> None:
    assert named_strings(_TENANTS_SOURCE, "_LIMIT") == frozenset()


def test_named_strings_finds_nothing_under_a_name_nothing_is_assigned_to() -> None:
    assert named_strings(_TENANTS_SOURCE, "_NOWHERE") == frozenset()


def test_published_keys_are_the_keys_of_the_wan_the_synthesizer_writes() -> None:
    assert published_keys(_SYNTHESIZER_SOURCE) == frozenset({"sites", "wan-pops"})


def test_fetched_collections_are_the_ones_the_map_asks_for() -> None:
    assert fetched_collections(_SPA_SOURCE) == frozenset({"sites", "wan-pops"})


def test_lists_that_agree_are_reported_as_nothing(tmp_path: Path) -> None:
    assert disagreements(_agreeing_repo(tmp_path)) == []


def test_a_collection_the_handler_serves_and_nothing_documents_is_reported(
    tmp_path: Path,
) -> None:
    reported = disagreements(_agreeing_repo(tmp_path, _without("wan-pops")))
    assert [line for line in reported if f"::error file={TENANTS}::" in line]


def test_a_collection_documented_and_left_out_of_the_handler_is_reported(
    tmp_path: Path,
) -> None:
    _agreeing_repo(tmp_path)
    _write(tmp_path, TENANTS, _TENANTS_SOURCE.replace('    "wan-pops",\n', ""))
    assert [line for line in disagreements(tmp_path) if f"::error file={OPENAPI}::" in line]


def test_an_input_the_handler_serves_and_nothing_documents_is_reported(tmp_path: Path) -> None:
    root = _agreeing_repo(tmp_path, _without("forced-circuits"))
    assert [line for line in disagreements(root) if "forced-circuits" in line]


def test_a_wan_key_the_synthesizer_writes_that_nothing_serves_is_reported(
    tmp_path: Path,
) -> None:
    _agreeing_repo(tmp_path)
    _write(tmp_path, SYNTHESIZER, _SYNTHESIZER_SOURCE.replace("wan-pops", "provider-pops"))
    assert [line for line in disagreements(tmp_path) if f"::error file={SYNTHESIZER}::" in line]


def test_a_config_resource_the_synthesizer_reads_that_nothing_serves_is_reported(
    tmp_path: Path,
) -> None:
    _agreeing_repo(tmp_path)
    _write(tmp_path, SYNTHESIZER, _SYNTHESIZER_SOURCE.replace("forced-circuits", "forced-paths"))
    assert [line for line in disagreements(tmp_path) if "forced-paths" in line]


def test_a_collection_the_map_fetches_that_nothing_serves_is_reported(tmp_path: Path) -> None:
    _agreeing_repo(tmp_path)
    _write(tmp_path, SPA, _SPA_SOURCE.replace("wan-pops", "backbone-nodes"))
    assert [line for line in disagreements(tmp_path) if f"::error file={SPA}::" in line]


def test_main_answers_zero_when_every_list_agrees(tmp_path: Path) -> None:
    assert main(["--root", str(_agreeing_repo(tmp_path))]) == 0


def test_main_answers_one_when_a_list_is_out_of_step(tmp_path: Path) -> None:
    assert main(["--root", str(_agreeing_repo(tmp_path, _without("sites")))]) == 1


def test_main_prints_an_annotation_naming_the_file_that_disagrees(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--root", str(_agreeing_repo(tmp_path, _without("sites")))])
    assert f"::error file={TENANTS}::" in capsys.readouterr().out
