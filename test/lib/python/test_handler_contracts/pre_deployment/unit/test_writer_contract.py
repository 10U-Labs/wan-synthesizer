from __future__ import annotations

from typing import Any

from test_handler_contracts import WriterContract

_CFG: dict[str, Any] = {
    "endpoint": "carriers",
    "param": "carrier",
    "key": "carriers/telia/fiber-segments.json",
    "id": "telia",
    "valid": [{"a_municipality": "Reston", "a_state": "VA", "z_municipality": "Denver",
               "z_state": "CO", "submarine": False}],
}


class TestTheWriteContract(WriterContract):
    CFG = _CFG
