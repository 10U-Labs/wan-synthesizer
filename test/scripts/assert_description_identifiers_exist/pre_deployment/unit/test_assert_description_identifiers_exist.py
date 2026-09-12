from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from assert_description_identifiers_exist import (
    OPENAPI,
    descriptions,
    identifiers,
    main,
    named_in_the_trees,
    unnamed_identifiers,
)

_SOURCE = Path("src", "api", "endpoints", "tenants", "lambdas", "handler.py")
_VENDOR = Path("src", "www", "spa", "vendor", "leaflet.js")
_HANDLER = '''_HEADERS = {"Content-Type": "application/json"}


def _delivered(backbone_lower_bound_miles: float) -> float:
    return backbone_lower_bound_miles
'''
_VENDOR_SOURCE = "var leaflet_layer_control = 1;\n"


def _spec(description: str) -> dict[str, Any]:
    return {
        "info": {"description": "Graphs as REST resources."},
        "paths": {
            "/wan-synthesizer/tenants/{tenant}/wan": {
                "get": {
                    "responses": {
                        "200": {"description": description},
                        "409": {"description": "No valid WAN is possible."},
                    }
                }
            }
        },
        "tags": ["untouched"],
    }


def _repo(root: Path, description: str) -> Path:
    written = {
        OPENAPI: json.dumps(_spec(description)),
        _SOURCE: _HANDLER,
        _VENDOR: _VENDOR_SOURCE,
        Path("etc", "two_pop.yml"): "backbone:\n  coverage_target_miles: 1090\n",
        Path("src", "api", "common", "storage", "main.tf"): 'bucket = "store"\n',
        Path("src", "www", "spa", "style.css"): "body { margin: 0 }\n",
    }
    for relative, text in written.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text, encoding="utf-8")
    return root


def test_descriptions_reads_one_nested_in_a_mapping() -> None:
    assert "Graphs as REST resources." in descriptions(_spec("anything"))


def test_descriptions_reads_one_nested_in_a_list() -> None:
    assert descriptions({"any": [{"description": "held in a list"}]}) == ["held in a list"]


def test_descriptions_reads_nothing_out_of_a_bare_value() -> None:
    assert descriptions("a string is not a description") == []


def test_descriptions_reads_nothing_out_of_a_description_that_is_not_a_string() -> None:
    assert descriptions({"description": {"nested": "mapping"}}) == []


def test_identifiers_finds_a_snake_case_name() -> None:
    assert identifiers("the backbone_lower_bound_miles it was built under") == frozenset(
        {"backbone_lower_bound_miles"}
    )


def test_identifiers_finds_no_ordinary_english_word() -> None:
    assert identifiers("the backup path multiple it was built under") == frozenset()


def test_identifiers_passes_over_a_name_shorter_than_four_characters() -> None:
    assert identifiers("a_b is too short to be worth reading") == frozenset()


def test_named_in_the_trees_holds_a_name_the_source_declares(tmp_path: Path) -> None:
    assert "backbone_lower_bound_miles" in named_in_the_trees(_repo(tmp_path, "any"))


def test_named_in_the_trees_holds_a_name_a_tenant_config_declares(tmp_path: Path) -> None:
    assert "coverage_target_miles" in named_in_the_trees(_repo(tmp_path, "any"))


def test_named_in_the_trees_holds_no_name_only_the_served_spec_carries(tmp_path: Path) -> None:
    assert "max_backup_path_multiple" not in named_in_the_trees(
        _repo(tmp_path, "the max_backup_path_multiple it was built under")
    )


def test_named_in_the_trees_holds_no_name_only_vendored_code_carries(tmp_path: Path) -> None:
    assert "leaflet_layer_control" not in named_in_the_trees(_repo(tmp_path, "any"))


def test_a_description_naming_something_that_exists_is_reported_as_nothing(
    tmp_path: Path,
) -> None:
    assert unnamed_identifiers(
        _repo(tmp_path, "the backbone_lower_bound_miles beside it")
    ) == []


def test_a_description_naming_something_gone_is_reported(tmp_path: Path) -> None:
    assert unnamed_identifiers(
        _repo(tmp_path, "the max_backup_path_multiple it was built under")
    ) == [("max_backup_path_multiple", "the max_backup_path_multiple it was built under")]


def test_main_answers_zero_when_every_spelled_identifier_exists(tmp_path: Path) -> None:
    assert main(["--root", str(_repo(tmp_path, "the backbone_lower_bound_miles beside it"))]) == 0


def test_main_answers_one_when_a_spelled_identifier_is_gone(tmp_path: Path) -> None:
    assert main(["--root", str(_repo(tmp_path, "the max_backup_path_multiple it held"))]) == 1


def test_main_prints_an_annotation_naming_the_identifier_nothing_declares(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--root", str(_repo(tmp_path, "the max_backup_path_multiple it held"))])
    assert "max_backup_path_multiple" in capsys.readouterr().out
