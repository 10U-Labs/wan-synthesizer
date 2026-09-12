from __future__ import annotations

import csv

from repo_utils import REPO_ROOT

_DATA = REPO_ROOT / "data"
_DCN = _DATA / "pops" / "dcn.csv"
_DCN_SEGMENT_ROWS = _DATA / "fiber_segments" / "terrestrial" / "dcn.csv"


def _pops() -> list[dict[str, str]]:
    with _DCN.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _segment_endpoints() -> set[tuple[str, str]]:
    with _DCN_SEGMENT_ROWS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    near = {(row["A_Municipality"], row["A_State"]) for row in rows}
    return near | {(row["Z_Municipality"], row["Z_State"]) for row in rows}


def test_segment_endpoints_resolve_to_pops() -> None:
    keys = {(pop["Municipality"], pop["State"]) for pop in _pops()}
    assert _segment_endpoints() <= keys
